"""Pull the NHL schedule (regular season + playoffs) week by week and write
data/processed/schedule.parquet. Resumable: completed weeks are cached on disk."""
import datetime as dt
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.clients.nhl_api import NHLApiClient  # noqa: E402

SEASONS = [2021, 2022, 2023, 2024, 2025, 2026]  # start year


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/processed/schedule.parquet")
    a = ap.parse_args()
    cl = NHLApiClient()
    today = dt.date.today()
    dates = []
    for y in SEASONS:
        d = dt.date(y, 9, 28)
        end = min(dt.date(y + 1, 7, 10), today + dt.timedelta(days=14))
        while d <= end:
            dates.append(d.isoformat())
            d += dt.timedelta(days=7)
    with ThreadPoolExecutor(4) as ex:
        weeks = list(ex.map(cl.schedule_week, dates))
    rows = {}
    for w in weeks:
        for day in w.get("gameWeek", []):
            for g in day.get("games", []):
                if g["gameType"] not in (2, 3):
                    continue
                rows[g["id"]] = dict(
                    game_id=g["id"], season=g["season"], game_type=g["gameType"], game_date_local=day["date"],
                    start_utc=g["startTimeUTC"], home=g["homeTeam"]["abbrev"], away=g["awayTeam"]["abbrev"],
                    home_id=g["homeTeam"]["id"], away_id=g["awayTeam"]["id"],
                    home_score_sched=g["homeTeam"].get("score"), away_score_sched=g["awayTeam"].get("score"),
                    game_state=g["gameState"], schedule_state=g.get("gameScheduleState"),
                    last_period_type_sched=(g.get("gameOutcome") or {}).get("lastPeriodType"),
                    period_number_sched=(g.get("periodDescriptor") or {}).get("number"),
                    neutral_site=g.get("neutralSite"), venue=(g.get("venue") or {}).get("default"),
                )
    df = pd.DataFrame(rows.values()).sort_values(["start_utc", "game_id"]).reset_index(drop=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out)
    print(f"network={cl.n_network} cached={cl.n_cached} games={len(df)}")
    print(df.groupby(["season", "game_type", "game_state"]).size().to_string())


if __name__ == "__main__":
    main()
