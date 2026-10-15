import requests, re, json
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
def txt(u):
    r=requests.get(u,headers=UA,timeout=25); return r.status_code,re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',r.text))
for u in ["https://www.sportsbookreview.com/terms-of-use/","https://www.sportsbookreview.com/terms-and-conditions/","https://www.espn.com/espn/news/story?page=termsOfUse"]:
    s,t=txt(u); print(s,u,len(t))
    for m in re.finditer(r'(scrap|robot|spider|automated|data min|crawl)',t,re.I):
        print("   ...",t[max(0,m.start()-150):m.start()+250]); break
