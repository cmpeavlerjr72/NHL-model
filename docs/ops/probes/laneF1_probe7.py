import requests, json, gzip, os, time
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
base="https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl"
dates=["20211115","20220215","20221115","20230215","20231115","20240215","20241022","20241115","20241215","20250115","20250215","20250315","20250415","20251115"]
for d in dates:
    p=f"data/raw/espn_scoreboard/{d}.json.gz"
    if not os.path.exists(p): print(d,"no scoreboard cache");continue
    evs=json.load(gzip.open(p))["events"]
    n=0;withodds=0;withopen=0;withclose=0;prov=set();tot_open=0
    for e in evs:
        eid=e["id"]; r=requests.get(f"{base}/events/{eid}/competitions/{eid}/odds",headers=UA,timeout=20); time.sleep(0.4)
        n+=1
        its=r.json().get("items",[]) if r.status_code==200 else []
        its=[i for i in its if "Live" not in i["provider"]["name"]]
        if its: withodds+=1
        for i in its:
            prov.add(i["provider"]["name"])
        if any("open" in i.get("awayTeamOdds",{}) for i in its): withopen+=1
        if any("close" in i.get("awayTeamOdds",{}) for i in its): withclose+=1
        if any("open" in i.get("total",{}) for i in its): tot_open+=1
    print(d,"games",n,"withodds",withodds,"open",withopen,"close",withclose,"totopen",tot_open,sorted(prov)[:14])
