"""Build data/processed tables from cached raw NHL API JSON (no network)."""
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.pbp.tables import process_game  # noqa: E402

OUT = Path("data/processed")


def main():
    sch = pd.read_parquet(OUT / "schedule.parquet")
    sch = sch[sch.game_state.isin(["OFF", "FINAL"])].sort_values(["start_utc", "game_id"])
    ids = sch.game_id.tolist()
    t0 = time.time()
    with Pool(4) as pool:
        res = pool.map(process_game, ids, chunksize=25)
    print(f"processed {len(res)} games in {time.time()-t0:.0f}s")
    games = pd.DataFrame([r[0] for r in res])
    games = games.merge(sch[["game_id", "home_score_sched", "away_score_sched", "last_period_type_sched",
                             "game_state", "neutral_site", "venue"]], on="game_id", how="left")
    games.to_parquet(OUT / "games.parquet")
    for name, i in (("events", 1), ("shifts", 2), ("player_box", 3), ("goalie_box", 4)):
        df = pd.DataFrame([row for r in res for row in r[i]])
        for season, g in df.groupby("season"):
            d = OUT / name
            d.mkdir(exist_ok=True)
            g.reset_index(drop=True).to_parquet(d / f"{name}_{season}.parquet")
        print(name, len(df))
        del df


if __name__ == "__main__":
    main()
