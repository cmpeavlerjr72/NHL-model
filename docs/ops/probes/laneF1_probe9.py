import requests, re, json
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def tx(u):
    t=requests.get(u,headers=UA,timeout=25).text
    t=re.sub(r'<style.*?</style>|<script.*?</script>','',t,flags=re.S); return re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',t))
for u,k in [("https://www.covers.com/sports/nhl/matchups?selectedDate=2025-01-15","Hurricanes"),("https://www.scoresandodds.com/nhl?date=2025-01-15","Carolina"),("https://sports.yahoo.com/nhl/scoreboard/?confId=&dateRange=2025-01-15","Hurricanes"),("https://www.oddsshark.com/nhl/scores?date=2025-01-15","Carolina")]:
    t=tx(u); i=t.find(k); print(u[:70],len(t),i); print("   ",t[max(0,i-100):i+400] if i>=0 else "NOT FOUND")
# raw covers
r=requests.get("https://www.covers.com/sports/nhl/matchups?selectedDate=2025-01-15",headers=UA,timeout=25)
for m in list(re.finditer(r'(Closing|Opening|closing line|data-book)',r.text))[:6]: print("COV",r.text[max(0,m.start()-100):m.start()+200].replace("\n"," "))
# NHL partner game past
r=requests.get("https://api-web.nhle.com/v1/partner-game/US/now",headers=UA); j=r.json(); print(list(j.keys()), json.dumps(j)[:500])
for u in ["https://api-web.nhle.com/v1/partner-game/US/2025-01-15","https://api-web.nhle.com/v1/gamecenter/2024020700/right-rail"]:
    r=requests.get(u,headers=UA); print(r.status_code,u,r.text[:200])
