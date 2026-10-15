"""Pull ESPN core /odds for NHL games into data/raw/espn_core_odds/ (resumable, 4 threads).
Order: 2024-25 regular season, 2024-25 playoffs, 2023-24 (regular then playoffs). 2025-26 is sealed: never pulled.
Usage: pull_lines_espn_core.py [max_seconds] [limit_games]"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

from nhl_sim.clients import espn_core_odds as C


def main():
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 1e9
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    C.RAW.mkdir(parents=True, exist_ok=True)
    m = C.event_map()
    m["order"] = m.apply(lambda r: (0 if r.season == 20242025 else 1, r.game_type, r.game_date), axis=1)
    m = m.sort_values("order")
    assert not (m.season == 20252026).any()
    todo = [e for e in m.event_id if not (C.RAW / f"{e}.json").exists()]
    if limit:
        todo = todo[:limit]
    print(f"{len(m)} mapped games, {len(todo)} todo", flush=True)
    t0 = time.time()
    cnt = Counter()
    with ThreadPoolExecutor(C.MAX_CONCURRENT) as ex:
        for i, res in enumerate(ex.map(lambda e: C.fetch(e) if time.time() - t0 < budget else "skipped", todo)):
            cnt[res] += 1
            if i % 200 == 0:
                print(i, dict(cnt), f"{time.time()-t0:.0f}s", flush=True)
    print(dict(cnt), f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
