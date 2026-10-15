import requests, json, time
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(u,**q):
    time.sleep(1); return requests.get(u,params=q,headers=H,timeout=30)
S="https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
def keys(d,p=""):
    out=[]
    for k,v in d.items():
        if isinstance(v,dict): out+=keys(v,p+k+".")
        else: out.append(p+k)
    return out
for d in ["20211215","20221215","20231215","20241215","20251215","20260115"]:
    ev=g(S+"/scoreboard",dates=d).json().get("events",[])
    if not ev: print(d,"no events");continue
    j=g(S+"/summary",event=ev[0]["id"]).json(); pc=j.get("pickcenter") or []
    print(d,ev[0]["name"],"providers",[(p["provider"]["name"],sorted(set(k.split('.')[0] if False else k for k in keys(p) if any(x in k for x in("open","close","current")))) [:6]) for p in pc][:2])
    if d=="20251215": json.dump(pc,open("data/samples_laneB/espn_nhl_pickcenter_2025-12-15.json","w"),indent=1)
