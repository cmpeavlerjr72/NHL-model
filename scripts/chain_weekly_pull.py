"""Weekly resumable NHL pull (INV-16). Refreshes the schedule into a versioned sibling
(data/processed/schedule_weekly.parquet; the shared schedule.parquet is never rewritten),
then runs the cache-first game pull for every final game, which re-tries empty shift charts.
Appends to logs/weekly_pull_<YYYY-MM-DD>.log. Exit code non-zero if any step failed."""
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parents[1]
py = sys.executable
sched = "data/processed/schedule_weekly.parquet"
logp = root / "logs" / f"weekly_pull_{time.strftime('%Y-%m-%d')}.log"
logp.parent.mkdir(exist_ok=True)
rc = 0
with open(logp, "a", buffering=1, encoding="utf-8") as log:
    for name, cmd in [("schedule", [py, "scripts/pull_schedule.py", "--out", sched]),
                      ("games", [py, "scripts/pull_games.py", "--schedule", sched])]:
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} START {name}\n")
        r = subprocess.run(cmd, cwd=root, stdout=log, stderr=subprocess.STDOUT, text=True)
        log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} END {name} rc={r.returncode}\n")
        rc = rc or r.returncode
        if r.returncode:
            break
sys.exit(rc)
