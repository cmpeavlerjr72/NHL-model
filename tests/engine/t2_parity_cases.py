"""SA-R3 T2 engine merge: parity cases shared by the fixture generator (`scripts/diag_engine_t2_parity_fixture.py`)
and `tests/engine/test_sim_t2_merge.py`.

Each case returns (tables, game_ids, game_types, n_seeds, seed0). Synthetic cases are random but fixed (numpy
default_rng with a fixed seed), with heterogeneous hazards, per-game per-team type tables and attempt rates so every
engine branch fires. The real case uses the H3'' hazard table and the T2 per-team type table of
results/strength_state_r5 (gitignored; the case is skipped when absent).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

R5 = Path("results/strength_state_r5")
G_SYN = 6
N_REAL = 16


def _shared_types(rng):
    t = rng.dirichlet([20.0, 1.0, 0.5, 4.0], size=(6, 5, 4))
    return t


def synthetic(per_team: bool, attempts: bool, seed: int = 7):
    rng = np.random.default_rng(seed)
    lam = rng.uniform(0.5, 6.0, size=(G_SYN, 2, 100, 5, 5, 5)).astype(np.float32)
    if per_team:
        types = rng.dirichlet([20.0, 1.0, 0.5, 4.0], size=(G_SYN, 2, 6, 5, 4))
    else:
        types = _shared_types(rng)
    t = dict(lam=lam, types=types, coinc_smp=np.array([True, False, True]),
             coinc_pim=np.array([4, 2, 10], np.int16), goal_rate=rng.uniform(1.0, 8.0, size=(3, 3)),
             stop_rate_ot=0.02)
    if attempts:
        t["att_lam"] = rng.uniform(30.0, 90.0, size=(G_SYN, 2, 100, 5, 7)).astype(np.float32)
        t["p_goal"] = rng.uniform(0.03, 0.15, size=5)
    gids = np.arange(2024020001, 2024020001 + G_SYN, dtype=np.int64)
    gtypes = np.array([2, 2, 2, 2, 3, 3])
    return t, gids, gtypes, 8, 3


def real_available() -> bool:
    return (R5 / "lam_H3_fold2.npy").exists() and (R5 / "types_T2_fold2.npy").exists() and \
        Path("results/strength_state_r3/fold2_rows.parquet").exists()


def real(per_team: bool):
    import pandas as pd
    games = np.sort(pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"])
                    .game_id.unique())
    lam = np.asarray(np.load(R5 / "lam_H3_fold2.npy", mmap_mode="r")[:N_REAL])
    types = np.asarray(np.load(R5 / "types_T2_fold2.npy", mmap_mode="r")[:N_REAL])
    if not per_team:
        types = types[0, 0].copy()          # any valid shared (6, 5, 4, 4) table exercises the flag-off path
    from nhl_sim.data.load import load_games
    gt = load_games([20242025], columns=["game_id", "game_type"]).set_index("game_id").loc[games[:N_REAL]]
    t = dict(lam=lam, types=types, coinc_smp=np.array([True, False, True]), coinc_pim=np.array([4, 2, 10], np.int16),
             goal_rate=np.full((3, 3), 2.5), stop_rate_ot=0.02)
    t["goal_rate"][2, 0] = 9.0
    t["goal_rate"][0, 2] = 0.5
    return t, games[:N_REAL], gt.game_type.to_numpy(), 4, 0


def digest(out: dict) -> dict:
    """sha256 of every output array (dtype, shape and bytes)."""
    d = {}
    for k in sorted(out):
        v = np.asarray(out[k])
        h = hashlib.sha256()
        h.update(str(v.dtype).encode())
        h.update(str(v.shape).encode())
        h.update(np.ascontiguousarray(v).tobytes())
        d[k] = h.hexdigest()
    return d


# flag-off cases recorded against the PRE-merge engine/sim.py (fixture tests/fixtures/sim_t2_merge_parity.json)
OFF_CASES = {"syn_stub": lambda: synthetic(False, False), "syn_attempts": lambda: synthetic(False, True),
             "real_stub": lambda: real(False)}
