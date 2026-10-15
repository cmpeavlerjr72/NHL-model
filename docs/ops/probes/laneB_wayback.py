import requests, json, time, collections, re
H={"User-Agent":"NHL-Model-research/0.1 (read-only audit)"}
for u in ["dailyfaceoff.com/starting-goalies","dailyfaceoff.com/starting-goalies/","rotowire.com/hockey/starting-goalies.php"]:
    time.sleep(1)
    r=requests.get("http://web.archive.org/cdx/search/cdx",params=dict(url=u,output="json",filter="statuscode:200",**{"from":"2021","to":"2026"},fl="timestamp"),headers=H,timeout=90)
    rows=r.json()[1:] if r.status_code==200 else []
    c=collections.Counter(x[0][:6] for x in rows); yrs=collections.Counter(x[0][:4] for x in rows)
    days=len({x[0][:8] for x in rows})
    print(u,r.status_code,len(rows),"distinct days",days,dict(yrs))
# one snapshot parse test
time.sleep(1)
r=requests.get("http://web.archive.org/web/20231122210556id_/https://www.dailyfaceoff.com/starting-goalies",headers=H,timeout=60)
t=r.text; print(r.status_code,len(t)); 
for k in ["Confirmed","Likely","Unconfirmed","strengthStatus","__NEXT_DATA__"]: print(k,t.count(k))
i=t.find("__NEXT_DATA__"); print(t[i:i+300] if i>0 else "")
m=re.findall(r'"newsDetails":"[^"]{0,60}|"playerName":"[^"]+"|"timestamp":"[^"]+"|"strength":"[^"]*"',t)[:12]; print(m)
