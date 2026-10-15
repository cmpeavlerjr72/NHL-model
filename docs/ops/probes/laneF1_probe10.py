import requests, json, re, time, gzip, os
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def rows(d):
    r=requests.get(f"https://www.sportsbookreview.com/betting-odds/nhl-hockey/?date={d}",headers=UA,timeout=25)
    m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',r.text,re.S); time.sleep(1.2)
    return json.loads(m.group(1))["props"]["pageProps"]["oddsTables"][0]["oddsTableModel"]["gameRows"]
g=rows("2025-01-15")[0]
for v in g["oddsViews"][:0]:
    if v: print(v["sportsbook"],v["openingLine"]["awayOdds"],v["openingLine"]["homeOdds"],"->",v["currentLine"]["awayOdds"],v["currentLine"]["homeOdds"])
for d in ["2024-10-22","2024-11-15","2025-03-15","2025-04-15","2023-11-15","2022-02-15","2021-11-15"]:
    gr=rows(d); e=d.replace("-","")
    ne=len(json.load(gzip.open(f"data/raw/espn_scoreboard/{e}.json.gz"))["events"]) if os.path.exists(f"data/raw/espn_scoreboard/{e}.json.gz") else None
    full=sum(1 for x in gr if any(v and v["openingLine"]["awayOdds"] is not None and v["currentLine"]["awayOdds"] is not None for v in x["oddsViews"]))
    print(d,"sbr games",len(gr),"espn games",ne,"with full ML open",full)
