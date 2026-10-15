"""Lane F3 probe 1: robots + one request per long-tail candidate (2024-25 date 2025-01-15).
Read-only, generic UA, ~2 requests per host."""
import json, os, re, sys, time
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "samples_laneF")
OUT = os.path.abspath(OUT)

PROBES = {
    "dratings": ("https://www.dratings.com", "https://www.dratings.com/predictor/nhl-hockey-predictions/completed/1?conference_id=&date=2025-01-15"),
    "dailyfaceoff": ("https://www.dailyfaceoff.com", "https://www.dailyfaceoff.com/starting-goalies/2025-01-15"),
    "killersports": ("https://killersports.com", "https://killersports.com/nhl/query?sdql=date%3D20250115&submit=++S+D+Q+L+%21++"),
    "sportsdatabase": ("https://sportsdatabase.com", "https://sportsdatabase.com/nhl/query?output=default&sdql=date%3D20250115&submit=++S+D+Q+L+%21++"),
    "teamrankings": ("https://www.teamrankings.com", "https://www.teamrankings.com/nhl/team/boston-bruins/odds-history?season-filter=2024"),
    "statmuse": ("https://www.statmuse.com", "https://www.statmuse.com/money/ask/nhl-moneyline-results-january-15-2025"),
    "apisports": ("https://v1.hockey.api-sports.io", "https://v1.hockey.api-sports.io/odds?league=57&season=2024"),
    "balldontlie": ("https://api.balldontlie.io", "https://api.balldontlie.io/nhl/v1/odds?dates[]=2025-01-15"),
    "lineups": ("https://www.lineups.com", "https://www.lineups.com/nhl/odds"),
    "dimers": ("https://www.dimers.com", "https://www.dimers.com/bet-hub/nhl/schedule"),
}

def main(names):
    res = {}
    for name in names:
        root, url = PROBES[name]
        d = os.path.join(OUT, f"F3_{name}"); os.makedirs(d, exist_ok=True)
        r = {}
        try:
            rb = requests.get(root + "/robots.txt", headers=UA, timeout=15)
            r["robots_status"] = rb.status_code
            open(os.path.join(d, "robots.txt"), "w", encoding="utf-8").write(rb.text[:20000])
        except Exception as e:
            r["robots_err"] = str(e)[:200]
        time.sleep(1)
        try:
            g = requests.get(url, headers=UA, timeout=20)
            r["status"] = g.status_code; r["len"] = len(g.text); r["ctype"] = g.headers.get("content-type")
            ext = "json" if "json" in (r["ctype"] or "") else "html"
            open(os.path.join(d, f"sample_2025-01-15.{ext}"), "w", encoding="utf-8").write(g.text[:400000])
            r["snippet"] = re.sub(r"\s+", " ", g.text[:300])
        except Exception as e:
            r["err"] = str(e)[:200]
        res[name] = r
        print(name, json.dumps(r)[:600]); sys.stdout.flush()
        time.sleep(1)

if __name__ == "__main__":
    main(sys.argv[1:] or list(PROBES))
