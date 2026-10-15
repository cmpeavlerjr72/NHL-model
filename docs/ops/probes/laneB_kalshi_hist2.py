import json, time, requests
B="https://api.elections.kalshi.com/trade-api/v2"
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(p,**q):
    time.sleep(0.3)
    r=requests.get(B+p,params=q,headers=H,timeout=30)
    try: return r.status_code,r.json()
    except Exception: return r.status_code,r.text[:300]
c,j=g("/series/KXNHLGAME"); s=j["series"]; print({k:v for k,v in s.items() if k not in("additional_prohibitions","product_metadata","settlement_sources","contract_terms_url","contract_url")}); print([x for x in s if 'fee' in x])
for ser in ["KXNHLGAME","KXNHLTOTAL","KXNHLGOAL","KXNHLSAVE"]:
  for ep in ("/historical/markets",):
    allm=[];cur=None
    for _ in range(60):
        q=dict(series_ticker=ser,limit=1000)
        if cur:q["cursor"]=cur
        c,j=g(ep,**q)
        if c!=200: print(ser,ep,c,str(j)[:200]);break
        allm+=j.get("markets",[]);cur=j.get("cursor")
        if not cur:break
    if allm:
        ct=sorted(m["close_time"] for m in allm); print(ser,ep,len(allm),ct[0],ct[-1])
        # check filter honored
        print("  tickers sample",[m['ticker'] for m in allm[:2]])
# one settled market full record
m=json.load(open("data/samples_laneB/kalshi_KXNHLGAME_settled_sample.json"))[0]
print({k:m[k] for k in m if k not in("rules_primary","rules_secondary")})
# candlesticks unauth
t=m["ticker"]; import datetime
st=int(datetime.datetime.fromisoformat(m["open_time"].replace("Z","+00:00")).timestamp()); en=int(datetime.datetime.fromisoformat(m["close_time"].replace("Z","+00:00")).timestamp())
c,j=g(f"/series/KXNHLGAME/markets/{t}/candlesticks",start_ts=st,end_ts=en,period_interval=60); print("candles unauth",c,str(j)[:500])
c,j=g("/markets/trades",ticker=t,limit=5); print("trades unauth",c,str(j)[:500])
c,j=g(f"/markets/{t}/orderbook"); print("orderbook(open?)",c,str(j)[:200])
