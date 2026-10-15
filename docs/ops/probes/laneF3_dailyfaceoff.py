"""Lane F3: Daily Faceoff historical starting-goalies date pages (read-only, generic UA).
URL: https://www.dailyfaceoff.com/starting-goalies/YYYY-MM-DD  (robots: only /api/ and /cms/ disallowed)
__NEXT_DATA__.props.pageProps.data[] = one row per game: goalies, Confirmed/Likely status, news text,
newsCreatedAt timestamps, and ONE puck-line price pair (pointSpread, home/awayTeamMoneylinePointSpread).
Usage: python -I laneF3_dailyfaceoff.py 2025-01-15 2022-01-15
"""
import json, os, re, sys, time
import requests
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "samples_laneF", "F3_dailyfaceoff"))
os.makedirs(OUT, exist_ok=True)
for d in sys.argv[1:]:
    t = requests.get(f"https://www.dailyfaceoff.com/starting-goalies/{d}", headers=UA, timeout=20).text
    pp = json.loads(re.search(r'id="__NEXT_DATA__"[^>]*>(.*?)</script>', t, re.S).group(1))["props"]["pageProps"]
    games = pp.get("data") or []
    json.dump(games, open(os.path.join(OUT, f"games_{d}.json"), "w"), indent=1)
    for g in games:
        print(d, g["awayTeamName"], "@", g["homeTeamName"], "| PL", g.get("pointSpread"), g.get("awayTeamMoneylinePointSpread"), g.get("homeTeamMoneylinePointSpread"),
              "| G", g.get("awayGoalieName"), g.get("awayNewsStrengthName"), g.get("awayNewsCreatedAt"), "/", g.get("homeGoalieName"), g.get("homeNewsStrengthName"), g.get("homeNewsCreatedAt"))
    time.sleep(2)
