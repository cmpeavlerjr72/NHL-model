"""Kalshi NHL markets: anonymous public GETs only (no key, no account endpoints)."""
from __future__ import annotations

import time

import requests

from .common import http_get_json

BASE = "https://api.elections.kalshi.com/trade-api/v2"
FALLBACK_SERIES = ["KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL", "KXNHLTEAMTOTAL", "KXNHL1P", "KXNHL1PTOTAL",
                   "KXNHL1PSPREAD", "KXNHL2P", "KXNHL2PTOTAL", "KXNHL3P", "KXNHL3PTOTAL", "KXNHLGOAL",
                   "KXNHLANYGOAL", "KXNHLPTS", "KXNHLAST", "KXNHLSAVES", "KXNHLSAVE", "KXNHLFIRSTGOAL",
                   "KXNHLOT", "KXNHLOVERTIME", "KXNHLF10G"]
SPACING = 0.3


def _get(sess, path, **q):
    time.sleep(SPACING)
    return http_get_json(BASE + path, params=q, session=sess)


def discover_series(sess) -> list[str]:
    try:
        s = _get(sess, "/series", category="Sports").get("series", [])
        found = {x["ticker"] for x in s if x["ticker"].startswith("KXNHL")}
        return sorted(found | set(FALLBACK_SERIES))
    except Exception:  # noqa: BLE001
        return list(FALLBACK_SERIES)


def fetch() -> dict:
    sess = requests.Session()
    out: dict[str, list] = {}
    for s in discover_series(sess):
        ms, cur = [], ""
        for _ in range(20):  # pagination guard
            q = dict(series_ticker=s, status="open", limit=1000)
            if cur:
                q["cursor"] = cur
            j = _get(sess, "/markets", **q)
            ms += j.get("markets", [])
            cur = j.get("cursor") or ""
            if not cur:
                break
        if ms:
            out[s] = ms
    return {"series": out}


def normalise(payload: dict, fetched_at: str) -> list[dict]:
    rows = []
    for s, ms in payload["series"].items():
        for m in ms:
            rows.append({
                "series": s, "event_ticker": m.get("event_ticker"), "ticker": m.get("ticker"),
                "title": m.get("title"), "yes_sub_title": m.get("yes_sub_title"),
                "strike_type": m.get("strike_type"), "floor_strike": m.get("floor_strike"),
                "cap_strike": m.get("cap_strike"),
                "yes_bid": m.get("yes_bid_dollars"), "yes_ask": m.get("yes_ask_dollars"),
                "no_bid": m.get("no_bid_dollars"), "no_ask": m.get("no_ask_dollars"),
                "last": m.get("last_price_dollars"), "volume": m.get("volume_fp"),
                "volume_24h": m.get("volume_24h_fp"), "open_interest": m.get("open_interest_fp"),
                "open_time": m.get("open_time"), "close_time": m.get("close_time"),
                "expected_expiration_time": m.get("expected_expiration_time"),
                "fetched_at": fetched_at,
            })
    return rows
