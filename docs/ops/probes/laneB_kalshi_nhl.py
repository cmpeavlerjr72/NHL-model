"""Lane B read-only Kalshi probe: unauthenticated public market data only."""
import json, time, sys, requests
B="https://api.elections.kalshi.com/trade-api/v2"
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(p,**q):
    time.sleep(0.3)
    r=requests.get(B+p,params=q,headers=H,timeout=30)
    try: return r.status_code,r.json()
    except Exception: return r.status_code,r.text[:200]
c,j=g("/series",category="Sports",limit=1000)
print("series status",c, type(j))
ser=j.get("series",[]) if isinstance(j,dict) else []
print(len(ser))
nhl=[s for s in ser if "NHL" in s.get("ticker","").upper() or "hockey" in json.dumps(s).lower()]
for s in nhl: print(s["ticker"],"|",s.get("title"),"|",s.get("frequency"),"|",s.get("fee_type"),s.get("fee_multiplier"))
json.dump(nhl,open("data/samples_laneB/kalshi_nhl_series.json","w"),indent=1)
