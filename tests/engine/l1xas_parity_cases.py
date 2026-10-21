"""SL-R7 L1x-as (Lane A7): parity cases shared by `scripts/diag_engine_l1xas_parity_fixture.py` and
`tests/engine/test_sim_l1xas.py`. Every case runs WITHOUT attr["l1x"], so the engine after the change must reproduce
the pre-change engine (80f0b2e, Lane E2 engine_c1s) bit for bit: the INV-60 cases (c1s_parity_cases) plus the full
INV-60 stack switched on (L0s state_pdf + game_mult, B0 (G, 5, 2), miss S0t, goal C1s), synthetic and real-game."""
from __future__ import annotations

import numpy as np

import c1s_parity_cases as C1
import standin_parity_cases as C


def _stack(t, g, seed):
    G = len(g)
    rng = np.random.default_rng(seed)
    xg = t["attr"]["xg"]
    lx = np.log(xg / (1 - xg))
    attr = {k: v for k, v in t["attr"].items() if k not in ("pdf", "p_block", "era_mult")}
    attr.update(state_pdf=rng.dirichlet(np.ones(78), size=(7, 2)), game_mult=rng.uniform(0.8, 1.25, size=(G, 3, 78)),
                p_block_game=rng.uniform(0.1, 0.35, size=(G, 5, 2)), p_miss_game=rng.uniform(0.2, 0.45, size=(G, 3, 2, 78)),
                goal=dict(cls_logit=lx[:, [0, 1, 2, 0, 0]], game_logit=rng.normal(0, 0.1, (G, 2, 5)), sc_logit=np.zeros(7),
                          goalie_id=np.arange(2 * G).reshape(G, 2) + 8470000, label="goal: test",
                          oracle_goalie="ORACLE GOALIE (test)"),
                stand_in={"block": "STAND-IN test block", "attr": "STAND-IN test attr", "miss": "STAND-IN test miss"})
    t["attr"] = attr
    return t


def syn_stack(per_team: bool, seed: int = 53):
    t, g, gt, n, s0 = C.syn_levelled(per_team)
    return _stack(t, g, seed), g, gt, n, s0


def real_stack():
    t, g, gt, n, s0 = C.real_levelled()
    return _stack(t, g, 59), g, gt, n, s0


CASES = dict(C1.CASES)
CASES.update({
    "syn_inv60_stack": (lambda: syn_stack(False), False, C.mixed_seasons),
    "syn_inv60_stack_t2": (lambda: syn_stack(True), True, C.mixed_seasons),
    "real_inv60_stack": (real_stack, True, lambda G: np.full(G, 20242025)),
})


def real_available() -> bool:
    return C1.real_available()


def run(sim_module, name, era):
    mk, per_team, sfn = CASES[name]
    t, g, gt, n, s0 = mk()
    kw = {} if sfn is None else dict(seasons=sfn(len(g)))
    return sim_module.simulate(t, g, gt, n, era, seed0=s0, per_team_types=per_team, **kw)
