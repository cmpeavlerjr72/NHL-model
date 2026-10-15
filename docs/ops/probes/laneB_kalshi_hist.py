import json, time, requests
B="https://api.elections.kalshi.com/trade-api/v2"
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
def g(p,**q):
    time.sleep(0.3)
    r=requests.get(B+p,params=q,headers=H,timeout=30)
    try: return r.status_code,r.json()
    except Exception: return r.status_code,r.text[:300]
c,j=g("/series/KXNHLGAME"); print("series",c,json.dumps(j)[:900])
c,j=g("/historical/cutoff"); print("hist cutoff",c,json.dumps(j)[:300])
for s in ["KXNHLGAME","KXNHLTOTAL","KXNHLGOAL","KXNHLPTS","KXNHLSAVE"]:
    allm=[];cur=None
    for _ in range(40):
        q=dict(series_ticker=s,status="settled",limit=1000)
        if cur:q["cursor"]=cur
        c,j=g("/markets",**q)
        if c!=200: print(s,"err",c,j);break
        allm+=j["markets"];cur=j.get("cursor")
        if not cur:break
    if allm:
        ct=sorted(m["close_time"] for m in allm)
        print(s,"settled markets",len(allm),"earliest close",ct[0],"latest",ct[-1])
        json.dump(allm[:200],open(f"data/samples_laneB/kalshi_{s}_settled_sample.json","w"))
    else: print(s,"settled 0")
# historical endpoint
c,j=g("/historical/markets",limit=5); print("historical/markets",c,json.dumps(j)[:400])
