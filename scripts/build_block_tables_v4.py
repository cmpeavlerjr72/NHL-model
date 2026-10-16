"""SB-R4 tables: Rr / Ra as-of block ratings (b 1000, w 0.7) -> data/processed/block/ratings_r4_{Rr,Ra}.parquet.
created_at < puck_drop asserted inside data.asof_block_ratings (assert_pregame) and again here."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd  # noqa: E402
from nhl_sim.block import data as D  # noqa: E402
from nhl_sim.block import data_v4 as D4  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

if __name__ == "__main__":
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "start", flush=True)
    a = D.load_attempts()
    games = pd.read_parquet(D.OUT / "games_v1.parquet")
    af = pd.read_parquet(D.OUT / "arena_v1.parquet")
    for mode in ("Rr", "Ra"):
        rt = D4.build_ratings_variant(a, games, af, mode)
        assert_pregame(rt)
        rt.to_parquet(D.OUT / f"ratings_r4_{mode}.parquet", index=False)
        print(time.strftime("%Y-%m-%d %H:%M:%S"), mode, rt.shape, flush=True)
