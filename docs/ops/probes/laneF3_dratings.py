"""Lane F3: DRatings NHL completed-games probe (read-only, generic UA, 2s spacing).

Index:  https://www.dratings.com/predictor/nhl-hockey-predictions/completed/{page}
        (~14 games/page, newest first; page 118 = 2025-03-11, page 400 = 2022-02-08)
Game:   https://www.dratings.com/predictor/nhl-hockey-predictions/{uuid}
        Money line / puck line / over-under tables: "Open" + per-book close for
        offshore (Heritage, Bovada, BetOnline, YouWager, SportsBetting) and
        Vegas (South Point, Circa, Wynn, Stations, Westgate) + best line + no-vig.
Usage:  python -I laneF3_dratings.py [page] [n_games]
"""
import json, os, re, sys, time
import requests

sys.stdout.reconfigure(encoding="utf-8")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
BASE = "https://www.dratings.com/predictor/nhl-hockey-predictions/"
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "samples_laneF", "F3_dratings"))


def text(html):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    s = re.sub(r"<br\s*/?>", " | ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("½", ".5").replace("Â½", ".5")
    s = re.sub(r"\s+", " ", s)
    # strip tooltip boilerplate
    s = re.sub(r"(Implied Margin|No-Vig Odds|Base Rating|Bet Trends|Sharp Line|Steam Move) [A-Z][^.]*\..*?More on \1", r"\1", s)
    return s


def parse_index(html):
    rows = []
    tbl = re.search(r'id="scroll-completed".*?</table>', html, re.S).group(0)
    for tr in re.findall(r"<tr>(.*?)</tr>", tbl, re.S):
        m = re.search(r'href="/predictor/nhl-hockey-predictions/([0-9a-f-]{36})".*?datetime="([^"]+)"', tr, re.S)
        if not m:
            continue
        teams = re.findall(r'href="/teams/nhl-hockey-ratings/[^"]+">([^<]+)</a>', tr)
        off = re.findall(r'<div class="offshore-sportsbook">(.*?)</div>', tr, re.S)
        veg = re.findall(r'<div class="vegas-sportsbook">(.*?)</div>', tr, re.S)
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        rows.append({
            "uuid": m.group(1), "start_utc": m.group(2), "away_or_first": teams[0] if teams else None,
            "home_or_second": teams[1] if len(teams) > 1 else None,
            "best_offshore_ml": off[0].split("<br />") if off else None,
            "best_vegas_ml": veg[0].split("<br />") if veg else None,
            "best_offshore_pl": off[1].split("<br />") if len(off) > 1 else None,
            "best_vegas_pl": veg[1].split("<br />") if len(veg) > 1 else None,
            "final": re.sub(r"<[^>]+>", " ", cells[5]).split() if len(cells) > 5 else None,
        })
    return rows


def parse_game(html):
    s = text(html)
    out = {}
    for label, anchor in [("moneyline", "Money Line Analysis"), ("puckline", "Spread Implied Margin"), ("total", "Over/Under Analysis")]:
        i = s.find(anchor)
        out[label] = s[i:i + 1400] if i >= 0 else None
    return out


def main():
    page = int(sys.argv[1]) if len(sys.argv) > 1 else 118
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    os.makedirs(OUT, exist_ok=True)
    ir = requests.get(f"{BASE}completed/{page}", headers=UA, timeout=20); ir.encoding = "utf-8"; idx = ir.text
    rows = parse_index(idx)
    json.dump(rows, open(os.path.join(OUT, f"index_page{page}.json"), "w"), indent=1)
    print(f"page {page}: {len(rows)} games, {rows[0]['start_utc'] if rows else None} .. {rows[-1]['start_utc'] if rows else None}")
    for r in rows[:n]:
        time.sleep(2)
        gr = requests.get(BASE + r["uuid"], headers=UA, timeout=20); gr.encoding = "utf-8"; g = gr.text
        parsed = parse_game(g)
        json.dump({"index_row": r, "sections_text": parsed}, open(os.path.join(OUT, f"game_{r['uuid']}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(json.dumps(r)); print({k: (v[:400] if v else v) for k, v in parsed.items()})


if __name__ == "__main__":
    main()
