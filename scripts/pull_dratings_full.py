"""Full DRatings NHL pull, 2021-22 .. 2024-25 (resumable, politely paced, cache-first).
Phase A: walk completed-game index pages (cache index_full_<page>.html) from the 2025-06 boundary back to 2021-09.
Phase B: fetch game pages (cache game_<uuid>.html), SBRO-overlap games (2021-22, 2022-23 to 2022-11-27) first.
Phase C: build data/processed/lines_dratings_v1.parquet (scripts/build_lines_dratings.py).
2025-26 (sealed) and 2026-27 game pages are NEVER fetched: only index rows dated < 2025-07-01 are kept.
Never re-fetches a cached file. Global spacing 3 s between request starts, <= 3 in flight. Log: results/logs/dratings_pull_<date>.log
Usage: python scripts/pull_dratings_full.py [--task NHL-Model-dratings-pull] [--max-hours 9]
When launched by the scheduled task, unregisters the task on exit."""
import argparse
import datetime as dt
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import build_lines_dratings as B  # noqa: E402
from nhl_sim.dratings import parse_index  # noqa: E402

RAW = B.RAW
BASE = "https://www.dratings.com/predictor/nhl-hockey-predictions/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NHL-Model-research (personal, 3s spacing)"
_last = [0.0]
_lock = threading.Lock()
LOG = ROOT / "results" / "logs" / f"dratings_pull_{dt.date.today().isoformat()}.log"
T0 = time.time()
DEADLINE = [1e18]


def log(*a):
    s = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] " + " ".join(str(x) for x in a)
    print(s, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def get(url, tries=5):
    for k in range(tries):
        with _lock:
            w = _last[0] + 3.0 - time.time()
            if w > 0:
                time.sleep(w)
            _last[0] = time.time()
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=45)
            if r.status_code == 200:
                r.encoding = "utf-8"  # server says ISO-8859-1 but sends utf-8
                return r.text
            log("HTTP", r.status_code, url)
            if r.status_code == 404:
                return None
        except requests.RequestException as e:
            log("ERR", type(e).__name__, url)
        time.sleep(min(60, 2 ** (k + 1)))
    return None


def fetch_cached(path, url):
    if path.exists() and path.stat().st_size > 5000:
        return path.read_text(encoding="utf-8"), False
    h = get(url)
    if h:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(h, encoding="utf-8")
        tmp.replace(path)
    return h, True


def phase_a():
    """Walk index pages. Page numbers grow with age. Find the boundary page (first with a row >= WIN_HI) going down from 95."""
    n_new = 0

    def page(p):
        nonlocal n_new
        h, new = fetch_cached(RAW / f"index_full_{p}.html", f"{BASE}completed/{p}")
        n_new += new
        return parse_index(h or "")

    p = 95
    while p > 1:
        rows = page(p)
        if not rows:
            raise SystemExit(f"empty index page {p}")
        if max(r["start_utc"][:10] for r in rows) >= B.WIN_HI:
            break
        p -= 1
    log("boundary page", p, "newest", max(r["start_utc"] for r in rows))
    p2 = p + 1
    while True:
        rows = page(p2)
        if not rows:
            log("empty index page", p2, "stop"); break
        newest = max(r["start_utc"][:10] for r in rows)
        if p2 % 20 == 0:
            log("index page", p2, newest, f"new={n_new}")
        if newest < B.WIN_LO:
            break
        p2 += 1
        if time.time() > DEADLINE[0]:
            log("deadline in phase A"); break
    log("phase A done; last page", p2, "new index fetches", n_new)


def phase_b():
    idx = B.index_rows()
    gid, g = B.match_games(idx)
    sb = pd.read_parquet(ROOT / "data" / "processed" / "lines_sbro_v1.parquet", columns=["game_id"]) if (ROOT / "data/processed/lines_sbro_v1.parquet").exists() else pd.DataFrame({"game_id": []})
    sbro = set(sb.game_id)
    order = sorted(gid, key=lambda u: (0 if gid[u] in sbro else 1, idx[u]["start_utc"]))
    # SBRO overlap first (chronological), then the rest newest season first
    first = [u for u in order if gid[u] in sbro]
    rest = sorted([u for u in order if gid[u] not in sbro], key=lambda u: idx[u]["start_utc"], reverse=True)
    todo = [u for u in first + rest if not (RAW / f"game_{u}.html").exists()]
    log(f"phase B: {len(idx)} index rows in window, {len(gid)} matched to NHL games, {len(todo)} to fetch ({len(first)} SBRO-overlap)")
    unmatched = [u for u in idx if u not in gid]
    if unmatched:
        log("index rows with no NHL game match:", len(unmatched))
    cnt = {"ok": 0, "fail": 0, "skip": 0}

    def one(u):
        if time.time() > DEADLINE[0]:
            cnt["skip"] += 1; return
        h, _ = fetch_cached(RAW / f"game_{u}.html", BASE + u)
        cnt["ok" if h else "fail"] += 1
        n = cnt["ok"] + cnt["fail"]
        if n % 100 == 0:
            el = time.time() - T0
            log(f"progress {n}/{len(todo)} ok={cnt['ok']} fail={cnt['fail']} elapsed={el/60:.0f}m eta={(len(todo)-n)*el/max(n,1)/60:.0f}m (est)")

    with ThreadPoolExecutor(3) as ex:
        list(ex.map(one, todo))
    log("phase B done", cnt)
    missing = [u for u in gid if not (RAW / f"game_{u}.html").exists()]
    log("games still without a page:", len(missing))
    return len(missing)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=None)
    ap.add_argument("--max-hours", type=float, default=9.0)
    ap.add_argument("--skip-a", action="store_true")
    a = ap.parse_args()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    DEADLINE[0] = T0 + a.max_hours * 3600
    log("start; pid", __import__("os").getpid())
    try:
        if not a.skip_a:
            phase_a()
        for _ in range(3):  # a retry pass picks up transient failures
            if phase_b() == 0:
                break
        log("phase C: build")
        B.main()
        log("done")
    except BaseException as e:  # noqa: BLE001
        log("FATAL", type(e).__name__, str(e)[:300])
        raise
    finally:
        if a.task:
            subprocess.run(["schtasks", "/Delete", "/TN", a.task, "/F"], capture_output=True)
            log("task unregistered:", a.task)


if __name__ == "__main__":
    main()
