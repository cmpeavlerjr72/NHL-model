"""Pull pbp + boxscore + shift chart per final game id. Resumable (cache hits are free).

usage: pull_games.py [--seasons 20232024 20242025 ...] [--max-seconds N] [--max-games N]
"""
import argparse
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.clients.nhl_api import NHLApiClient  # noqa: E402

DEFAULT_ORDER = [20232024, 20242025, 20262027, 20252026, 20222023, 20212022]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", type=int, default=DEFAULT_ORDER)
    ap.add_argument("--max-seconds", type=float, default=None)
    ap.add_argument("--max-games", type=int, default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--schedule", default="data/processed/schedule.parquet")
    a = ap.parse_args()
    sch = pd.read_csv if False else pd.read_parquet(a.schedule)
    sch = sch[sch.game_state.isin(["OFF", "FINAL"])]
    ids = []
    for s in a.seasons:
        ids += sch[sch.season == s].sort_values(["start_utc", "game_id"]).game_id.tolist()
    if a.max_games:
        ids = ids[: a.max_games]
    cl = NHLApiClient()
    log = open(f"logs/pull_games_{time.strftime('%Y%m%d_%H%M%S')}.log", "a", buffering=1)
    t0 = time.time()
    stop = threading.Event()
    done = [0]
    fails = []

    def one(gid):
        if stop.is_set():
            return gid, "skipped"
        try:
            cl.pbp(gid); cl.boxscore(gid); cl.shifts(gid)
            return gid, "ok"
        except Exception as e:  # noqa: BLE001
            return gid, f"FAIL {e}"

    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(one, g) for g in ids]
        for f in as_completed(futs):
            gid, st = f.result()
            if st.startswith("FAIL"):
                fails.append((gid, st))
                print(gid, st, file=log)
            if st != "skipped":
                done[0] += 1
            if done[0] % 100 == 0 and st != "skipped":
                el = time.time() - t0
                print(f"{time.strftime('%H:%M:%S')} done={done[0]}/{len(ids)} elapsed={el:.0f}s "
                      f"rate={done[0]/el:.2f} games/s net={cl.n_network} cached={cl.n_cached}", file=log)
            if a.max_seconds and time.time() - t0 > a.max_seconds:
                stop.set()
    el = time.time() - t0
    msg = (f"{time.strftime('%H:%M:%S')} END done={done[0]}/{len(ids)} elapsed={el:.0f}s "
           f"rate={done[0]/max(el,1e-9):.2f} games/s net={cl.n_network} cached={cl.n_cached} fails={len(fails)}")
    print(msg, file=log)
    print(msg)
    for g, s in fails[:20]:
        print(g, s)


if __name__ == "__main__":
    main()
