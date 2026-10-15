"""DRatings NHL game-page cell parser (completed games).

Page layout per market section (ids scroll-money / scroll-spread / scroll-ou): two tables (offshore, vegas), each
header `[blank | Open Line | book1..book5 | Best Line | No-Vig Odds]`, two body rows (away first, then home; or Over, Under).
Cell text: ML `-201`; PL `-1½+132`; total `o5½-103`.
"""
from __future__ import annotations

import re

import pandas as pd

TEAM = {"Anaheim Ducks": "ANA", "Boston Bruins": "BOS", "Buffalo Sabres": "BUF", "Calgary Flames": "CGY",
        "Carolina Hurricanes": "CAR", "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL",
        "Columbus Blue Jackets": "CBJ", "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
        "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN", "Montreal Canadiens": "MTL",
        "Nashville Predators": "NSH", "New Jersey Devils": "NJD", "New York Islanders": "NYI",
        "New York Rangers": "NYR", "Ottawa Senators": "OTT", "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT",
        "San Jose Sharks": "SJS", "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
        "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Utah Mammoth": "UTA", "Vancouver Canucks": "VAN",
        "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG", "Arizona Coyotes": "ARI"}

_CELL = re.compile(r"^([ou]?)([+-]?\d+(?:½)?)?([+-]\d+(?:\.\d+)?)$")


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s).replace("&nbsp;", " ").replace("Â½", "½").replace("�", "½").strip()
    return s


def cell(txt: str):
    """-> (line, price). ML cell has no line."""
    t = txt.strip().replace("\xa0", "")
    m = _CELL.match(t)
    if not m:
        return None, None
    line = m.group(2)
    if line is not None:
        line = float(line.replace("½", "")) + (0.5 if line.endswith("½") else 0.0) * (-1 if line.startswith("-") else 1)
        if m.group(1) == "":  # PL: sign of the line is the side's; magnitude only matters
            pass
    return line, float(m.group(3))


def parse_tables(section_html: str):
    """-> list of dicts {group, books, rows:[(label, [cells...])]} for offshore/vegas tables in a section."""
    out = []
    for t in re.findall(r"<table.*?</table>", section_html, re.S):
        group = "offshore" if "offshore-sportsbook" in t[:300] else "vegas" if "vegas-sportsbook" in t[:300] else "?"
        thead = re.search(r"<thead.*?</thead>", t, re.S).group(0)
        heads = [_clean(re.sub(r'<div class="tooltip">.*?</div></div></div>', "", h, flags=re.S))
                 for h in re.findall(r"<th>(.*?)</th>", thead, re.S)]
        body = re.search(r"<tbody.*?</tbody>", t, re.S).group(0)
        rows = []
        for tr in re.findall(r"<tr>(.*?)</tr>", body, re.S):
            tds = [_clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            rows.append((tds[0], tds[1:]))
        out.append({"group": group, "heads": heads[1:], "rows": rows})
    return out


def parse_game(html: str) -> dict:
    """-> {'start_utc','title','markets': {'ml'|'pl'|'total': [table...]}}"""
    title = re.search(r"<title>(.*?)</title>", html, re.S)
    dt = re.findall(r'datetime="([^"]+)"', html)
    secs = {}
    for key, sid in (("ml", "scroll-money"), ("pl", "scroll-spread"), ("total", "scroll-ou")):
        i = html.find(f'id="{sid}"')
        if i < 0:
            secs[key] = []
            continue
        nxt = [html.find(f'id="{o}"', i + 10) for o in ("scroll-money", "scroll-spread", "scroll-ou")]
        nxt = [n for n in nxt if n > i]
        j = min(nxt) if nxt else i + 20000
        secs[key] = parse_tables(html[i:j][:40000])
    return {"title": title.group(1) if title else None, "start_utc": dt[0] if dt else None, "markets": secs}


def american_to_prob(a):
    return 100 / (a + 100) if a > 0 else -a / (-a + 100)


def nov_vig_home(a_away, a_home):
    pa, ph = american_to_prob(a_away), american_to_prob(a_home)
    return ph / (pa + ph)


def parse_index(html: str):
    rows = []
    tbl = re.search(r'id="scroll-completed".*?</table>', html, re.S)
    if not tbl:
        return rows
    for tr in re.findall(r"<tr>(.*?)</tr>", tbl.group(0), re.S):
        m = re.search(r'href="/predictor/nhl-hockey-predictions/([0-9a-f-]{36})".*?datetime="([^"]+)"', tr, re.S)
        teams = re.findall(r'href="/teams/nhl-hockey-ratings/[^"]+">([^<]+)</a>', tr)
        if m and len(teams) >= 2:
            rows.append({"uuid": m.group(1), "start_utc": m.group(2), "away": TEAM.get(teams[0]), "home": TEAM.get(teams[1]),
                         "away_name": teams[0], "home_name": teams[1]})
    return rows
