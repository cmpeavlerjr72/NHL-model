import json, time, requests, collections
B="https://api.elections.kalshi.com/trade-api/v2"
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(p,**q):
    time.sleep(0.3)
    r=requests.get(B+p,params=q,headers=H,timeout=30)
    try: return r.status_code,r.json()
    except Exception: return r.status_code,r.text[:200]
SER=["KXNHLGAME","KXNHLSPREAD","KXNHLTOTAL","KXNHLTEAMTOTAL","KXNHL1P","KXNHL1PTOTAL","KXNHLGOAL","KXNHLANYGOAL","KXNHLPTS","KXNHLAST","KXNHLSAVES","KXNHLSAVE","KXNHLFIRSTGOAL","KXNHLOT","KXNHLOVERTIME","KXNHL1PBTTS","KXNHLF10G"]
out={}
for s in SER:
    c,j=g("/markets",series_ticker=s,status="open",limit=1000)
    ms=j.get("markets",[]) if isinstance(j,dict) else []
    ev=collections.Counter(m["event_ticker"] for m in ms)
    vol=sum(float(m.get("volume_fp") or 0) for m in ms)
    print(s,c,"open markets",len(ms),"events",len(ev),"cursor",bool(j.get("cursor")) if isinstance(j,dict) else None,"vol_fp",vol)
    if ms:
        m=ms[0]
        print("   keys:",sorted(m.keys()))
        for m in ms[:3]:
            print("   ",{k:m.get(k) for k in ("ticker","title","yes_sub_title","market_type","strike_type","floor_strike","cap_strike","yes_bid_dollars","yes_ask_dollars","no_bid_dollars","volume_fp","open_interest_fp","liquidity_dollars","open_time","close_time","expected_expiration_time")})
    out[s]=ms
json.dump(out,open("data/samples_laneB/kalshi_nhl_open_markets_2026-10-15.json","w"))
