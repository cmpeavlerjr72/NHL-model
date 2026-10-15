import requests, re, json
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) research-probe"}
B="https://www.sportsbookreviewsonline.com"
r=requests.get(B+"/scoresoddsarchives/nhl/nhloddsarchives.htm",headers=H,timeout=25)
t=r.text
print(len(t)); 
print(sorted(set(re.findall(r'href="([^"]*(?:nhl|xlsx|xls|zip)[^"]*)"',t,re.I)))[:60])
txt=re.sub(r'<[^>]+>',' ',t); txt=re.sub(r'\s+',' ',txt)
i=txt.find('Historical NHL'); print(txt[i:i+1800])
