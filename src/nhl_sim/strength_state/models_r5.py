"""SS-R5 (INV-29) penalty-type arms T1-T3 with team terms (docs/models/strength_state/experiments.md SS-R5).

T1  multinomial logit on season + strength state + score bucket + period (identical design to models.t1_design)
T2  T1 + own taken-rating + opponent taken-rating (the hazard's as-of ratings, ratings_grid_v2, w=1.0, b=1800)
T3  T2 + as-of team offsetting-share rating (shrunk log-odds of the team's coincidental share vs the league,
    beta-binomial prior strength k penalties) for the penalty-taking team and for the opponent

Every rating is relative to its own snapshot's league mean. As-of = games on earlier calendar dates only (same
convention as tables.asof_ratings: all games of a day see the snapshot taken before that day).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.strength_state import models as M
from nhl_sim.strength_state.models_r2 import wkey

SS = M.SS
TYPE_VERSION = "v2"
W, B = 1.0, 1800
RATING_FEATURES = {"T1": [], "T2": ["taken_own", "taken_opp"],
                   "T3": ["taken_own", "taken_opp", "off_own", "off_opp"]}


def logit(p):
    return np.log(p / (1 - p))


def offset_rating(k: float, version: str = TYPE_VERSION) -> pd.DataFrame:
    """As-of offsetting-share rating per (game_id, team_id), cumulative over all earlier game dates in the data
    (no season reset; interpretation choice, labelled). C = coincidental penalty events charged to the team,
    N = all penalty events charged to the team (type_rows rows). League share p_L = (sum C + 1) / (sum N + 4).
    rating = logit((C + k p_L)/(N + k)) - logit(p_L), then minus the mean over teams in the snapshot."""
    t = pd.read_parquet(SS / f"type_rows_{version}.parquet", columns=["game_id", "team", "cls"])
    tg = pd.read_parquet(SS / f"team_game_{version}.parquet", columns=["game_id", "team_id", "is_home", "date"])
    t = t.merge(tg.assign(team=1 - tg.is_home)[["game_id", "team", "team_id"]], on=["game_id", "team"], how="left")
    if t.team_id.isna().any():
        raise ValueError("type rows without a team-game")
    t["co"] = (t.cls == "coincidental").astype(int)
    ev = t.groupby(["game_id", "team_id"]).agg(C=("co", "sum"), N=("co", "size")).reset_index()
    d = tg.merge(ev, on=["game_id", "team_id"], how="left").fillna({"C": 0, "N": 0})
    d["date"] = pd.to_datetime(d.date)
    teams = np.sort(d.team_id.unique())
    tix = {x: i for i, x in enumerate(teams)}
    C, N = np.zeros(len(teams)), np.zeros(len(teams))
    out = []
    for day, g in d.sort_values(["date", "game_id"]).groupby("date", sort=True):
        pL = (C.sum() + 1.0) / (N.sum() + 4.0)
        r = logit((C + k * pL) / (N + k)) - logit(pL)
        r = r - r.mean()
        ti = g.team_id.map(tix).to_numpy()
        out.append(pd.DataFrame({"game_id": g.game_id.to_numpy(), "team_id": g.team_id.to_numpy(), "off": r[ti]}))
        np.add.at(C, ti, g.C.to_numpy())
        np.add.at(N, ti, g.N.to_numpy())
    return pd.concat(out, ignore_index=True)


def team_ratings(k: float) -> pd.DataFrame:
    """(game_id, team_id) -> taken (hazard rating), off (offsetting-share rating at prior strength k)."""
    key = wkey(W, B)
    rt = pd.read_parquet(SS / f"ratings_grid_{TYPE_VERSION}.parquet", columns=["game_id", "team_id", f"taken_{key}"])
    rt.columns = ["game_id", "team_id", "taken"]
    return rt.merge(offset_rating(k), on=["game_id", "team_id"], how="left", validate="one_to_one")


def type_frame(seasons, last_train_season: int, k: float) -> pd.DataFrame:
    """Type rows (one per penalty-taking event) with team-view state and as-of ratings of the taking team and its
    opponent. Event team = `team` (0 home, 1 away)."""
    t = M.type_frame(seasons, last_train_season, version=TYPE_VERSION)
    tg = pd.read_parquet(SS / f"team_game_{TYPE_VERSION}.parquet", columns=["game_id", "team_id", "opp_id", "is_home"])
    t = t.merge(tg.assign(team=1 - tg.is_home)[["game_id", "team", "team_id", "opp_id"]], on=["game_id", "team"],
                how="left")
    rt = team_ratings(k)
    t = t.merge(rt.rename(columns={"taken": "taken_own", "off": "off_own"}), on=["game_id", "team_id"], how="left")
    t = t.merge(rt.rename(columns={"team_id": "opp_id", "taken": "taken_opp", "off": "off_opp"}),
                on=["game_id", "opp_id"], how="left")
    for c in ("taken_own", "taken_opp", "off_own", "off_opp"):
        if t[c].isna().any():
            raise ValueError(f"missing {c} on {int(t[c].isna().sum())} type rows")
    return t


def design(t, arm: str, seasons_ref) -> np.ndarray:
    X = M.t1_design(t, seasons_ref)
    cols = [t[c].to_numpy(float)[:, None] for c in RATING_FEATURES[arm]]
    return np.hstack([X] + cols) if cols else X


def fit(t: pd.DataFrame, arm: str) -> dict:
    from sklearn.linear_model import LogisticRegression
    seasons_ref = sorted(int(s) for s in t.season_f.unique())
    m = LogisticRegression(penalty=None, max_iter=5000)
    m.fit(design(t, arm, seasons_ref), t.k.to_numpy())
    if list(m.classes_) != list(range(len(M.TYPE_CLASSES))):
        raise ValueError("a type class is absent from training")
    return dict(arm=arm, seasons_ref=seasons_ref, coef=m.coef_.tolist(), intercept=m.intercept_.tolist())


def predict(m: dict, t: pd.DataFrame) -> np.ndarray:
    z = design(t, m["arm"], m["seasons_ref"]) @ np.asarray(m["coef"]).T + np.asarray(m["intercept"])
    z -= z.max(1, keepdims=True)
    p = np.exp(z)
    return p / p.sum(1, keepdims=True)


def team_type_table(m: dict, team_rows: pd.DataFrame, k: float, last_train_season: int) -> np.ndarray:
    """Engine lookup: float64 (G, 2, 6, 5, 4, 4) = p[game, team, st, sc, period, class], games sorted. team_rows has
    one row per (game, team) with game_id, team (0 home, 1 away). Ratings are the as-of ratings of that game."""
    games = np.sort(team_rows.game_id.unique())
    tgm = pd.read_parquet(SS / f"team_game_{TYPE_VERSION}.parquet", columns=["game_id", "team_id", "opp_id", "is_home"])
    tgm = tgm[tgm.game_id.isin(games)].assign(team=lambda d: 1 - d.is_home)
    rt = team_ratings(k)
    a = tgm.merge(rt.rename(columns={"taken": "taken_own", "off": "off_own"}), on=["game_id", "team_id"])
    a = a.merge(rt.rename(columns={"team_id": "opp_id", "taken": "taken_opp", "off": "off_opp"}),
                on=["game_id", "opp_id"]).sort_values(["game_id", "team"]).reset_index(drop=True)
    if len(a) != 2 * len(games):
        raise ValueError("need one row per (game, team)")
    st, sc, per = np.meshgrid(np.arange(6), np.arange(5), np.arange(1, 5), indexing="ij")
    base = pd.DataFrame({"st": st.ravel(), "sc": sc.ravel(), "period": per.ravel(), "season_f": last_train_season})
    S = len(base)
    out = np.zeros((len(a), S, len(M.TYPE_CLASSES)))
    for i in range(0, len(a), 256):
        part = a.iloc[i:i + 256]
        big = base.loc[np.tile(np.arange(S), len(part))].reset_index(drop=True)
        for c in ("taken_own", "taken_opp", "off_own", "off_opp"):
            big[c] = np.repeat(part[c].to_numpy(), S)
        out[i:i + len(part)] = predict(m, big).reshape(len(part), S, -1)
    return out.reshape(len(games), 2, 6, 5, 4, len(M.TYPE_CLASSES))
