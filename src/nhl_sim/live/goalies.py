"""Daily Faceoff starting goalies: one page fetch per run, parse __NEXT_DATA__."""
from __future__ import annotations

import json
import re
import time

import requests

from .common import UA

URL = "https://www.dailyfaceoff.com/starting-goalies"
_RX = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def parse_html(html: str) -> dict:
    m = _RX.search(html)
    if not m:
        raise RuntimeError("__NEXT_DATA__ not found")
    pp = json.loads(m.group(1))["props"]["pageProps"]
    # keep only the game rows + date (drop articles/boilerplate)
    return {"date": pp.get("date"), "data": pp["data"]}


def fetch() -> dict:
    last = None
    for i in range(4):
        try:
            r = requests.get(URL, headers={"User-Agent": UA}, timeout=30)
            if r.status_code == 200:
                return parse_html(r.text)
            last = RuntimeError(f"HTTP {r.status_code}")
        except (requests.RequestException, ValueError, KeyError, RuntimeError) as e:
            last = e
        time.sleep(2 ** i)
    raise RuntimeError(f"daily faceoff fetch failed: {last}")


def normalise(payload: dict, fetched_at: str) -> list[dict]:
    rows = []
    for g in payload["data"]:
        for side in ("home", "away"):
            other = "away" if side == "home" else "home"
            rows.append({
                "game_date": g.get("date") or payload.get("date"),
                "game_start_utc": g.get("dateGmt"),
                "side": side,
                "team": g.get(f"{side}TeamName"),
                "opponent": g.get(f"{other}TeamName"),
                "goalie_id": g.get(f"{side}GoalieId"),
                "goalie_name": g.get(f"{side}GoalieName"),
                "status": g.get(f"{side}NewsStrengthName"),
                "source_ts": g.get(f"{side}NewsCreatedAt"),
                "source_name": g.get(f"{side}NewsSourceName"),
                "fetched_at": fetched_at,
            })
    return rows
