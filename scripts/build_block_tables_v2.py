"""SB-R2 tables: as-of block ratings on the extended grid b in {1000, 3000, 10000, 30000} x w in {0.5, 0.7, 0.85}
-> data/processed/block/ratings_v2.parquet (v1 untouched). created_at < puck_drop asserted (data.assert_pregame)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.block import data as D  # noqa: E402

D.GRID_W = (0.5, 0.7, 0.85)
D.GRID_B = (1000, 3000, 10000, 30000)

if __name__ == "__main__":
    t = time.strftime("%Y-%m-%d %H:%M:%S")
    print(t, "start", flush=True)
    a = D.load_attempts()
    games = D.game_table()
    rt = D.build_ratings(a, games)
    rt.to_parquet(D.OUT / "ratings_v2.parquet", index=False)
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "ratings_v2", rt.shape, flush=True)
