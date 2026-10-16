"""SB-R1 tables (docs/models/block/experiments.md SB-R1): as-of ratings (all grid cells), arena block factor, and
every league block-share level construction -> data/processed/block/{ratings,arena,level}_v1.parquet.
created_at < puck_drop asserted on every row (data.assert_pregame). 2025-26 never read.
"""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.block import data as D  # noqa: E402

SPECS = {"M0": ("M0", None), "M1_K500": ("M1", 500), "M1_K2000": ("M1", 2000), "M1_K8000": ("M1", 8000),
         "M2_H30": ("M2", (30, 2000)), "M2_H60": ("M2", (60, 2000)), "O": ("O", None)}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    D.OUT.mkdir(parents=True, exist_ok=True)
    a = D.load_attempts()
    games = D.game_table()
    print(now(), "attempts", len(a), "games", len(games), flush=True)
    meta, S = D.asof_levels(a, games, SPECS)
    parts = []
    for n in SPECS:
        f = D.level_frame(meta, S[n])
        f.insert(1, "construction", n)
        parts.append(f)
    pd.concat(parts, ignore_index=True).to_parquet(D.OUT / "level_v1.parquet", index=False)
    print(now(), "levels done", flush=True)
    af = D.build_arena(a, games)
    af.to_parquet(D.OUT / "arena_v1.parquet", index=False)
    print(now(), "arena done", af.arena_f.describe().round(4).to_dict(), flush=True)
    rt = D.build_ratings(a, games)
    rt.to_parquet(D.OUT / "ratings_v1.parquet", index=False)
    k = D.wkey(0.85, 1000)
    print(now(), "ratings done", len(rt), f"SD rf_es {rt[f'rf_es_{k}'].std():.4f} ra_es {rt[f'ra_es_{k}'].std():.4f}", flush=True)
    games.to_parquet(D.OUT / "games_v1.parquet", index=False)
