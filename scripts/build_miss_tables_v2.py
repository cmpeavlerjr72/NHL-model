"""SM-R2 tier-level table (docs/models/miss/experiments.md SM-R2): every as-of (level group x danger tier) miss-share
construction -> data/processed/miss/level_tier_v2.parquet (created_at < puck_drop asserted). games/arena/ratings are the SM-R1
tables (unchanged). 2025-26 never read."""
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.miss import data as M  # noqa: E402
from nhl_sim.miss import tier as T  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

SPECS = {"M0": ("M0", None), "M1_K500": ("M1", 500), "M1_K2000": ("M1", 2000), "M1_K8000": ("M1", 8000),
         "M2_H30": ("M2", (30, 2000)), "M2_H60": ("M2", (60, 2000)), "O": ("O", None)}

if __name__ == "__main__":
    a = M.load_rows()
    games = pd.read_parquet(M.OUT / "games_v1.parquet")
    print(time.strftime("%H:%M:%S"), "rows", len(a), "games", len(games), flush=True)
    meta, S = T.asof_levels(a, games, SPECS)
    parts = []
    for n in SPECS:
        f = T.level_frame(meta, S[n])
        f.insert(1, "construction", n)
        parts.append(f)
    L = pd.concat(parts, ignore_index=True)
    assert_pregame(L.dropna(subset=["created_at"]))
    L.to_parquet(M.OUT / "level_tier_v2.parquet", index=False)
    print(time.strftime("%H:%M:%S"), "done", L.shape, flush=True)
