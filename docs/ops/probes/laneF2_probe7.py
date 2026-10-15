import requests, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-probe"}
for pid in ["doi:10.7910/DVN/AONGK9","doi:10.7910/DVN/39ZFRO","doi:10.7910/DVN/DPPU8O"]:
    r=requests.get("https://dataverse.harvard.edu/api/datasets/:persistentId/",params={"persistentId":pid},headers=H,timeout=30)
    print("=====",pid,r.status_code)
    d=r.json()["data"]["latestVersion"]
    print(d.get("license"),d.get("termsOfUse"))
    for f in d["metadataBlocks"]["citation"]["fields"]:
        if f["typeName"] in("dsDescription","keyword","title"): print(f["typeName"],json.dumps(f["value"])[:1500])
    for f in d["files"]: print("  FILE",f["label"],f["dataFile"].get("filesize"),f["dataFile"].get("contentType"),f["dataFile"]["id"],f.get("restricted"))
