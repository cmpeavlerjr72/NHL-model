"""ESPN core API `/odds` client + ESPN-event-id -> NHL game_id mapping.

Read-only, polite: generic User-Agent, max 4 concurrent requests, exponential backoff, raw JSON cached to
data/raw/espn_core_odds/<event_id>.json (never re-fetched).
"""
from __future__ import annotations

import gzip
import json
import threading
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "data" / "raw" / "espn_core_odds"
SCOREBOARD = ROOT / "data" / "raw" / "espn_scoreboard"
BASE = "https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
ABBR = {"TB": "TBL", "NJ": "NJD", "SJ": "SJS", "LA": "LAK", "UTAH": "UTA"}
MAX_CONCURRENT = 4
_sem = threading.Semaphore(MAX_CONCURRENT)


def url(eid) -> str:
    return f"{BASE}/events/{eid}/competitions/{eid}/odds"


def fetch(eid, tries: int = 5, min_gap: float = 0.4) -> str:
    """Fetch and cache one event's odds. Returns 'cached' | 'ok' | 'fail'."""
    p = RAW / f"{eid}.json"
    if p.exists():
        return "cached"
    for k in range(tries):
        try:
            with _sem:
                r = requests.get(url(eid), headers={"User-Agent": UA}, timeout=30)
                time.sleep(min_gap)
            if r.status_code == 200:
                r.json()
                tmp = p.with_suffix(".tmp")
                tmp.write_bytes(r.content)
                tmp.replace(p)
                return "ok"
            if r.status_code == 404:  # event has no odds resource: cache an empty marker
                p.write_text('{"items": [], "_status": 404}', encoding="utf-8")
                return "ok"
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** k)
    return "fail"


def event_map(seasons=(20232024, 20242025)) -> pd.DataFrame:
    """ESPN event id -> NHL game_id via scoreboard cache (date + home/away), regular season + playoffs."""
    g = pd.read_parquet(ROOT / "data" / "processed" / "games.parquet")
    g = g[g.season.isin(seasons) & g.game_type.isin([2, 3])]
    key = {(r.game_date_local, r.home, r.away): r for r in g.itertuples()}
    rows = []
    for f in sorted(SCOREBOARD.glob("*.json.gz")):
        d = f.name[:8]
        iso = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        for e in json.load(gzip.open(f)).get("events", []):
            comp = e["competitions"][0]["competitors"]
            h = next(c for c in comp if c["homeAway"] == "home")["team"]["abbreviation"]
            a = next(c for c in comp if c["homeAway"] == "away")["team"]["abbreviation"]
            h, a = ABBR.get(h, h), ABBR.get(a, a)
            r = key.get((iso, h, a))
            if r is None:  # ESPN date can differ from local date by a day
                for dd in (-1, 1):
                    iso2 = (pd.Timestamp(iso) + pd.Timedelta(days=dd)).strftime("%Y-%m-%d")
                    r = key.get((iso2, h, a))
                    if r is not None:
                        break
            if r is not None:
                rows.append({"event_id": str(e["id"]), "game_id": int(r.game_id), "season": int(r.season),
                             "game_type": int(r.game_type), "game_date": r.game_date_local})
    m = pd.DataFrame(rows).drop_duplicates("event_id")
    return m.drop_duplicates("game_id")
