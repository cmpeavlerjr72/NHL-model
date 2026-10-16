"""SL-R3 recording-era flag (GameState.rec_era, D24): parity cases shared by `scripts/diag_engine_era_parity_fixture.py`
and `tests/engine/test_sim_era_flag.py`.

Every case runs WITHOUT the levelled stage-4 path (no attr["era_mult"]), so the engine after the change must reproduce
the pre-change engine (27cffc0) bit for bit: the stage-4 option off (stage-1 stub, stage-3 attempts, T2 types, the
real incumbent) and the SL-R1 cdf path (attr on, unlevelled). Each case returns (tables, game_ids, game_types, n_seeds,
seed0); the dict value also carries the per_team_types flag.
"""
from __future__ import annotations

import numpy as np

import attr_parity_cases as A
import t2_parity_cases as T2


def syn_attr(per_team: bool, seed: int = 11):
    t, g, gt, n, s0 = T2.synthetic(per_team, True)
    rng = np.random.default_rng(seed)
    p = rng.dirichlet(np.ones(78) * 0.5, size=(len(g), 2, 2, 3, 7))
    t["attr"] = dict(cdf=np.cumsum(p, -1).astype(np.float32), interval_of_minute=(np.arange(100) >= 60).astype(np.int64),
                     p_block=np.array([0.25, 0.2, 0.3, 0.25, 0.25]), xg=rng.uniform(0.01, 0.2, size=(78, 3)), n_type=6)
    return t, g, gt, n, s0


def real_attr():
    t, g, gt, n, s0 = A.real_incumbent()
    rng = np.random.default_rng(5)
    p = rng.dirichlet(np.ones(78), size=(len(g), 2, 2, 3, 7))
    t["attr"] = dict(cdf=np.cumsum(p, -1).astype(np.float32), interval_of_minute=(np.arange(100) >= 60).astype(np.int64),
                     p_block=np.array([0.27, 0.2, 0.3, 0.27, 0.27]), xg=rng.uniform(0.02, 0.15, size=(78, 3)), n_type=6)
    return t, g, gt, n, s0


CASES = {
    "syn_stub": (lambda: T2.synthetic(False, False), False),
    "syn_attempts": (lambda: T2.synthetic(False, True), False),
    "syn_attempts_t2": (lambda: T2.synthetic(True, True), True),
    "real_incumbent": (A.real_incumbent, True),
    "syn_attr_cdf": (lambda: syn_attr(False), False),
    "syn_attr_cdf_t2": (lambda: syn_attr(True), True),
    "real_attr_cdf": (real_attr, True),
}
