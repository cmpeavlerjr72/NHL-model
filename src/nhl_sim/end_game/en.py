"""EG-R1 part A (INV-66, Lane H8a): empty-net scoring inputs and the engine's tables["pull"] builder.

Inventory of the served tables at the EN team-view states (5 EN-for = own goalie pulled, 6 EN-against = shooting at
the empty net):
  stage 3 A3g-c      NO EN states (G, 2, M, 5, 7)  -> STAND-IN: as-of M1 K500 attempt level per EN state (this module)
  stage 4 L0s / L1x  L0s state_pdf rows 5 / 6 (the baseline, L33); L1x-as serves EN rows as the L0s baseline x the
                     ES-group M1 K500 level (SL-R7 offline does the same)
  block B0           ES group (B0 fit pools 5v5 + 4v4 + 3v3 + EN in the ES group)  -> index 0 of the (G, 5, 2) table
  miss S0t           ES group (rating group 0)
  goal C1s           EN-for = sg 5 EAF (5v5 level group), defending starter; EN-against: none (no goalie)
                     -> STAND-IN: as-of M1 K500 level of goal per SOG on st-6 SOG (this module; 1.0 in the data)
M1 K500 = (n + K s_prev) / (d + K) per game date from the season's earlier dates (K = 500 attempts for the attempt
rate, with d in attempt units d = exposure x s_prev; K = 500 SOG for the goal share), s_prev = the previous season's
final value; 2021-22 prior = its own final value (burn-in, never judged). created_at < puck_drop asserted.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED
from nhl_sim.end_game import pull as PL
from nhl_sim.strength_state.tables import assert_pregame

K = 500.0
SEASONS = [20212022, 20222023, 20232024, 20242025]
SA = PROCESSED / "shot_attempt"
SATTR = PROCESSED / "shot_attribute"
MOD = PROCESSED / "end_game" / "models_v1"
EN_ATT_LABEL = ("STAND-IN (EG-R1 part A): EN attempt rates = as-of M1 K500 league level per EN state (EN-for / "
                "EN-against attempts per team-hour, stage-3 attempt rows st 5 / 6); flat, no team terms")
EN_GOAL_LABEL = ("STAND-IN (EG-R1 part A): goal per SOG into an empty net = as-of M1 K500 league level on st-6 SOG")
PULL_LABEL = "goalie pull: P1 hazard (EG-R1 part A, selected on fold 2 after D45)"


def _games(seasons):
    g = pd.read_parquet(PROCESSED / "block" / "games_v1.parquet")
    g = g[g.season.isin(seasons)]
    return g.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)


def _asof(games, num, den, kind):
    """M1 K500 per game. num / den: per-game counts (attempts, exposure s) or (goals, SOG). -> (value, meta)."""
    seasons = sorted(games.season.unique())
    final = {s: num[(games.season == s).to_numpy()].sum() / den[(games.season == s).to_numpy()].sum() for s in seasons}
    v = np.zeros(len(games))
    created = np.full(len(games), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    last_drop = None
    for i, s in enumerate(seasons):
        prev = final[seasons[i - 1]] if i > 0 else final[s]
        ix_s = np.flatnonzero((games.season == s).to_numpy())
        dates = games.date.to_numpy()[ix_s]
        n = d = 0.0
        for dt in np.unique(dates):
            ix = ix_s[dates == dt]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            if kind == "rate":                       # K attempts at the prior rate: (n + K) / (d + K / prev)
                v[ix] = (n + K) / (d + K / prev)
            else:                                    # share: (n + K prev) / (d + K)
                v[ix] = (n + K * prev) / (d + K)
            n += num[ix].sum(); d += den[ix].sum()
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": games.season.to_numpy(),
                         "created_at": pd.to_datetime(created).tz_localize("UTC"), "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    m2 = meta[meta.created_at.notna()]
    assert_pregame(m2.rename(columns={}))
    return v, final, meta


def en_levels(seasons=SEASONS) -> tuple[pd.DataFrame, dict]:
    """-> (per game: lam_ef, lam_ea attempts per team-HOUR, p_en_goal; plus counts), info with finals."""
    games = _games(seasons)
    idx = pd.Index(games.game_id)
    out = pd.DataFrame({"game_id": games.game_id, "season": games.season})
    info = {}
    for st, nm in ((5, "ef"), (6, "ea")):
        x, e = np.zeros(len(games)), np.zeros(len(games))
        for s in seasons:
            r = pd.read_parquet(SA / f"attempt_rows_v1_{s}.parquet", columns=["game_id", "st", "exposure_s", "y"])
            r = r[r.st == st].groupby("game_id")[["y", "exposure_s"]].sum()
            p = idx.get_indexer(r.index)
            ok = p >= 0
            x[p[ok]] += r.y.to_numpy()[ok]; e[p[ok]] += r.exposure_s.to_numpy()[ok]
        v, fin, meta = _asof(games, x, e, "rate")
        out[f"lam_{nm}"] = v * 3600.0
        out[f"att_{nm}"], out[f"exp_{nm}_s"] = x, e
        info[nm] = {str(k): float(f * 3600) for k, f in fin.items()}
    g, n = np.zeros(len(games)), np.zeros(len(games))
    for s in seasons:
        a = pd.read_parquet(SATTR / f"attempt_attr_v1_{s}.parquet", columns=["game_id", "st", "event", "is_goal"])
        a = a[(a.st == 6) & a.event.isin(["SHOT", "GOAL"])].groupby("game_id").is_goal.agg(["sum", "size"])
        p = idx.get_indexer(a.index); ok = p >= 0
        g[p[ok]] += a["sum"].to_numpy()[ok]; n[p[ok]] += a["size"].to_numpy()[ok]
    v, fin, meta = _asof(games, g, n, "share")
    out["p_en_goal"], out["en_goals"], out["en_sog"] = v, g, n
    info["en_goal"] = {str(k): float(f) for k, f in fin.items()}
    out = out.merge(meta[["game_id", "created_at", "puck_drop"]], on="game_id")
    return out, info


def parity(L: pd.DataFrame) -> pd.DataFrame:
    """Per-season predicted / actual: attempts (level x exposure) and EN-against goals per SOG."""
    rows = []
    for s, x in L.groupby("season"):
        r = dict(season=int(s))
        for nm in ("ef", "ea"):
            r[f"{nm}_pred_over_actual"] = float((x[f"lam_{nm}"] / 3600 * x[f"exp_{nm}_s"]).sum() / x[f"att_{nm}"].sum())
            r[f"{nm}_n_attempts"] = int(x[f"att_{nm}"].sum())
        r["en_goal_pred_over_actual"] = float((x.p_en_goal * x.en_sog).sum() / x.en_goals.sum())
        r["en_sog"] = int(x.en_sog.sum())
        r["judged"] = s != 20212022
        rows.append(r)
    return pd.DataFrame(rows)


# ===================================================================================== engine tables["pull"]
def goal_eaf(games, goal_info=None):
    """C1s EAF (sg 5) columns in the C1s engine form: cls (78,), game (G, 2); goalie = the defending starter."""
    from nhl_sim.engine import c1s_tables as CT
    from nhl_sim.goal.data import logit
    P = CT._goal_parts(games)
    st_ = CT.starters(games)
    z = CT._goalie_z(P, games, st_[:, ::-1].copy())
    c = P["coef"]
    gl = np.zeros((len(games), 2))
    for j in (0, 1):
        common = (c[12] * (1 - j) + c[13] * P["B"][:, j] + c[14] * P["B"][:, 1 - j] + c[15] * P["af"]
                  + P["spec"]["s_t"] * P["spec"]["c_t"] * P["TR"][:, j] + P["s_date"] * z[:, j])
        gl[:, j] = c[5] + P["delta"][:, 0] + common             # sg 5 EAF, level group 0 (5v5 + EAF)
    return logit(P["T"][:, 5]), gl, P


def pull_tables(games: np.ndarray, season: int = 20242025, arm: str | None = None) -> tuple[dict, dict]:
    """tables["pull"] for the engine, in engine game order. arm: the selected arm (default: select.json)."""
    sel = json.loads((MOD / "select.json").read_text())
    arm = arm or sel["selected"]
    m = json.loads((MOD / f"fold2_{arm}.json").read_text())
    if arm == "P1":
        hz = dict(kind="P1", table=PL.p1_table(m))
    else:
        h0, h1 = PL.p0_tables(m)
        hz = dict(kind="P0", h_first=h0, h_repull=h1)
    L, linfo = en_levels()
    Lg = L.set_index("game_id").reindex(np.asarray(games))
    if Lg.lam_ef.isna().any():
        raise ValueError("games without an EN level")
    cls, gl, _ = goal_eaf(games)
    t = dict(hazard=hz, en_lam=np.stack([Lg.lam_ef.to_numpy(), Lg.lam_ea.to_numpy()], 1),
             p_en_goal=Lg.p_en_goal.to_numpy(), eaf_cls=cls, eaf_game=gl,
             label=PULL_LABEL if arm == "P1" else f"goalie pull: {arm}",
             stand_in={"en_attempts": EN_ATT_LABEL, "en_goal": EN_GOAL_LABEL},
             note="no delayed-penalty state (INV-70); stage 1 reads the penalty-derived strength during a pull")
    return t, dict(arm=arm, levels=linfo, n_games=len(games))
