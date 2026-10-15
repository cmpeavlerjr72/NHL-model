"""INV-11: ESPN pickcenter line coverage for every regular-season game, 2023-24, 2024-25, 2025-26.

Game list = data/processed/schedule.parquet (regular season, finished games). ESPN event ids come from the
per-date scoreboard (range queries return 400). Raw JSON cached under data/raw/espn/ (never re-fetched).
Read-only, 2 worker threads each spaced >= 1 s (about 2 req/s total).
Outputs: data/processed/espn_lines_coverage.csv (per game x provider) and
docs/tests/espn_lines_coverage_2026-10-15.md (summary written by this script).
"""
import json
import sys
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "espn"
S = "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
H = {"User-Agent": "NHL-Model-research/0.1 (personal read-only research)"}
SEASONS = [20232024, 20242025, 20252026]
ABBR = {"TB": "TBL", "NJ": "NJD", "SJ": "SJS", "LA": "LAK", "UTAH": "UTA", "UTA": "UTA"}
_lock = threading.Lock()
_last = [0.0]
stats = Counter()


def get(url, **q):
    for i in range(4):
        with _lock:  # global spacing: one request start per 0.5 s => ~2 req/s over 2 threads
            wait = _last[0] + 0.5 - time.time()
            if wait > 0:
                time.sleep(wait)
            _last[0] = time.time()
        try:
            r = requests.get(url, params=q, headers=H, timeout=30)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (400, 404):
                return {"_status": r.status_code}
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** i)
    return {"_status": "failed"}


def cached(path: Path, fn):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    j = fn()
    if j.get("_status") != "failed":  # failures are not cached, retried on the next run
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(j), encoding="utf-8")
    stats["fetched"] += 1
    return j


def scoreboard(date: str):
    return cached(RAW / "scoreboard" / f"{date}.json", lambda: get(S + "/scoreboard", dates=date.replace("-", "")))


def summary(eid: str):
    def f():
        j = get(S + "/summary", event=eid)
        if "_status" in j:
            return j
        return {"id": eid, "pickcenter": j.get("pickcenter"), "odds": j.get("odds"),
                "header_comp": (j.get("header", {}).get("competitions") or [{}])[0].get("status")}
    return cached(RAW / "summary" / f"{eid}.json", f)


def has(d, *path):
    for k in path:
        if not isinstance(d, dict):
            return False
        d = d.get(k)
    return d is not None


def provider_flags(p):
    ml_o = has(p, "moneyline", "home", "open", "odds") or has(p, "moneyline", "away", "open", "odds")
    ml_c = has(p, "moneyline", "home", "close", "odds") or has(p, "moneyline", "away", "close", "odds")
    pl_o = has(p, "pointSpread", "home", "open", "line") or has(p, "pointSpread", "away", "open", "line")
    pl_c = has(p, "pointSpread", "home", "close", "line") or has(p, "pointSpread", "away", "close", "line")
    to_o = has(p, "total", "over", "open", "line")
    to_c = has(p, "total", "over", "close", "line")
    ml = ml_o or ml_c or has(p, "homeTeamOdds", "moneyLine") or has(p, "awayTeamOdds", "moneyLine")
    pl = pl_o or pl_c or (p.get("spread") is not None)
    tot = to_o or to_c or (p.get("overUnder") is not None)
    return dict(has_ml=bool(ml), has_pl=bool(pl), has_total=bool(tot),
                has_open=bool(ml_o or pl_o or to_o), has_close=bool(ml_c or pl_c or to_c))


def main():
    sch = pd.read_parquet(ROOT / "data" / "processed" / "schedule.parquet")
    sch = sch[(sch.game_type == 2) & sch.season.isin(SEASONS) & (sch.game_state.isin(["OFF", "FINAL"]))].copy()
    print("games", sch.groupby("season").size().to_dict(), flush=True)
    dates = sorted(sch.game_date_local.unique())
    t0 = time.time()
    with ThreadPoolExecutor(2) as ex:
        sb = dict(zip(dates, ex.map(scoreboard, dates)))
    print(f"scoreboards done {len(dates)} dates, {stats['fetched']} fetched, {time.time()-t0:.0f}s", flush=True)

    ev = {}
    for d, j in sb.items():
        for e in j.get("events", []):
            comp = e["competitions"][0]["competitors"]
            h = next(c for c in comp if c["homeAway"] == "home")["team"]["abbreviation"]
            a = next(c for c in comp if c["homeAway"] == "away")["team"]["abbreviation"]
            ev[(d, ABBR.get(h, h), ABBR.get(a, a))] = e["id"]
    sch["espn_id"] = [ev.get((d, h, a)) for d, h, a in zip(sch.game_date_local, sch.home, sch.away)]
    print("unmatched", int(sch.espn_id.isna().sum()), "of", len(sch), flush=True)
    ids = sorted(sch.espn_id.dropna().unique())
    t1 = time.time()
    with ThreadPoolExecutor(2) as ex:
        sm = dict(zip(ids, ex.map(summary, ids)))
    print(f"summaries done {len(ids)}, {time.time()-t1:.0f}s", flush=True)

    rows = []
    for g in sch.itertuples():
        pcs = (sm.get(g.espn_id) or {}).get("pickcenter") or [] if g.espn_id else []
        if not pcs:
            rows.append(dict(game_id=g.game_id, season=g.season, espn_id=g.espn_id, provider=None))
        for p in pcs:
            rows.append(dict(game_id=g.game_id, season=g.season, espn_id=g.espn_id,
                             provider=p["provider"]["name"], **provider_flags(p)))
    df = pd.DataFrame(rows)
    out = ROOT / "data" / "processed" / "espn_lines_coverage.csv"
    df.to_csv(out, index=False)
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
