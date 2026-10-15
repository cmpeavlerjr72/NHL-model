"""DraftKings Predictions (DKeX) NHL board: anonymous board GETs only (no login, no orders).
Header recipe and percent-encoded query follow the CFB puller (Lane B probe laneB_dk_nhl.py)."""
from __future__ import annotations

import time
from urllib.parse import quote

import requests

from .common import http_get_json

URL = "https://sportsbook-nash.draftkings.com/sites/PREDICT/api/sportscontent/controldata/home/leagueSubcategory/v1/markets"
LEAGUE = "42133"
SUBCATS = {"4525": "ml_pl_total", "13192": "alt_total", "16715": "team_goals_period", "16716": "team_total",
           "14495": "goalscorer", "16544": "sog", "16545": "points", "16546": "assists", "16547": "goals",
           "16549": "goalie_saves", "16550": "goalie_saves_ou"}
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
    "accept": "application/json", "origin": "https://predictions.draftkings.com",
    "referer": "https://predictions.draftkings.com/", "accept-encoding": "identity",
    "x-pe-cn": "predict-web", "x-pe-cv": "1.12.0", "x-pe-ep": "PR", "x-pe-loc": "US-GA",
}


def _url(sub: str, top: int = 100) -> str:
    p = {"isBatchable": "false",
         "eventsQuery": f"$filter=leagueId eq '{LEAGUE}' AND clientMetadata/Subcategories/any(s: s/Id eq '{sub}')",
         "marketsQuery": f"$filter=clientMetadata/subCategoryId eq '{sub}' AND tags/all(t: t ne 'SportcastBetBuilder')",
         "include": "Events", "entity": "events", "top": str(top)}
    return URL + "?" + "&".join(k + "=" + quote(v) for k, v in p.items())


def fetch() -> dict:
    sess = requests.Session()
    out, errs = {}, []
    for sub in SUBCATS:
        time.sleep(0.5)
        try:
            j = http_get_json(_url(sub), headers=HEADERS, session=sess)
        except Exception as e:  # noqa: BLE001 - one subcategory failing must not lose the rest
            errs.append(f"{sub}:{e}")
            continue
        out[sub] = {k: j.get(k, []) for k in ("events", "markets", "selections")}
    if not out:
        raise RuntimeError("all DKeX subcategories failed: " + "; ".join(errs)[:300])
    return {"subcategories": out, "errors": errs}


def _norm_american(s):
    return s.replace("−", "-") if s else s


def normalise(payload: dict, fetched_at: str) -> list[dict]:
    rows, seen = [], set()
    for sub, d in payload["subcategories"].items():
        ev = {e["id"]: e for e in d["events"]}
        mk = {m["id"]: m for m in d["markets"]}
        for s in d["selections"]:
            m = mk.get(s.get("marketId"))
            if not m or s["id"] in seen:
                continue
            seen.add(s["id"])
            e = ev.get(m.get("eventId"), {})
            parts = s.get("participants") or []
            disp = s.get("displayOdds") or {}
            rows.append({
                "subcategory": sub, "event_id": m.get("eventId"), "event": e.get("name"),
                "event_start": e.get("startEventDate"), "market_id": m["id"], "market": m.get("name"),
                "market_type": (m.get("marketType") or {}).get("name"),
                "selection_id": s["id"], "selection": s.get("label"),
                "outcome_type": s.get("outcomeType"),
                "participant": parts[0].get("name") if parts else None,
                "line": s.get("points", s.get("milestoneValue")),
                "price_american": _norm_american(disp.get("american")),
                "price_decimal": s.get("trueOdds"), "implied_pct": disp.get("percentage"),
                "fetched_at": fetched_at,
            })
    return rows
