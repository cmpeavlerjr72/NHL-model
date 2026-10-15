import requests, json, re
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def g(u,**k):
    try:
        r=requests.get(u,headers=UA,timeout=20,**k); print(r.status_code,len(r.content),r.headers.get("content-type","")[:30],u[:120]); return r
    except Exception as e: print("ERR",u,str(e)[:80])
# 2023 structure
j=json.load(open("data/samples_laneF/espn_core/odds_20230115_401459280.json"))
it=j["items"][5]; print(it["provider"]["name"], list(it.keys()), list(it["awayTeamOdds"].keys()))
print(json.dumps({k:v for k,v in it.items() if k not in("awayTeamOdds","homeTeamOdds")})[:600])
for u in ["https://api.actionnetwork.com/web/v1/scoreboard/nhl?date=20250115",
 "https://api.actionnetwork.com/web/v2/scoreboard/nhl?date=20250115&bookIds=15,30,76,75,123,69,68,972,71,247,79",
 "https://www.actionnetwork.com/nhl/odds",
 "https://www.actionnetwork.com/robots.txt",
 "https://www.sportsbookreview.com/betting-odds/nhl-hockey/?date=2025-01-15",
 "https://www.sportsbookreview.com/robots.txt",
 "https://www.covers.com/sport/hockey/nhl/odds",
 "https://www.covers.com/robots.txt",
 "https://api-web.nhle.com/v1/partner-game/US/now",
 "https://api-web.nhle.com/v1/gamecenter/2024020700/landing",
 "https://site.web.api.espn.com/apis/v2/scoreboard/header?sport=hockey&league=nhl&dates=20250115"]:
    r=g(u)
    if r is not None and r.status_code==200:
        t=r.text
        if "robots" in u: print(t[:700])
        elif "NEXT_DATA" in t: print("has NEXT_DATA")
