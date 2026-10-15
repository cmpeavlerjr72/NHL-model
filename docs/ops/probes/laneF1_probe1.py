import requests, json, gzip, re, sys
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36","Accept":"application/json,text/html,*/*"}
def get(u,**k):
    try:
        r=requests.get(u,headers=UA,timeout=20,**k); return r
    except Exception as e: print("ERR",u,e); return None
def show(u):
    r=get(u)
    if r is None: return None
    print(r.status_code,len(r.content),u[:150]); return r
sb=json.load(gzip.open("data/raw/espn_scoreboard/20250115.json.gz"))
evs=sb.get("events",[]); print(len(evs))
ids=[(e["id"],e["shortName"]) for e in evs]; print(ids)
eid=ids[0][0]
base="https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl"
r=show(f"{base}/events/{eid}/competitions/{eid}/odds")
if r is not None and r.status_code==200:
    open("data/samples_laneF/espn_core/odds_20250115_%s.json"%eid,"w").write(r.text); print(r.text[:1500])
