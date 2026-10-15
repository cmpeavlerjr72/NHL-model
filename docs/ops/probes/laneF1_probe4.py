import requests, json, re
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
g=lambda u:requests.get(u,headers=UA,timeout=25)
r=g("https://api.actionnetwork.com/robots.txt"); print("AN api robots",r.status_code,r.text[:200])
for d in ["20250115","20230115"]:
    r=g(f"https://api.actionnetwork.com/web/v1/scoreboard/nhl?date={d}"); j=r.json()
    gs=j.get("games",[]); print(d,len(gs))
    if d=="20250115": open("data/samples_laneF/actionnetwork/scoreboard_v1_20250115.json","w").write(r.text)
    if gs:
        g0=gs[0]; print(list(g0.keys())); o=g0.get("odds",[]); print(len(o)); 
        print(json.dumps(o[0])[:900] if o else None)
        print([ (x.get("book_id"),x.get("type")) for x in o][:40])
r=g("https://api.actionnetwork.com/web/v2/scoreboard/nhl?date=20250115&bookIds=15,30"); print(r.text[:300])
# SBR
r=g("https://www.sportsbookreview.com/betting-odds/nhl-hockey/?date=2025-01-15"); t=r.text
m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',t,re.S); j=json.loads(m.group(1))
open("data/samples_laneF/sbr/next_data_ml_20250115.json","w").write(m.group(1))
def walk(o,d=0,p=""):
    if d>6: return
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(v,(dict,list)): print(" "*d+p+"/"+k, type(v).__name__, len(v)); walk(v,d+1,"")
    elif isinstance(o,list) and o: walk(o[0],d+1)
walk(j["props"]["pageProps"])
