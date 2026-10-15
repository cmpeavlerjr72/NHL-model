"""DRatings 2024-25 sample: walk index pages (3 s spacing), pick games spread across months, cache raw html.
Usage: pull_dratings_sample.py [per_page=11] [stop_hhmm_epoch_seconds_budget]"""
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from nhl_sim.dratings import parse_index

RAW = Path("data/raw/dratings")
BASE = "https://www.dratings.com/predictor/nhl-hockey-predictions/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
PAGES = [106, 118, 130, 142, 154, 166, 178]  # ~12 pages (~3-5 weeks) apart: 2025-04-05 back to ~Oct 2024 (dates printed at run time)
_last = [0.0]
_lock = threading.Lock()


def get(url, tries=4):
    for k in range(tries):
        with _lock:  # global spacing: request starts >= 3 s apart (server latency ~7 s, so up to 3 in flight)
            w = _last[0] + 3.0 - time.time()
            if w > 0:
                time.sleep(w)
            _last[0] = time.time()
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
            r.encoding = "utf-8"
            if r.status_code == 200:
                return r.text
        except requests.RequestException:
            pass
        time.sleep(2 ** k)
    return None


def cached(path, url):
    if path.exists():
        return path.read_text(encoding="utf-8")
    h = get(url)
    if h:
        path.write_text(h, encoding="utf-8")
    return h


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 11
    budget = float(sys.argv[2]) if len(sys.argv) > 2 else 1e9
    t0 = time.time()
    RAW.mkdir(parents=True, exist_ok=True)
    n = 0
    todo = []
    for pg in PAGES:
        if time.time() - t0 > budget:
            print("budget reached"); break
        h = cached(RAW / f"index_{pg}.html", f"{BASE}completed/{pg}")
        rows = parse_index(h or "")
        print(pg, len(rows), rows[0]["start_utc"] if rows else None, rows[-1]["start_utc"] if rows else None, flush=True)
        todo.extend(rows[:per])
    def one(r):
        if time.time() - t0 > budget:
            return 0
        new = not (RAW / f"game_{r['uuid']}.html").exists()
        cached(RAW / f"game_{r['uuid']}.html", BASE + r["uuid"])
        return int(new)
    with ThreadPoolExecutor(3) as ex:
        n = sum(ex.map(one, todo))
    print("new game pages", n, f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
