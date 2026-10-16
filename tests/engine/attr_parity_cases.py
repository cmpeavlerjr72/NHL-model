"""SL-R1 engine flag (shot attributes): parity cases shared by `scripts/diag_engine_attr_parity_fixture.py` and
`tests/engine/test_sim_attr_flag.py`. Each case returns (tables, game_ids, game_types, n_seeds, seed0); the dict value
also carries the per_team_types flag the case runs with. The real case uses the LC-2 H3'' hazard and T2 type tables
of results/strength_state_lc2/r5 (the stage-1 incumbent, D18) and the A3g-c attempt table of
results/shot_attempt_r3 (D20), on the first 12 fold-2 games; it is skipped when those gitignored files are absent.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

import t2_parity_cases as T2

LC2 = Path("results/strength_state_lc2/r5")
ATT = Path("results/shot_attempt_r3/att_lam_A3g-c_fold2.npy")
N_REAL = 12


def real_available() -> bool:
    return (LC2 / "lam_H3_fold2.npy").exists() and (LC2 / "types_T2_fold2.npy").exists() and ATT.exists() and \
        Path("results/strength_state_r3/fold2_rows.parquet").exists()


def real_incumbent():
    import pandas as pd
    from nhl_sim.data.load import load_games
    games = np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"])
                    .game_id.unique())[:N_REAL]
    t = dict(lam=np.asarray(np.load(LC2 / "lam_H3_fold2.npy", mmap_mode="r")[:N_REAL]),
             types=np.asarray(np.load(LC2 / "types_T2_fold2.npy", mmap_mode="r")[:N_REAL]),
             coinc_smp=np.array([True, False, True]), coinc_pim=np.array([4, 2, 10], np.int16),
             goal_rate=np.full((3, 3), 2.5), stop_rate_ot=0.02,
             att_lam=np.asarray(np.load(ATT, mmap_mode="r")[:N_REAL]),
             p_goal=np.array([0.055, 0.12, 0.05, 0.07, 0.09]))
    gt = load_games([20242025], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    return t, games, gt.game_type.to_numpy(), 4, 0


CASES = {
    "syn_stub": (lambda: T2.synthetic(False, False), False),
    "syn_attempts": (lambda: T2.synthetic(False, True), False),
    "syn_attempts_t2": (lambda: T2.synthetic(True, True), True),
    "real_incumbent": (real_incumbent, True),
}
