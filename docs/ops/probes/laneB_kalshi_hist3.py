import json, time, requests, datetime, collections
B="https://api.elections.kalshi.com/trade-api/v2"
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(p,**q):
    time.sleep(0.3)
    r=requests.get(B+p,params=q,headers=H,timeout=30)
    try: return r.status_code,r.json()
    except Exception: return r.status_code,r.text[:300]
res={}
for ser in ["KXNHLSPREAD","KXNHLTEAMTOTAL","KXNHLPTS","KXNHLAST","KXNHLSAVE","KXNHL1PTOTAL","KXNHLOT"]:
    allm=[];cur=None
    for _ in range(80):
        q=dict(series_ticker=ser,limit=1000)
        if cur:q["cursor"]=cur
        c,j=g("/historical/markets",**q)
        if c!=200: print(ser,c,str(j)[:200]);break
        allm+=j.get("markets",[]);cur=j.get("cursor")
        if not cur:break
    if allm:
        ct=sorted(m["close_time"] for m in allm); print(ser,len(allm),ct[0][:10],ct[-1][:10])
# game series monthly distribution + sample
allm=[];cur=None
for _ in range(10):
    q=dict(series_ticker="KXNHLGAME",limit=1000)
    if cur:q["cursor"]=cur
    c,j=g("/historical/markets",**q); allm+=j["markets"];cur=j.get("cursor")
    if not cur:break
print(sorted(collections.Counter(m["close_time"][:7] for m in allm).items()))
json.dump(allm[:300],open("data/samples_laneB/kalshi_KXNHLGAME_historical_sample.json","w"))
m=allm[100]; print(m["ticker"],m["result"],m.get("last_price_dollars"),m.get("volume_fp"))
t=m["ticker"]
st=int(datetime.datetime.fromisoformat(m["open_time"].replace("Z","+00:00")).timestamp()); en=int(datetime.datetime.fromisoformat(m["close_time"].replace("Z","+00:00")).timestamp())
for p,q in [(f"/historical/markets/{t}/candlesticks",dict(start_ts=st,end_ts=en,period_interval=60)),("/historical/trades",dict(ticker=t,limit=3)),(f"/series/KXNHLGAME/markets/{t}/candlesticks",dict(start_ts=st,end_ts=en,period_interval=60))]:
    c,j=g(p,**q); print(p,c,str(j)[:350])
