"""SB-R1 data layer (docs/models/block/experiments.md SB-R1; cascade stage 5, block decision; D23, D24).

Rows: one per stage-3 target attempt (SHOT, MISS, BLOCK, GOAL; shootout and penalty shots excluded), from the stage-4
attempt tables `data/processed/shot_attribute/attempt_attr_v1_*.parquet` (read only). y = blocked.
Strength group (ES, PP, PK, ENF, ENA) from the shooting team's pre-event view. Gated rows: grp 0..2. EN rows are
fit and predicted with the ES level group (labelled) and reported only.

Level groups: ES (grp 0 and the EN groups, which take the ES level), PP, PK. Level = as-of league BLOCK SHARE per
level group, entered as a logit offset logit(s_asof) - logit(s_train) with coefficient 1.

Constructions (one value per game date, from games dated strictly earlier):
  M0   last season's final share, constant all season
  E    recording-era intercept: pooled share of the fold's TRAINING rows of the game's era (era 2 from 2023-24, D24,
       computed here from the season id); an era without training rows falls back to the pooled training share
  M1_K (blocks_std + K s_prev) / (attempts_std + K), K in {500, 2000, 8000} attempts
  M2   M1 with K = 2000 and the season-to-date counts discounted by 0.5^(gap days / H), H in {30, 60}
  O    oracle: the season's own final share (diagnostic, never selectable)
s_prev for the first data season (2021-22) is its own final share (look-ahead, labelled; its rows are never judged).
created_at = 6 h after the last puck drop of the previous game date (LC-2 form), asserted < puck_drop.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.data.load import PROCESSED, load_games
from nhl_sim.shot_attribute.tables import OPP_RATING_GROUP, RATING_GROUP, asof_arena_distance  # read-only use
from nhl_sim.strength_state.tables import assert_pregame

SA = PROCESSED / "shot_attribute"
OUT = PROCESSED / "block"
SEASONS = [20212022, 20222023, 20232024, 20242025]
ERA2_FROM = 20232024
LEVEL_GROUP = np.array([0, 1, 2, 0, 0], np.int8)
LG_NAMES = ("ES+EN", "PP", "PK")
GRID_W = (0.5, 0.7, 0.85, 1.0)
GRID_B = (300, 1000, 3000)
ARENA_C = 1200.0
RG = ("es", "pp", "pk")
OPP_RG = {0: 0, 1: 2, 2: 1}
SIMPLICITY = ("M0", "E", "M1", "M2")
COLS = ["game_id", "season", "game_type", "t", "team", "is_home", "blocked", "is_goal", "st", "grp", "sc", "period",
        "ptype", "rebound", "rush"]


def era_of(season) -> np.ndarray:
    return np.where(np.asarray(season) >= ERA2_FROM, 2, 1).astype(np.int8)


def wkey(w, b):
    return f"w{float(w)}_b{int(b)}"


def logit(p):
    p = np.clip(p, 1e-9, 1 - 1e-9)
    return np.log(p / (1 - p))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def load_attempts(seasons=SEASONS) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(SA / f"attempt_attr_v1_{s}.parquet", columns=COLS) for s in seasons],
                     ignore_index=True)


def game_table() -> pd.DataFrame:
    """One row per game: game_id, season, date (str), drop (UTC), home_id, away_id, arena."""
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet",
                         columns=["game_id", "season", "date", "drop", "team_id", "is_home"])
    g = tg[tg.season.isin(SEASONS)].groupby("game_id").agg(season=("season", "first"), date=("date", "first"),
                                                           drop=("drop", "first")).reset_index()
    gm = load_games(SEASONS, columns=["game_id", "home_id", "away_id", "neutral_site", "venue"])
    g = g.merge(gm.drop(columns="season", errors="ignore"), on="game_id", how="left", validate="one_to_one")
    ns = g.neutral_site.astype(bool)
    g["arena"] = np.where(ns, "venue:" + g.venue.astype(str), "team:" + g.home_id.astype(str))
    return g.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)


# ----------------------------------------------------------------------------------------------- level
def game_counts(a: pd.DataFrame, games: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """(G, 3) block counts and attempt counts per level group (all game rows, EN pooled into ES)."""
    gi = pd.Series(np.arange(len(games)), index=games.game_id.to_numpy())
    ix = gi.reindex(a.game_id.to_numpy()).to_numpy()
    if np.isnan(ix.astype(float)).any():
        raise ValueError("attempt rows for a game missing from the game list")
    ix = ix.astype(np.int64)
    lg = LEVEL_GROUP[a.grp.to_numpy()]
    B = np.zeros((len(games), 3))
    T = np.zeros((len(games), 3))
    np.add.at(B, (ix, lg), a.blocked.to_numpy().astype(float))
    np.add.at(T, (ix, lg), 1.0)
    return B, T


def asof_levels(a: pd.DataFrame, games: pd.DataFrame, specs: dict):
    """specs {name: (kind, param)}, kind M0 / M1 (K) / M2 ((half_life, K)) / O. -> (meta, {name: (G, 3) shares})."""
    games = games.sort_values(["date", "game_id"], kind="stable").reset_index(drop=True)
    B, T = game_counts(a, games)
    seasons = sorted(games.season.unique())
    final = {}
    for s in seasons:
        m = (games.season == s).to_numpy()
        final[s] = B[m].sum(0) / T[m].sum(0)
    out = {n: np.zeros((len(games), 3)) for n in specs}
    created = np.full(len(games), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    last_drop = None
    for i, season in enumerate(seasons):
        s_prev = final[seasons[i - 1]] if i > 0 else final[season]
        idx_s = np.flatnonzero((games.season == season).to_numpy())
        dates = games.date.to_numpy()[idx_s]
        st = {n: [np.zeros(3), np.zeros(3)] for n in specs}
        prev_date = None
        for d in np.unique(dates):
            ix = idx_s[dates == d]
            if last_drop is not None:
                created[ix] = np.datetime64((pd.Timestamp(last_drop) + pd.Timedelta(hours=6)).tz_convert(None))
            gap = 0.0 if prev_date is None else float((pd.Timestamp(d) - pd.Timestamp(prev_date)).days)
            for n, (kind, par) in specs.items():
                nb, nt = st[n]
                if kind == "M0":
                    v = s_prev
                elif kind == "O":
                    v = final[season]
                elif kind == "M1":
                    v = (nb + par * s_prev) / (nt + par)
                elif kind == "M2":
                    hl, K = par
                    f = 0.5 ** (gap / hl)
                    nb, nt = nb * f, nt * f
                    st[n] = [nb, nt]
                    v = (nb + K * s_prev) / (nt + K)
                else:
                    raise ValueError(kind)
                out[n][ix] = v
            for n in specs:
                st[n] = [st[n][0] + B[ix].sum(0), st[n][1] + T[ix].sum(0)]
            prev_date = d
            last_drop = pd.to_datetime(games["drop"].to_numpy()[ix], utc=True).max()
    meta = pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": games.season.to_numpy(),
                         "created_at": pd.to_datetime(created).tz_localize("UTC"),
                         "puck_drop": pd.to_datetime(games["drop"], utc=True)})
    assert_pregame(meta)
    return meta, out


def share_table(a: pd.DataFrame) -> np.ndarray:
    """(3,) pooled block share per level group."""
    lg = LEVEL_GROUP[a.grp.to_numpy()]
    n = np.bincount(lg, minlength=3).astype(float)
    b = np.bincount(lg, weights=a.blocked.to_numpy().astype(float), minlength=3)
    if (n == 0).any():
        raise ValueError("empty level group")
    return b / n


def era_level(a_train: pd.DataFrame, games: pd.DataFrame) -> np.ndarray:
    """E: per game (order of `games`) the pooled training share of the game's era; fallback to all training."""
    pooled = share_table(a_train)
    era_tr = era_of(a_train.season.to_numpy())
    by = {e: (share_table(a_train[era_tr == e]) if (era_tr == e).any() else pooled) for e in (1, 2)}
    return np.stack([by[e] for e in era_of(games.season.to_numpy())])


def level_frame(meta: pd.DataFrame, S: np.ndarray) -> pd.DataFrame:
    f = meta[["game_id", "season", "created_at", "puck_drop"]].copy()
    for g in range(3):
        f[f"s_{g}"] = S[:, g]
    return f


def row_offset(rows: pd.DataFrame, level: pd.DataFrame, s_train: np.ndarray) -> np.ndarray:
    """Per-row logit offset logit(s_asof[game, level group]) - logit(s_train[level group])."""
    L = level.set_index("game_id")[["s_0", "s_1", "s_2"]].reindex(rows.game_id.to_numpy()).to_numpy()
    if np.isnan(L).any():
        raise ValueError("rows without a level")
    lg = LEVEL_GROUP[rows.grp.to_numpy()]
    s = L[np.arange(len(rows)), lg]
    return logit(s) - logit(s_train[lg])


# --------------------------------------------------------------------------------------------- ratings
def asof_block_ratings(long: pd.DataFrame, w: float, b: float) -> pd.DataFrame:
    """long: one row per team-game: game_id, season, date, drop, team_id, xf, nf, xa, na (blocked-attempt and attempt
    counts for / against in one rating group). Shrunk block log-odds relative to the snapshot league mean (L1):
    r = logit((X + b mu) / (N + b)), logit(mu) = logit(league share to date) + w x last season's final relative value,
    minus the cross-team mean of r. Only games dated before the snapshot (same season) enter it.
    -> game_id, team_id, rf, ra, created_at, puck_drop."""
    out = []
    prev_final = {"f": {}, "a": {}}
    prev_lg = {"f": 0.25, "a": 0.25}
    last_drop = None
    for season in sorted(long.season.unique()):
        L = long[long.season == season]
        teams = np.sort(L.team_id.unique())
        tix = {t_: i for i, t_ in enumerate(teams)}
        X = {k: np.zeros(len(teams)) for k in ("f", "a")}
        Nn = {k: np.zeros(len(teams)) for k in ("f", "a")}
        pri = {k: np.array([prev_final[k].get(t_, 0.0) for t_ in teams]) for k in ("f", "a")}

        def snap():
            res = {}
            for k in ("f", "a"):
                lg = X[k].sum() / Nn[k].sum() if Nn[k].sum() > 0 else prev_lg[k]
                mu = sigmoid(logit(lg) + w * pri[k])
                r = logit((X[k] + b * mu) / (Nn[k] + b))
                res[k] = r - r.mean()
            return res

        for d in np.sort(L.date.unique()):
            s = snap()
            day = L[L.date == d]
            ti = day.team_id.map(tix).to_numpy()
            created = None if last_drop is None else pd.Timestamp(last_drop) + pd.Timedelta(hours=6)
            out.append(pd.DataFrame({"game_id": day.game_id.to_numpy(), "team_id": day.team_id.to_numpy(),
                                     "rf": s["f"][ti], "ra": s["a"][ti], "created_at": created,
                                     "puck_drop": pd.to_datetime(day["drop"], utc=True)}))
            for k, (xc, nc) in {"f": ("xf", "nf"), "a": ("xa", "na")}.items():
                np.add.at(X[k], ti, day[xc].to_numpy(float))
                np.add.at(Nn[k], ti, day[nc].to_numpy(float))
            last_drop = pd.to_datetime(day["drop"], utc=True).max()
        fin = snap()
        prev_final = {k: dict(zip(teams, fin[k])) for k in ("f", "a")}
        prev_lg = {k: X[k].sum() / Nn[k].sum() for k in ("f", "a")}
    r = pd.concat(out, ignore_index=True)
    r["created_at"] = pd.to_datetime(r.created_at, utc=True)
    return r


def attach_ids(a: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    g = games[["game_id", "home_id", "away_id"]]
    a = a.merge(g, on="game_id", how="left", validate="many_to_one")
    a["team_id"] = np.where(a.team == 0, a.home_id, a.away_id)
    a["opp_id"] = np.where(a.team == 0, a.away_id, a.home_id)
    return a


def build_ratings(a: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """All seasons, all grid cells, groups ES / PP / PK. Fold independent (counts only; no trained input)."""
    r = attach_ids(a, games)
    r = r[r.grp <= 2]
    r = r.assign(y=r.blocked.astype(float))
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet",
                         columns=["game_id", "season", "date", "drop", "team_id"])
    tg = tg[tg.season.isin(SEASONS)].reset_index(drop=True)
    grid = tg[["game_id", "team_id"]].copy()
    longs = {}
    for gi_, g in enumerate(RG):
        fo = r[r.grp == gi_].groupby(["game_id", "team_id"]).agg(xf=("y", "sum"), nf=("y", "size"))
        ag = r[r.grp == OPP_RG[gi_]].groupby(["game_id", "opp_id"]).agg(xa=("y", "sum"), na=("y", "size"))
        ag.index = ag.index.set_names(["game_id", "team_id"])
        L = tg.join(fo, on=["game_id", "team_id"]).join(ag, on=["game_id", "team_id"])
        longs[g] = L.fillna({"xf": 0.0, "nf": 0, "xa": 0.0, "na": 0}).sort_values(["date", "game_id"])
    first = True
    for w in GRID_W:
        for b in GRID_B:
            for g in RG:
                rr = asof_block_ratings(longs[g], w, b)
                assert_pregame(rr)
                rr = rr.rename(columns={"rf": f"rf_{g}_{wkey(w, b)}", "ra": f"ra_{g}_{wkey(w, b)}"})
                keep = ["game_id", "team_id", f"rf_{g}_{wkey(w, b)}", f"ra_{g}_{wkey(w, b)}"]
                if first:
                    keep += ["created_at", "puck_drop"]
                    first = False
                grid = grid.merge(rr[keep], on=["game_id", "team_id"], how="left", validate="one_to_one")
    if grid.drop(columns=["created_at"]).isna().any().any():
        raise ValueError("missing ratings")
    return grid


def build_arena(a: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """As-of arena BLOCK-recording factor: log((A + c ybar) / (E + c ybar)) over earlier-dated games at the arena,
    A = blocks, E = both-teams expected blocks (shooting team's road for-offset + defending team's road against-offset),
    all goalies-in attempts (grp 0..2). Reuses shot_attribute.tables.asof_arena_distance with d := blocked (0/1)."""
    r = attach_ids(a, games)
    r = r[r.grp <= 2].merge(games[["game_id", "date", "drop", "arena", "neutral_site"]], on="game_id", how="left",
                            validate="many_to_one")
    ns = r.neutral_site.astype(bool)
    u = pd.DataFrame({"game_id": r.game_id, "season": r.season, "date": r.date, "drop": r["drop"], "arena": r.arena,
                      "shoot_id": r.team_id, "def_id": r.opp_id, "shooter_road": (r.team == 1) | ns,
                      "defender_road": (r.team == 0) | ns, "d": r.blocked.astype(float)})
    af = asof_arena_distance(u, ARENA_C)
    assert_pregame(af)
    af["c"] = ARENA_C
    miss = set(games.game_id) - set(af.game_id)
    if miss:
        raise ValueError(f"{len(miss)} games without an arena factor")
    return af


def assemble(a: pd.DataFrame, games: pd.DataFrame, ratings: pd.DataFrame, arena: pd.DataFrame, w: float, b: float) -> pd.DataFrame:
    """Attach features for ratings cell (w, b): own_r (shooting team's blocked-against rating, row's rating group),
    opp_r (defending team's blocks-for rating at the opposing group), b2b own / opp, arena_f, arena, clock, l0."""
    r = attach_ids(a, games)
    r = r.merge(games[["game_id", "date", "arena"]], on="game_id", how="left", validate="many_to_one")
    k = wkey(w, b)
    cols = {f"{p}_{g}_{k}": f"{p}{i}" for p in ("rf", "ra") for i, g in enumerate(RG)}
    rt = ratings[["game_id", "team_id", *cols]].rename(columns=cols)
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "team_id", "b2b"])
    own = rt.merge(tg, on=["game_id", "team_id"], how="left", validate="one_to_one")
    r = r.merge(own.rename(columns={"b2b": "b2b_own"}), on=["game_id", "team_id"], how="left", validate="many_to_one")
    r = r.merge(own.rename(columns={"team_id": "opp_id", "b2b": "b2b_opp",
                                    **{f"{p}{i}": f"o_{p}{i}" for p in ("rf", "ra") for i in range(3)}}),
                on=["game_id", "opp_id"], how="left", validate="many_to_one")
    rg = RATING_GROUP[r.grp.to_numpy()]
    og = OPP_RATING_GROUP[rg]
    ix = np.arange(len(r))
    r["own_r"] = r[["rf0", "rf1", "rf2"]].to_numpy()[ix, rg]
    r["opp_r"] = r[["o_ra0", "o_ra1", "o_ra2"]].to_numpy()[ix, og]
    r["own_rf_es"], r["opp_ra_es"] = r.rf0, r.o_ra0
    r = r.merge(arena[["game_id", "arena_f"]], on="game_id", how="left", validate="many_to_one")
    for c in ("own_r", "opp_r", "b2b_own", "b2b_opp", "arena_f"):
        if r[c].isna().any():
            raise ValueError(f"missing feature {c} on {int(r[c].isna().sum())} rows")
    r["clock"] = (r.t // 60).astype(np.int32)
    r["l0"] = (r.grp.astype(np.int64) * 2 + r.ptype).astype(np.int8)
    r["y"] = r.blocked.astype(np.int8)
    return r.drop(columns=[c for c in r.columns if c.startswith(("rf", "ra", "o_r"))])
