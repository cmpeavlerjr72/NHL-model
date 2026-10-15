import requests, json, re, time
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def nd(u):
    r=requests.get(u,headers=UA,timeout=25)
    m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',r.text,re.S)
    time.sleep(1.2)
    return r.status_code,(json.loads(m.group(1)) if m else None),m.group(1) if m else ""
for path,d in [("","2025-01-15"),("pointspread/","2025-01-15"),("totals/","2025-01-15"),("","2024-12-10"),("","2023-01-15"),("","2022-01-15"),("","2021-01-20"),("","2019-01-15")]:
    u=f"https://www.sportsbookreview.com/betting-odds/nhl-hockey/{path}?date={d}"
    s,j,raw=nd(u)
    if not j: print(s,u,"no nextdata");continue
    gr=j["props"]["pageProps"]["oddsTables"][0]["oddsTableModel"]["gameRows"]
    nb=[len(g["oddsViews"]) for g in gr if g["oddsViews"]]
    v=next((x for g in gr for x in g["oddsViews"] if x), None)
    print(s,path or "moneyline/",d,"games",len(gr),"books/game",nb[:4], v and v["viewType"])
    if v: print("   ",json.dumps(v["openingLine"]),json.dumps(v["currentLine"]))
    if d in("2025-01-15",) and path: open(f"data/samples_laneF/sbr/next_data_{path.strip('/')}_20250115.json","w").write(raw)
    if d in("2023-01-15","2022-01-15"): open(f"data/samples_laneF/sbr/next_data_ml_{d.replace('-','')}.json","w").write(raw)
