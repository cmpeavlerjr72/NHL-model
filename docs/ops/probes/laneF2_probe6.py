import requests
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-probe"}
def j(u,**p):
    try:
        r=requests.get(u,headers=H,params=p,timeout=25)
        return r.status_code, r.json()
    except Exception as e: return None,str(e)
for q in ["NHL betting odds","NHL moneyline odds","hockey betting odds closing lines"]:
    s,d=j("https://zenodo.org/api/records",q=q,size=8)
    print("ZENODO",q,s)
    if s==200:
        for h in d["hits"]["hits"]: print("  ",h["metadata"]["publication_date"],h["metadata"]["title"][:90],h["links"]["self_html"])
    s,d=j("https://dataverse.harvard.edu/api/search",q=q,type="dataset",per_page=6)
    print("DATAVERSE",s)
    if s==200:
        for h in d["data"]["items"]: print("  ",h.get("published_at","")[:10],h["name"][:90],h["url"])
    s,d=j("https://api.osf.io/v2/nodes/",**{"filter[title][icontains]":q,"page[size]":5})
    print("OSF",s)
    if s==200:
        for h in d["data"]: print("  ",h["attributes"]["title"][:90],h["links"]["html"])
for q in ["nhl odds history csv","nhl closing lines","pinnacle historical odds","nhl moneyline dataset","hockey odds scraper","nhl sportsbookreview"]:
    s,d=j("https://api.github.com/search/repositories",q=q,sort="updated",per_page=8)
    print("GH",q,s)
    if s==200:
        for i in d["items"]: print("  ",i["full_name"],i["stargazers_count"],i["pushed_at"][:10],(i["description"] or "")[:80])
