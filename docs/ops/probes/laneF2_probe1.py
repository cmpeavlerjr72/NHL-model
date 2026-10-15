import requests, json, sys
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-probe"}
def g(u,**k):
    try:
        r=requests.get(u,headers=H,timeout=25,**k); return r
    except Exception as e:
        print("ERR",u,e); return None
out={}
# SBRO
for u in ["https://www.sportsbookreviewsonline.com/scoresoddsarchives/nhl/nhloddsarchives.htm",
 "https://www.sportsbookreviewsonline.com/scoresoddsarchives/nhl-odds-archives.htm",
 "https://www.sportsbookreviewsonline.com/robots.txt",
 "https://web.archive.org/cdx/search/cdx?url=sportsbookreviewsonline.com/scoresoddsarchives/nhl/*&output=json&limit=15&filter=statuscode:200"]:
    r=g(u); print("SBRO",u,r.status_code if r is not None else None, (r.text[:600] if r is not None else ""));print()
# HF
r=g("https://huggingface.co/api/datasets?search=nhl&limit=50")
print("HF nhl",[d["id"] for d in r.json()] if r else None)
r=g("https://huggingface.co/api/datasets?search=hockey&limit=50")
print("HF hockey",[d["id"] for d in r.json()] if r else None)
r=g("https://huggingface.co/api/datasets?search=sports%20odds&limit=50")
print("HF odds",[d["id"] for d in r.json()] if r else None)
# GitHub
for q in ["nhl odds","nhl betting odds dataset","sportsbookreview scraper","hockey odds csv"]:
    r=g("https://api.github.com/search/repositories",params={"q":q,"sort":"stars","per_page":10})
    if r is not None and r.status_code==200:
        print("GH",q)
        for i in r.json()["items"]: print("  ",i["full_name"],i["stargazers_count"],i["pushed_at"][:10],(i["description"] or "")[:90])
    else: print("GH",q,r.status_code if r is not None else None)
