import requests, re
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-probe"}
G="https://gamma-api.polymarket.com"
pat=re.compile(r"^nhl-[a-z]+-[a-z]+-\d{4}-\d\d-\d\d$")
for a,b in [("2024-10-01","2024-11-30"),("2024-12-01","2024-12-20"),("2024-12-20","2025-01-08")]:
    r=requests.get(G+"/events",headers=H,params=dict(tag_slug="nhl",end_date_min=a,end_date_max=b,limit=500,order="endDate",ascending="true"),timeout=25).json()
    g=sorted(x["slug"][-10:] for x in r if pat.match(x["slug"]))
    print(a,b,len(r),len(g),g[:1],g[-1:])
