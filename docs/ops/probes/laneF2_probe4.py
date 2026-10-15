import requests, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-probe"}
G="https://gamma-api.polymarket.com"
def ev(a,b,lim=100):
    r=requests.get(G+"/events",headers=H,params=dict(tag_slug="nhl",end_date_min=a,end_date_max=b,limit=lim),timeout=25); return r.json()
for a,b in [("2024-09-01","2024-10-31"),("2024-10-01","2024-11-30"),("2024-12-01","2024-12-31"),("2025-01-01","2025-01-31"),("2025-03-01","2025-03-31")]:
    e=ev(a,b); g=[x["slug"] for x in e if x["slug"].startswith("nhl-") and x["slug"][-4:].isdigit()]
    print(a,b,len(e),len(g),g[:2])
e=ev("2025-01-14","2025-01-16")
g=[x for x in e if x["slug"].startswith("nhl-") and x["slug"][-2:].isdigit()]
print("jan15 games",len(g),[x["slug"] for x in g])
x=g[0]; print(x["slug"],len(x["markets"]))
for m in x["markets"]: print(m.get("question"),m.get("outcomes"),m.get("outcomePrices"),m.get("volume"),m.get("sportsMarketType"))
m=x["markets"][0]; toks=json.loads(m["clobTokenIds"])
out={"event":x["slug"],"markets":[{k:m.get(k) for k in("question","outcomes","outcomePrices","volume","clobTokenIds","gameStartTime","sportsMarketType")} for m in x["markets"]]}
for iv,fd in (("max",60),("max",1440)):
    r=requests.get("https://clob.polymarket.com/prices-history",headers=H,params=dict(market=toks[0],interval=iv,fidelity=fd),timeout=25)
    h=r.json().get("history",[]); print(iv,fd,r.status_code,len(h),h[:2],h[-2:])
    out["hist_%s_%s"%(iv,fd)]=h[:400]
# earliest pre-2024-09 game event?
for a,b in [("2023-10-01","2024-04-30"),("2024-04-01","2024-06-30")]:
    e=ev(a,b); print(a,len([x for x in e if x["slug"].startswith("nhl-") and x["slug"][-4:].isdigit()]),[x["slug"] for x in e][:3])
json.dump(out,open("data/samples_laneF/f2/polymarket_nhl_2025-01-15_sample.json","w"))
