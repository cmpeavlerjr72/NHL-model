"""Lane B: anonymous read of DK Predictions public board JSON (same headers the CFB puller uses). No login, no cookies, no orders."""
import requests, json, time, sys
U="https://sportsbook-nash.draftkings.com/sites/PREDICT/api/sportscontent/controldata/home/leagueSubcategory/v1/markets"
H={"user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36","accept":"application/json","origin":"https://predictions.draftkings.com","referer":"https://predictions.draftkings.com/","accept-encoding":"identity","x-pe-cn":"predict-web","x-pe-cv":"1.12.0","x-pe-ep":"PR","x-pe-loc":"US-GA"}
def pull(lg,sub,top=100):
    p={"isBatchable":"false","eventsQuery":f"$filter=leagueId eq '{lg}' AND clientMetadata/Subcategories/any(s: s/Id eq '{sub}')","marketsQuery":f"$filter=clientMetadata/subCategoryId eq '{sub}' AND tags/all(t: t ne 'SportcastBetBuilder')","include":"Events","entity":"events","top":str(top)}
    time.sleep(0.5)
    r=requests.get(U+"?"+"&".join(k+"="+__import__("urllib.parse").parse.quote(v) for k,v in p.items()),headers=H,timeout=30)
    try: return r.status_code,r.json()
    except Exception: return r.status_code,r.text[:200]
if __name__=="__main__":
    lg=sys.argv[1]
    for sub in sys.argv[2:]:
        c,j=pull(lg,sub)
        if c!=200: print(lg,sub,c,str(j)[:150]); continue
        ev=j.get("events",[]);mk=j.get("markets",[]);se=j.get("selections",[])
        print(lg,sub,c,"events",len(ev),"markets",len(mk),"sels",len(se))
        if mk:
            print("  market names:",sorted({m["name"] for m in mk})[:12])
            print("  ev ex:",[e["name"] for e in ev[:3]])
        json.dump(j,open(f"data/samples_laneB/dk_nhl_{lg}_{sub}.json","w"))
