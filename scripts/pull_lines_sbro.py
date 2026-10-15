"""Pull SBRO (sportsbookreviewsonline.com) NHL odds archive pages for 2021-22 and 2022-23 into data/raw/sbro/.
robots.txt: only /go/ disallowed. 3 s spacing, cached, never re-fetched. See docs/ops/data_sources.md."""
import time
from pathlib import Path

import requests

RAW = Path("data/raw/sbro")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NHL-Model-research"
SEASONS = ["2021-22", "2022-23"]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for s in SEASONS:
        p = RAW / f"nhl-odds-{s}.html"
        if p.exists() and p.stat().st_size > 50000:
            print("cached", s); continue
        for k in range(4):
            r = requests.get(f"https://www.sportsbookreviewsonline.com/scoresoddsarchives/nhl-odds-{s}/",
                             headers={"User-Agent": UA}, timeout=60)
            if r.status_code == 200:
                r.encoding = "utf-8"
                p.write_text(r.text, encoding="utf-8")
                print("fetched", s, len(r.text)); break
            time.sleep(3 * 2 ** k)
        time.sleep(3)


if __name__ == "__main__":
    main()
