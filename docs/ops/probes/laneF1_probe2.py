import requests, json, gzip
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
base="https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl"
def g(u):
    r=requests.get(u,headers=UA,timeout=20); return r
for d in ["20250115","20230115","20220115","20210115","20241015","20250410"]:
    try: sb=json.load(gzip.open(f"data/raw/espn_scoreboard/{d}.json.gz"))
    except Exception as e: print(d,"nofile");continue
    for e in sb["events"][:2]:
        eid=e["id"]; r=g(f"{base}/events/{eid}/competitions/{eid}/odds")
        j=r.json() if r.status_code==200 else {}
        its=j.get("items",[])
        print(d,eid,e["shortName"],r.status_code,[(i["provider"]["name"],i.get("overUnder"),("open" in i.get("total",{}) or "open" in i.get("homeTeamOdds",{})),i.get("awayTeamOdds",{}).get("moneyLine")) for i in its])
        if d in("20230115","20220115","20241015") and e is sb["events"][0]:
            open(f"data/samples_laneF/espn_core/odds_{d}_{eid}.json","w").write(r.text)
eid="401688304"
for u in [f"{base}/events/{eid}/competitions/{eid}/odds/58/history/0/movement",f"{base}/events/{eid}/competitions/{eid}/odds/58/history/0/movement?limit=100",f"{base}/events/{eid}/competitions/{eid}/odds/58"]:
    r=g(u); print(r.status_code,len(r.text),u[-60:]); 
    if r.status_code==200: print(r.text[:600])
