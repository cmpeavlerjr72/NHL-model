"""The engine's DEFAULT table set (INV-63, Lane E3, 2026-10-21; D40-D43).

`default_attr(games)` builds the `tables["attr"]` the closed-loop runners pass with no flags:
  stage 4  L1x-as (SL-R7, D42/D43; L0s M1 K500 baseline + L1x-ot0 terms + as-of Qa scale)   attr["l1x"]
  block    B0 STAND-IN, own 4v4 / 3v3 groups (INV-54)                                       attr["p_block_game"]
  miss     S0t STAND-IN (D37)                                                               attr["p_miss_game"]
  goal     C1s (provisional, D40), ORACLE GOALIE (box-score starter faces every SOG, D8)    attr["goal"]
Stage 1 (H3''-LC2 + T2) and stage 3 (A3g-c) are the other `tables` keys (see scripts/run_engine_defaults_v1.py).
Output markers: `stand_in` lists block B0 and miss S0t only (no `attr` label: L1x-as is a selected model),
`attr_model` = the L1x-as label, `goal_model`, `oracle_goalie`.

`l0s_attr(games)` is the explicit pre-D43 path (L0s stand-in, labelled `attr` in `stand_in`), kept so the 2026-10-16 / 
2026-10-21 INV-60 loops stay reproducible. Nothing in sim.py changed: the flags are the same, only the table builder
that the runners call changed. The xG_ref goal stub (`attr["xg"]` without `goal`) stays behind its own flag.
Every served component is checked against its offline fold-2 prediction (< 1e-6) before it is returned.
"""
from __future__ import annotations

import time

import numpy as np

from nhl_sim.engine import c1s_tables as CT
from nhl_sim.shot_attribute import serve_l1xas as SV
from nhl_sim.shot_attribute.models import SA
from nhl_sim.shot_attribute.tables import N_TYPE


DEFAULT_STAND_IN = {k: v for k, v in CT.STAND_IN.items() if k != "attr"}
TOL = 1e-6


def _log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S %z"), msg, flush=True)


def _check(par):
    for k, v in par.items():
        _log(f"{k} parity: max |diff| {v['max_abs_diff']:.3e} over {v['n_rows']:,} rows")
    bad = {k: v["max_abs_diff"] for k, v in par.items() if not v["max_abs_diff"] <= TOL}
    if bad:
        raise RuntimeError(f"served != offline: {bad}")


def _common(games):
    pb, binfo = CT.block_b0g_table(games)
    pm, minfo = CT.miss_s0t_table(games)
    P = CT._goal_parts(games)
    goal, ginfo = CT.goal_c1s_tables(games, P=P)
    par = dict(block=CT.b0g_parity(games, pb, binfo), miss=CT.miss_parity(games, pm), goal=CT.goal_parity(games, goal, P))
    info = dict(block=binfo, miss=minfo, goal=ginfo)
    xg = np.load(SA / "xg_ref_v1_f2.npy")[:, :3]
    return pb, pm, goal, xg, par, info


def default_attr(games: np.ndarray) -> tuple[dict, dict]:
    """The default attr: L1x-as + B0 + S0t + C1s (oracle goalie). Returns (attr, info incl. parity)."""
    t0 = time.time()
    sp, gm, linfo = CT.l0s_m1k500_tables(games)
    lx, xinfo = SV.l1xas_tables(games)
    pb, pm, goal, xg, par, info = _common(games)
    par = dict(l1xas=SV.l1xas_parity(games, sp, gm, lx), **par)
    _check(par)
    attr = dict(state_pdf=sp, game_mult=gm, l1x=lx, p_block_game=pb, p_miss_game=pm, goal=goal, xg=xg, n_type=N_TYPE,
                stand_in=dict(DEFAULT_STAND_IN))
    _log(f"default tables + parity {time.time() - t0:.0f}s")
    return attr, dict(parity=par, l0s_level=linfo, l1xas=xinfo, **info)


def l0s_attr(games: np.ndarray) -> tuple[dict, dict]:
    """Explicit pre-D43 path: stage 4 = L0s STAND-IN (labelled `attr`), the rest as the default."""
    sp, gm, linfo = CT.l0s_m1k500_tables(games)
    pb, pm, goal, xg, par, info = _common(games)
    par = dict(l0s=CT.l0s_parity(games, sp, gm), **par)
    _check(par)
    attr = dict(state_pdf=sp, game_mult=gm, p_block_game=pb, p_miss_game=pm, goal=goal, xg=xg, n_type=N_TYPE,
                stand_in=dict(CT.STAND_IN))
    return attr, dict(parity=par, l0s_level=linfo, **info)
