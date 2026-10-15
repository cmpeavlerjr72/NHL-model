import requests, json, time, datetime, collections
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
S="https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
def g(u,**q):
    time.sleep(0.8)
    for i in range(3):
        try:
            r=requests.get(u,params=q,headers=H,timeout=30)
            if r.status_code==200: return r.json()
        except Exception: pass
        time.sleep(2*(i+1))
    return {}
rows=[]
for yr in (2021,2022,2023,2024,2025):
    ids=[]
    for k in range(7):
        d=datetime.date(yr,12,8)+datetime.timedelta(days=k)
        for e in g(S+"/scoreboard",dates=d.strftime("%Y%m%d")).get("events",[]):
            ids.append((d.isoformat(),e["id"],e["name"],e["status"]["type"]["state"]))
    for d,i,n,st in ids:
        pc=g(S+"/summary",event=i).get("pickcenter") or []
        if not pc: rows.append(dict(season=yr,date=d,id=i,name=n,provider=None)); continue
        for p in pc:
            rows.append(dict(season=yr,date=d,id=i,name=n,provider=p["provider"]["name"],
              ml_away_open=(p.get("moneyline",{}).get("away",{}).get("open",{}) or {}).get("odds"),
              ml_away_close=(p.get("moneyline",{}).get("away",{}).get("close",{}) or {}).get("odds"),
              ml_home_close=(p.get("moneyline",{}).get("home",{}).get("close",{}) or {}).get("odds"),
              total_close=(p.get("total",{}).get("over",{}).get("close",{}) or {}).get("line"),
              pl_close=(p.get("pointSpread",{}).get("away",{}).get("close",{}) or {}).get("line"),
              legacy_ml_away=(p.get("awayTeamOdds") or {}).get("moneyLine"), legacy_ou=p.get("overUnder")))
json.dump(rows,open("data/samples_laneB/espn_nhl_oneweek_per_season_dec8-14.json","w"),indent=0)
by=collections.defaultdict(lambda:[0,0,collections.Counter(),0,0])
games=collections.defaultdict(set)
for r in rows:
    games[r["season"]].add(r["id"])
    if r["provider"]:
        b=by[r["season"]]; b[2][r["provider"]]+=1
        if r.get("ml_away_close") or r.get("legacy_ml_away"): b[3]+=1
        if r.get("ml_away_open"): b[4]+=1
for y in sorted(games): print(y,"games",len(games[y]),"provider rows",dict(by[y][2]),"with ML",by[y][3],"with open",by[y][4])
