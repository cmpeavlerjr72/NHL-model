import requests, re, time
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
urls=["https://www.covers.com/sports/nhl/matchups?selectedDate=2025-01-15",
"https://www.covers.com/sport/hockey/nhl/odds?date=2025-01-15",
"https://www.oddsshark.com/nhl/odds",
"https://www.oddsshark.com/nhl/scores?date=2025-01-15",
"https://www.vegasinsider.com/nhl/odds/las-vegas/",
"https://www.scoresandodds.com/nhl?date=2025-01-15",
"https://sports.yahoo.com/nhl/scoreboard/?confId=&dateRange=2025-01-15",
"https://www.cbssports.com/nhl/odds/",
"https://api.foxsports.com/bifrost/v1/nhl/scoreboard/segment/20250115?apikey=jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq",
"https://www.rotowire.com/betting/nhl/odds",
"https://www.oddstrader.com/nhl/",
"https://www.actionnetwork.com/nhl/odds/2025-01-15",
"https://api-web.nhle.com/v1/partner-game/US/now",
"https://api.nhle.com/stats/rest/en/game?cayenneExp=gameDate=%222025-01-15%22",
"https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/events/401688304/competitions/401688304/probabilities",
"https://www.pickswise.com/nhl/odds/",
"https://www.thescore.com/nhl/events",
]
for u in urls:
    try:
        r=requests.get(u,headers=UA,timeout=20); t=r.text
        odds=len(re.findall(r'[+\-−]\d{3}\b',t))
        print(r.status_code,len(t),"oddslike",odds,"NEXT" if "__NEXT_DATA__" in t else "",u)
    except Exception as e: print("ERR",u,str(e)[:60])
    time.sleep(1)
