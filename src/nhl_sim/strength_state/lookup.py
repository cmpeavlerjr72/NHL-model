"""Lookup tables the closed-loop engine reads (no live model calls in the sim loop).

hazard   lam[g, team, minute, st, sc, pd] penalty-taking events per hour, from a fitted hazard arm, for every
         reachable engine state (st 0..4; the engine has no goalie pull so 'other' is unreachable)
types    p[st, sc, period, class] from a fitted type arm (season feature fixed at the last training season)
coinc    empirical coincidental stoppages (smp flag, PIM) of the last training season
goals    LABELLED STUB: league goal rate per (own skaters, opp skaters), both goalies in, last training season
stops    LABELLED STUB: league whistle (STOPPAGE) rate per second in regular-season OT, last training season
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.strength_state import models as M
from nhl_sim.strength_state.timeline import EV_COLS, season_timeline

N_MIN = 100           # game minutes tabulated; later playoff-OT minutes reuse the last one
N_ST_ENGINE = 5


def minute_grid():
    m = np.arange(N_MIN)
    per = np.where(m < 60, m // 20 + 1, 4)
    return m, per, (m >= 60).astype(int), ((m >= 55) & (m < 60)).astype(int)


def hazard_table(arm: str, model, team_rows: pd.DataFrame, chunk: int = 64) -> np.ndarray:
    """team_rows: one row per (game, team) with game_id, team, season, season_f, taken_own, drawn_opp, is_home,
    b2b_own, b2b_opp. Returns float32 (G, 2, N_MIN, 5, 5, 5) penalty-taking events per hour, games sorted."""
    games = np.sort(team_rows.game_id.unique())
    m, per, ptype, last5 = minute_grid()
    st, sc, pdf = np.meshgrid(np.arange(N_ST_ENGINE), np.arange(5), np.arange(5), indexing="ij")
    K = st.size
    base = pd.DataFrame({"minute": np.repeat(np.arange(N_MIN), K), "st": np.tile(st.ravel(), N_MIN),
                         "sc": np.tile(sc.ravel(), N_MIN), "pdiff": np.tile(pdf.ravel(), N_MIN)})
    base["period"], base["ptype"], base["last5"] = per[base.minute], ptype[base.minute], last5[base.minute]
    base["clock"], base["t0"], base["exposure_s"] = base.minute, base.minute * 60, 3600
    tr = team_rows.sort_values(["game_id", "team"]).reset_index(drop=True)
    if len(tr) != 2 * len(games):
        raise ValueError("need exactly one row per (game, team)")
    B = len(base)
    out = np.zeros((len(tr), B), np.float32)
    for a in range(0, len(tr), chunk):
        part = tr.iloc[a:a + chunk]
        big = base.loc[np.tile(np.arange(B), len(part))].reset_index(drop=True)
        for c in ("season", "season_f", "taken_own", "drawn_opp", "is_home", "b2b_own", "b2b_opp"):
            big[c] = np.repeat(part[c].to_numpy(), B)
        big["cell"] = (big.season_f.astype(np.int64) % 10000) * 100 + big.st * 10 + big.ptype
        mu = M.predict_lgb(model, big) if arm.startswith("H3") else M.predict_glm(model, big)
        out[a:a + len(part)] = np.asarray(mu, np.float32).reshape(len(part), B)
    return out.reshape(len(games), 2, N_MIN, N_ST_ENGINE, 5, 5)


def type_table(arm: str, model, season_f: int) -> np.ndarray:
    st, sc, per = np.meshgrid(np.arange(6), np.arange(5), np.arange(1, 5), indexing="ij")
    t = pd.DataFrame({"st": st.ravel(), "sc": sc.ravel(), "period": per.ravel(), "season_f": season_f})
    p = M.predict_t1(model, t) if arm == "T1" else M.predict_t0(model, t)
    return p.reshape(6, 5, 4, len(M.TYPE_CLASSES)).astype(np.float64)


def coinc_table(season: int, version="v1"):
    c = pd.read_parquet(M.SS / f"coinc_bundles_{version}.parquet")
    c = c[c.season == season]
    return c.smp.to_numpy(bool), c.pim.to_numpy(np.int16)


def stub_tables(season: int):
    """Goal-rate stub (per hour, index [own_sk-3, opp_sk-3]) and RS-OT whistle stub (per second), from one
    TRAINING season's replay. Returns dict with goal_rate, goal_n, goal_exposure_h, stop_rate_ot."""
    from nhl_sim.data.load import load_events
    ev = load_events([season], columns=EV_COLS)
    tl = season_timeline(ev)
    games, sk, prev = tl["games"], tl["sk"], tl["prev"]
    N, T = sk.shape[:2]
    played = np.arange(T)[None, :] < games.end_t.to_numpy()[:, None]
    gin = (prev[..., 0] == 1) & (prev[..., 3] == 1)
    expo = np.zeros((3, 3))
    for own, opp in ((0, 1), (1, 0)):
        a = np.clip(sk[..., own] - 3, 0, 2)
        b = np.clip(sk[..., opp] - 3, 0, 2)
        m = played & gin
        np.add.at(expo, (a[m], b[m]), 1)
    gi = {g: i for i, g in enumerate(games.game_id)}
    x = ev[(ev.event == "GOAL") & (ev.period_type != "SO")]
    i = x.game_id.map(gi).to_numpy()
    t = np.clip(x.game_time_s.to_numpy().astype(int) - 1, 0, T - 1)
    own = np.where(x.owner_is_home.astype(bool), 0, 1)
    ok = gin[i, t]
    n = np.zeros((3, 3))
    np.add.at(n, (np.clip(sk[i, t, own] - 3, 0, 2)[ok], np.clip(sk[i, t, 1 - own] - 3, 0, 2)[ok]), 1)
    rate = (n + 0.5) / (expo / 3600.0 + 0.5 / (n.sum() / (expo.sum() / 3600.0)))
    rs_ot = (np.arange(T)[None, :] >= 3600) & played & (games.game_type.to_numpy()[:, None] == 2)
    st = ev[(ev.event == "STOPPAGE") & (ev.period_type == "OT") & (ev.game_type == 2)]
    stop_rate = len(st) / max(1, rs_ot.sum())
    return dict(goal_rate=rate, goal_n=n, goal_exposure_h=expo / 3600.0, stop_rate_ot=stop_rate)
