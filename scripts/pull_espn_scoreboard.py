"""Pull the ESPN NHL scoreboard by date into data/raw/espn_scoreboard/ (gzip raw JSON, resumable, 4 threads).
Usage: pull_espn_scoreboard.py [start YYYYMMDD] [end YYYYMMDD] [max_seconds]"""
import gzip
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import requests

OUT = Path("data/raw/espn_scoreboard")
URL = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard"
# ESPN returns 403 for a descriptive custom User-Agent; a generic browser string is accepted.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def fetch(d: str, tries: int = 5):
    p = OUT / f"{d}.json.gz"
    if p.exists():
        return "cached"
    for k in range(tries):
        try:
            r = requests.get(URL, params={"dates": d, "limit": 300}, headers={"User-Agent": UA}, timeout=30)
            if r.status_code == 200:
                r.json()  # validate
                tmp = p.with_suffix(".tmp")
                tmp.write_bytes(gzip.compress(r.content))
                tmp.replace(p)
                return "ok"
        except Exception:
            pass
        time.sleep(2 ** k)
    return "fail"


def main():
    a = sys.argv[1] if len(sys.argv) > 1 else "20211001"
    b = sys.argv[2] if len(sys.argv) > 2 else "20261014"
    budget = float(sys.argv[3]) if len(sys.argv) > 3 else 1e9
    s, e = (date(int(x[:4]), int(x[4:6]), int(x[6:])) for x in (a, b))
    days = [(s + timedelta(i)).strftime("%Y%m%d") for i in range((e - s).days + 1)]
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    counts = {}
    todo = [d for d in days if not (OUT / f"{d}.json.gz").exists()]
    with ThreadPoolExecutor(4) as ex:
        for res in ex.map(lambda d: fetch(d) if time.time() - t0 < budget else "skipped", todo):
            counts[res] = counts.get(res, 0) + 1
    print(f"{len(days)} days, {len(todo)} todo, {counts}, {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
