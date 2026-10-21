"""The engine's DEFAULT table set (INV-63, Lane E3, 2026-10-21; D40-D43).

`default_attr(games)` builds the `tables["attr"]` the closed-loop runners pass with no flags:
  stage 4  L1x-as (SL-R7, D42/D43; L0s M1 K500 baseline + L1x-ot0 terms + as-of Qa scale)   attr["l1x"]
  block    B1a-as on the B0' base (INV-77, D52; was the B0 STAND-IN until 2026-10-21)     attr["p_block_game"] + attr["block_b1aas"]
           (`b0_attr` is the explicit pre-INV-77 path with the B0 STAND-IN, `b1aas_attr` an alias of `default_attr`)
  stage 3  `att_table(games)` serves A3g-c with the 3v3 OT level ON (INV-77; EG-R1 part B); ot3v3=False is the disk table.
           The goalie pull and the shootout stay behind their own flags (tables["pull"], tables["shootout"]).
  miss     S0t STAND-IN (D37)                                                               attr["p_miss_game"]
  goal     C1s (provisional, D40), ORACLE GOALIE (box-score starter faces every SOG, D8)    attr["goal"]
Stage 1 (H3''-LC2 + T2) and stage 3 (A3g-c) are the other `tables` keys (see scripts/run_engine_defaults_v1.py).
Output markers: `stand_in` lists miss S0t only (no `attr`, no `block` label: L1x-as and B1a-as are selected models; `block_model` carries B1a-as),
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


B0_STAND_IN = {k: v for k, v in CT.STAND_IN.items() if k != "attr"}          # pre-INV-77 default: block B0 + miss S0t
DEFAULT_STAND_IN = {k: v for k, v in B0_STAND_IN.items() if k != "block"}     # INV-77: block is B1a-as, miss S0t remains
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


def b0_attr(games: np.ndarray) -> tuple[dict, dict]:
    """Explicit pre-INV-77 path (the INV-63 default): L1x-as + block B0 STAND-IN + S0t + C1s (oracle goalie). Kept so
    the 2026-10-21 loops stay reproducible. Returns (attr, info incl. parity)."""
    t0 = time.time()
    sp, gm, linfo = CT.l0s_m1k500_tables(games)
    lx, xinfo = SV.l1xas_tables(games)
    pb, pm, goal, xg, par, info = _common(games)
    par = dict(l1xas=SV.l1xas_parity(games, sp, gm, lx), **par)
    _check(par)
    attr = dict(state_pdf=sp, game_mult=gm, l1x=lx, p_block_game=pb, p_miss_game=pm, goal=goal, xg=xg, n_type=N_TYPE,
                stand_in=dict(B0_STAND_IN))
    _log(f"default tables + parity {time.time() - t0:.0f}s")
    return attr, dict(parity=par, l0s_level=linfo, l1xas=xinfo, **info)


def default_attr(games: np.ndarray) -> tuple[dict, dict]:
    """The DEFAULT attr (INV-77, Lane E4, D52/D53): `b0_attr` with block B1a-as (SB-R5) on the B0' base replacing the
    B0 STAND-IN: L1x-as + B1a-as + S0t (stand-in) + C1s (oracle goalie). Bit-identical to the pre-INV-77 `b1aas_attr`.
    Block B1a-as on the B0' base replaces the
    B0 STAND-IN (attr["block_b1aas"]; stand_in keeps miss S0t only). Tables from the committed snapshot (never
    recomputed); the engine-served block probability is checked against the offline fold-2 B1a-as prediction."""
    from nhl_sim.block import serve_b1aas as SB
    attr, info = b0_attr(games)
    T, binfo = SB.b1aas_tables(games, attr["p_block_game"])
    par = SB.engine_parity(np.asarray(games, np.int64), attr["p_block_game"], T)
    _check(dict(block_b1aas=par))
    attr["block_b1aas"] = dict(game_logit=T["game_logit"], sc_logit=T["sc_logit"], label=SB.LABEL)
    attr["stand_in"] = {k: v for k, v in attr["stand_in"].items() if k != "block"}
    info = dict(info, block_b1aas=binfo)
    info["parity"] = dict(info["parity"], block_b1aas=par)
    return attr, info


b1aas_attr = default_attr    # pre-INV-77 name of the same builder (runners of 2026-10-21 call it)


def l0s_attr(games: np.ndarray) -> tuple[dict, dict]:
    """Explicit pre-D43 path: stage 4 = L0s STAND-IN (labelled `attr`), the rest as the default."""
    sp, gm, linfo = CT.l0s_m1k500_tables(games)
    pb, pm, goal, xg, par, info = _common(games)
    par = dict(l0s=CT.l0s_parity(games, sp, gm), **par)
    _check(par)
    attr = dict(state_pdf=sp, game_mult=gm, p_block_game=pb, p_miss_game=pm, goal=goal, xg=xg, n_type=N_TYPE,
                stand_in=dict(CT.STAND_IN))
    return attr, dict(parity=par, l0s_level=linfo, **info)


# --------------------------------------------------------------------------- EG-R1 parts B and C (Lane H8b, default off)
ATT_A3GC_FOLD2 = "results/shot_attempt_r3/att_lam_A3g-c_fold2.npy"
SHOOTOUT_LABEL = "shootout S1: rules mechanics, as-of M1 K500 per-attempt success, as-of home-first share (EG-R1 part C)"
OT3V3_LABEL = "3v3 OT attempt level: own as-of M1 K500 (EG-R1 part B), A3g-c cell refit on the training rows"


def att_table(games: np.ndarray, ot3v3: bool = True) -> tuple[np.ndarray, dict]:
    """The stage-3 table served to the engine (A3g-c, fold 2). ot3v3=False: the table as it is on disk (explicit,
    bit-identical to the pre-EG-R1 loops). ot3v3=True (DEFAULT since INV-77): its 3v3 entries re-levelled by the own as-of 3v3 level
    (`end_game.ot_level.served_att_lam`); every other state is bit-identical, and the served 3v3 rows are checked
    against the offline prediction (< 1e-6 relative) before the table is returned."""
    att = np.load(ATT_A3GC_FOLD2)
    if not ot3v3:
        return att, {}
    from nhl_sim.end_game import ot_level as OL
    new, info = OL.served_att_lam(att, games, 2)
    par = OL.served_parity(new, games, 2)
    _log(f"ot3v3 parity: max rel diff {par['max_rel_diff']:.3e} over {par['n_rows']:,} rows")
    if not par["max_rel_diff"] <= TOL:
        raise RuntimeError(f"served 3v3 != offline: {par}")
    return new, dict(label=OT3V3_LABEL, parity=par, **info)


def shootout_tables(games: np.ndarray) -> dict:
    """tables["shootout"] for the engine flag (S1): per-game as-of success p and home-shoots-first share."""
    from nhl_sim.end_game import shootout as SOF
    return dict(SOF.s1_tables(games), label=SHOOTOUT_LABEL)
