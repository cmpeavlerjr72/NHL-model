"""INV-60 (Lane E2): parity cases shared by `scripts/diag_engine_c1s_parity_fixture.py` and
`tests/engine/test_sim_c1s.py`.

Every case runs WITHOUT the new flags (no attr["game_mult"], no 5-group p_block_game, no attr["miss"] / attr["goal"]),
so the engine after the change must reproduce the pre-change engine (7fac157) bit for bit. Cases: the D32 stand-in
fixture cases (SL-R3 era cases + the levelled pdf path) plus the D32 stand-ins switched ON as they were served before
this change (B0 (G, 3, 2) table, L0s levelled by era_mult), synthetic and real-game. Value: (make, per_team_types,
seasons_fn).
"""
from __future__ import annotations

import numpy as np

import attr_parity_cases as A
import standin_parity_cases as C


def syn_standins_on(per_team: bool, seed: int = 31):
    t, g, gt, n, s0 = C.syn_levelled(per_team)
    rng = np.random.default_rng(seed)
    attr = {k: v for k, v in t["attr"].items() if k not in ("pdf", "p_block")}
    attr.update(state_pdf=rng.dirichlet(np.ones(78), size=(7, 2)), p_block_game=rng.uniform(0.1, 0.35, size=(len(g), 3, 2)),
                stand_in={"block": "STAND-IN test block", "attr": "STAND-IN test attr"})
    t["attr"] = attr
    return t, g, gt, n, s0


def real_standins_on():
    t, g, gt, n, s0 = C.real_levelled()
    rng = np.random.default_rng(37)
    attr = {k: v for k, v in t["attr"].items() if k not in ("pdf", "p_block")}
    attr.update(state_pdf=rng.dirichlet(np.ones(78), size=(7, 2)), p_block_game=rng.uniform(0.1, 0.35, size=(len(g), 3, 2)),
                stand_in={"block": "STAND-IN test block", "attr": "STAND-IN test attr"})
    t["attr"] = attr
    return t, g, gt, n, s0


CASES = dict(C.CASES)
CASES.update({
    "syn_standins_on": (lambda: syn_standins_on(False), False, C.mixed_seasons),
    "syn_standins_on_t2": (lambda: syn_standins_on(True), True, C.mixed_seasons),
    "real_standins_on": (real_standins_on, True, lambda G: np.full(G, 20242025)),
})


def real_available() -> bool:
    return A.real_available()


def run(sim_module, name, era):
    mk, per_team, sfn = CASES[name]
    t, g, gt, n, s0 = mk()
    kw = {} if sfn is None else dict(seasons=sfn(len(g)))
    return sim_module.simulate(t, g, gt, n, era, seed0=s0, per_team_types=per_team, **kw)
