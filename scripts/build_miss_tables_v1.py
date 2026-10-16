"""SM-R1 tables (docs/models/miss/experiments.md SM-R1): games, every as-of miss-share level construction, the as-of arena
miss-recording factor and the road-only as-of miss ratings -> data/processed/miss/{games,level,arena,ratings}_v1.parquet.
created_at < puck_drop asserted on every row (assert_pregame). 2025-26 never read.

    build_miss_tables_v1.py levels    games + levels (step 1)
    build_miss_tables_v1.py ratings   arena factor + road-only ratings (step 2)
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.miss import data as M  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

SPECS = {"M0": ("M0", None), "M1_K500": ("M1", 500), "M1_K2000": ("M1", 2000), "M1_K8000": ("M1", 8000),
         "M2_H30": ("M2", (30, 2000)), "M2_H60": ("M2", (60, 2000)), "O": ("O", None)}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    cmd = sys.argv[1]
    M.OUT.mkdir(parents=True, exist_ok=True)
    a = M.load_rows()
    games = M.game_table()
    print(now(), "unblocked rows", len(a), "games", len(games), flush=True)
    if cmd == "levels":
        games.to_parquet(M.OUT / "games_v1.parquet", index=False)
        meta, S = M.asof_levels(a, games, SPECS)
        parts = []
        for n in SPECS:
            f = M.level_frame(meta, S[n])
            f.insert(1, "construction", n)
            parts.append(f)
        L = pd.concat(parts, ignore_index=True)
        assert_pregame(L.dropna(subset=["created_at"]))
        L.to_parquet(M.OUT / "level_v1.parquet", index=False)
        print(now(), "levels done", L.shape, flush=True)
    else:
        af = M.build_arena(a, games)
        af.to_parquet(M.OUT / "arena_v1.parquet", index=False)
        print(now(), "arena done", af.arena_f.describe().round(4).to_dict(), flush=True)
        rt = M.build_ratings_road(a, games)
        assert_pregame(rt)
        rt.to_parquet(M.OUT / "ratings_v1.parquet", index=False)
        k = f"w{M.W_}_b{M.B_}"
        print(now(), "ratings done", rt.shape, f"SD rf_es {rt[f'rf_es_{k}'].std():.4f} rf_pp {rt[f'rf_pp_{k}'].std():.4f} "
              f"rf_pk {rt[f'rf_pk_{k}'].std():.4f}", flush=True)
