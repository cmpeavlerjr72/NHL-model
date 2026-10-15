"""Parse cached ESPN core /odds JSON into long rows: game x provider x market (ml / pl / total).

Pregame-only (L18): items whose provider is "Live Odds" (id 59, "ESPN Bet - Live Odds") are dropped.
Ambiguity fails the build: duplicate non-live provider id within a game, or an unrecognised live-looking name.
"close_*" is filled only from an explicit `close` object; `current` is never promoted to close.
"""
from __future__ import annotations

import json
from pathlib import Path

LIVE_IDS = {"59"}  # verified: "ESPN Bet - Live Odds" (in-game prices, e.g. BUF -3000)


class AmbiguousProviders(Exception):
    pass


def is_live(prov: dict) -> bool:
    name = (prov.get("name") or "").lower()
    return str(prov.get("id")) in LIVE_IDS or "live" in name or "in-play" in name or "inplay" in name


def num(x):
    """American odds / line string -> float; None if missing."""
    if x is None:
        return None
    s = str(x).strip().upper()
    if s in ("", "N/A", "NONE"):
        return None
    if s in ("EVEN", "EV", "PK"):
        return 100.0 if s != "PK" else 0.0
    try:
        return float(s.replace("+", ""))
    except ValueError:
        return None


def _g(d, *path):
    for p in path:
        if not isinstance(d, dict):
            return None
        d = d.get(p)
    return d


def implied(american):
    if american is None:
        return None
    return 100 / (american + 100) if american > 0 else -american / (-american + 100)


def parse_event(raw: dict, game_id: int, season: int) -> tuple[list[dict], dict]:
    """Return (rows, info). info: n_items, n_live_dropped, live_names."""
    items = raw.get("items") or []
    live = [i for i in items if is_live(i.get("provider", {}))]
    pre = [i for i in items if not is_live(i.get("provider", {}))]
    ids = [str(i["provider"]["id"]) for i in pre]
    if len(ids) != len(set(ids)):
        raise AmbiguousProviders(f"game {game_id}: duplicate pregame provider ids {ids}")
    rows = []
    for it in pre:
        prov = it["provider"]["name"]
        base = {"game_id": game_id, "season": season, "provider": prov, "provider_id": str(it["provider"]["id"])}
        for side, key in (("away", "awayTeamOdds"), ("home", "homeTeamOdds")):
            t = it.get(key) or {}
            o, c = t.get("open") or {}, t.get("close") or {}
            rows.append({**base, "market": "ml", "side_or_line": side,
                         "open_price": num(_g(o, "moneyLine", "american")), "close_price": num(_g(c, "moneyLine", "american")),
                         "open_line": None, "close_line": None})
            rows.append({**base, "market": "pl", "side_or_line": side,
                         "open_price": num(_g(o, "spread", "american")), "close_price": num(_g(c, "spread", "american")),
                         "open_line": num(_g(o, "pointSpread", "american")), "close_line": num(_g(c, "pointSpread", "american"))})
        o, c = it.get("open") or {}, it.get("close") or {}
        for side in ("over", "under"):
            rows.append({**base, "market": "total", "side_or_line": side,
                         "open_price": num(_g(o, side, "american")), "close_price": num(_g(c, side, "american")),
                         "open_line": num(_g(o, "total", "american")), "close_line": num(_g(c, "total", "american"))})
    return rows, {"n_items": len(items), "n_live_dropped": len(live), "live_names": [i["provider"]["name"] for i in live]}


def vig_outliers(df, lo=1.00, hi=1.10):
    """Close ML implied-prob sum per game x provider; return rows outside [lo, hi] (and the full series)."""
    ml = df[(df.market == "ml") & df.close_price.notna()].copy()
    ml["imp"] = ml.close_price.map(implied)
    s = ml.pivot_table(index=["game_id", "provider"], columns="side_or_line", values="imp")
    s = s.dropna(subset=["away", "home"])
    s["vig_sum"] = s.away + s.home
    return s[(s.vig_sum < lo) | (s.vig_sum > hi)].reset_index(), s.reset_index()
