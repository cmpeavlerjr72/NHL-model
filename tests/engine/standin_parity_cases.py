"""D32 stand-ins (block B0, stage-4 L0s): parity cases shared by `scripts/diag_engine_standin_parity_fixture.py` and
`tests/engine/test_sim_standins.py`.

Every case runs WITHOUT the stand-in flags (no attr["p_block_game"], no attr["state_pdf"]), so the engine after the
change must reproduce the pre-change engine (3ce7112) bit for bit. The cases are the SL-R3 era cases (stage-4 off,
stage-3 attempts, T2 types, real incumbent, SL-R1 cdf path) plus the SL-R3 LEVELLED pdf path (attr["pdf"] +
attr["era_mult"], seasons= given), which the earlier fixtures do not cover. Value: (make, per_team_types, seasons_fn).
"""
from __future__ import annotations

import numpy as np

import attr_parity_cases as A
import era_parity_cases as E
import t2_parity_cases as T2


def syn_levelled(per_team: bool, seed: int = 13):
    t, g, gt, n, s0 = T2.synthetic(per_team, True)
    rng = np.random.default_rng(seed)
    p = rng.dirichlet(np.ones(78) * 0.5, size=(len(g), 2, 2, 3, 7)).astype(np.float32)
    em = np.full((3, 3, 78), np.nan)
    em[1:] = rng.uniform(0.7, 1.4, size=(2, 3, 78))
    t["attr"] = dict(pdf=p, era_mult=em, interval_of_minute=(np.arange(100) >= 60).astype(np.int64),
                     p_block=np.array([0.25, 0.2, 0.3, 0.25, 0.25]), xg=rng.uniform(0.01, 0.2, size=(78, 3)), n_type=6)
    return t, g, gt, n, s0


def real_levelled():
    t, g, gt, n, s0 = A.real_incumbent()
    rng = np.random.default_rng(17)
    p = rng.dirichlet(np.ones(78), size=(len(g), 2, 2, 3, 7)).astype(np.float32)
    em = np.full((3, 3, 78), np.nan)
    em[1:] = rng.uniform(0.8, 1.25, size=(2, 3, 78))
    t["attr"] = dict(pdf=p, era_mult=em, interval_of_minute=(np.arange(100) >= 60).astype(np.int64),
                     p_block=np.array([0.27, 0.2, 0.3, 0.27, 0.27]), xg=rng.uniform(0.02, 0.15, size=(78, 3)), n_type=6)
    return t, g, gt, n, s0


def mixed_seasons(G):
    return np.where(np.arange(G) % 2 == 0, 20222023, 20242025)


CASES = {name: (mk, per_team, None) for name, (mk, per_team) in E.CASES.items()}
CASES.update({
    "syn_levelled": (lambda: syn_levelled(False), False, mixed_seasons),
    "syn_levelled_t2": (lambda: syn_levelled(True), True, mixed_seasons),
    "real_levelled": (real_levelled, True, lambda G: np.full(G, 20242025)),
})


def run(sim_module, name, era):
    mk, per_team, sfn = CASES[name]
    t, g, gt, n, s0 = mk()
    kw = {} if sfn is None else dict(seasons=sfn(len(g)))
    return sim_module.simulate(t, g, gt, n, era, seed0=s0, per_team_types=per_team, **kw)
