import requests, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-probe"}
G="https://gamma-api.polymarket.com"
def j(u,**p):
    r=requests.get(u,headers=H,params=p,timeout=25); print(r.status_code,r.url[:150]); 
    try: return r.json()
    except: print(r.text[:200]); return None
ev=j(G+"/events",tag_slug="nhl",closed="true",limit=500,order="endDate",ascending="false")
ds=sorted(e["endDate"][:10] for e in ev); print(len(ev),ds[0],ds[-1])
# earliest NHL game events
for off in (0,):
    ev2=j(G+"/events",tag_slug="nhl",closed="true",limit=5,order="endDate",ascending="true")
    for e in ev2: print(e["slug"],e["endDate"][:10])
# specific 2025-01-15 slugs
for s in ["nhl-dal-col-2025-01-15","nhl-tor-bos-2025-01-15","nhl-nyr-car-2025-01-15"]:
    e=j(G+"/events",slug=s); print(s,len(e) if e else e)
# try date-window
e=j(G+"/events",tag_slug="nhl",end_date_min="2025-01-10",end_date_max="2025-01-20",limit=20)
print(len(e) if e else e, [x["slug"] for x in (e or [])][:10])
e=j(G+"/events",tag_slug="nhl",end_date_min="2025-10-01",end_date_max="2025-10-10",limit=20)
print(len(e) if e else e, [x["slug"] for x in (e or [])][:10])
if e:
    m=e[0]["markets"][0]; print(json.dumps({k:m.get(k) for k in ("question","clobTokenIds","outcomes","outcomePrices","volume")}))
    tok=json.loads(m["clobTokenIds"])[0]
    h=j("https://clob.polymarket.com/prices-history",market=tok,interval="max",fidelity=60)
    print(str(h)[:300])
    json.dump({"event_slug":e[0]["slug"],"market":m,"history":h},open("data/samples_laneF/f2/polymarket_nhl_sample.json","w"))
