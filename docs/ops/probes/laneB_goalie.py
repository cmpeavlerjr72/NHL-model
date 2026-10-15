import requests, json, time
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(u,**q):
    time.sleep(1); r=requests.get(u,params=q,headers=H,timeout=30); return r
r=g("https://api-web.nhle.com/v1/schedule/2026-10-15"); print("sched",r.status_code)
games=[x for d in r.json()["gameWeek"] if d["date"]=="2026-10-15" for x in d["games"]]
print(len(games),[ (x["id"],x["awayTeam"]["abbrev"],x["homeTeam"]["abbrev"],x["startTimeUTC"],x["gameState"]) for x in games[:3]])
gid=games[0]["id"]
r=g(f"https://api-web.nhle.com/v1/gamecenter/{gid}/landing"); j=r.json(); print("landing",r.status_code,list(j.keys()))
print(json.dumps(j.get("matchup",{}).get("goalieComparison",{}))[:700])
r=g(f"https://api-web.nhle.com/v1/gamecenter/{gid}/right-rail"); j=r.json(); print("rail",r.status_code,list(j.keys()))
# Wayback
r=g("http://archive.org/wayback/available",url="dailyfaceoff.com/starting-goalies",timestamp="20231115"); print("wayback",r.status_code,r.text[:300])
r=g("http://web.archive.org/cdx/search/cdx",url="dailyfaceoff.com/starting-goalies/",output="json",limit="5",**{"from":"2022","to":"2025","collapse":"timestamp:8"}); print("cdx",r.status_code,r.text[:400])
for u in ["https://www.dailyfaceoff.com/robots.txt","https://www.rotowire.com/hockey/starting-goalies.php"]:
    r=g(u); print(u,r.status_code,len(r.text)); 
    if "robots" in u: print(r.text[:600])
