import requests, json, time
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(u,**q):
    time.sleep(1); return requests.get(u,params=q,headers=H,timeout=30)
S="https://site.api.espn.com/apis/site/v2/sports/hockey/nhl"
r=g(S+"/scoreboard",dates="20260415"); print(r.status_code)
ev=r.json().get("events",[]); print("events",len(ev))
for e in ev[:2]:
    c=e["competitions"][0]; print(e["id"],e["name"],json.dumps(c.get("odds"))[:700])
if ev:
    r=g("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary",event=ev[0]["id"]); j=r.json()
    print("summary keys",list(j.keys())); print("pickcenter",json.dumps(j.get("pickcenter"))[:1200])
    json.dump({"scoreboard_event":ev[0],"pickcenter":j.get("pickcenter"),"odds":j.get("odds")},open("data/samples_laneB/espn_nhl_2026-04-15_sample.json","w"))
# 2022 sample
r=g(S+"/scoreboard",dates="20230115"); ev=r.json().get("events",[]); print("2023 events",len(ev), json.dumps(ev[0]["competitions"][0].get("odds"))[:300] if ev else "")
if ev:
    j=g("https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/summary",event=ev[0]["id"]).json(); print("2023 pickcenter",json.dumps(j.get("pickcenter"))[:500])
