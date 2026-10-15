"""Parse cached SBRO pages -> data/processed/lines_sbro_v1.parquet (one row per matched game, wide).
Columns: game_id, season, game_date, home, away, ml_open_{home,away}, ml_close_{home,away}, pl_{home,away}_{line,price},
total_open_line/_p1/_p2, total_close_line/_p1/_p2 (p1 = first-listed (visitor) row price, p2 = second row price).
SBRO publishes one consensus open/close per game (no per-book detail) and gives the puck line once (treated as close).
Unmatched games written to data/processed/lines_sbro_v1_unmatched.csv."""
import re
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/sbro")
OUT = Path("data/processed/lines_sbro_v1.parquet")
NAME = {"anaheim": "ANA", "arizona": "ARI", "boston": "BOS", "buffalo": "BUF", "calgary": "CGY", "carolina": "CAR",
        "chicago": "CHI", "colorado": "COL", "columbus": "CBJ", "dallas": "DAL", "detroit": "DET", "edmonton": "EDM",
        "florida": "FLA", "losangeles": "LAK", "minnesota": "MIN", "montreal": "MTL", "nyislanders": "NYI",
        "nyrangers": "NYR", "nashville": "NSH", "newjersey": "NJD", "ottawa": "OTT", "philadelphia": "PHI",
        "pittsburgh": "PIT", "sanjose": "SJS", "seattle": "SEA", "seattlekraken": "SEA", "st.louis": "STL",
        "stlouis": "STL", "tampabay": "TBL", "toronto": "TOR", "vancouver": "VAN", "vegas": "VGK",
        "washington": "WSH", "winnipeg": "WPG"}


def parse_season(s):
    h = (RAW / f"nhl-odds-{s}.html").read_text(encoding="utf-8")
    y0 = int(s[:4])
    rows = []
    for r in re.findall(r"<tr>(.*?)</tr>", h, re.S):
        c = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
        if len(c) == 16 and c[0].isdigit():
            rows.append(c)
    out = []
    for a, b in zip(rows[0::2], rows[1::2]):
        assert a[0] == b[0] and int(b[1]) == int(a[1]) + 1, (a[:4], b[:4])
        md = a[0].zfill(4)
        yr = y0 if int(md[:2]) >= 8 else y0 + 1
        f = lambda x: float(x) if x not in ("", "NL") else None
        out.append(dict(season=int(s[:4]) * 10000 + int(s[:4]) + 1, date=f"{yr}-{md[:2]}-{md[2:]}", vh1=a[2], vh2=b[2],
                        t1=NAME.get(re.sub(r"\s", "", a[3]).lower()), t2=NAME.get(re.sub(r"\s", "", b[3]).lower()),
                        raw1=a[3], raw2=b[3], fin1=f(a[7]), fin2=f(b[7]),
                        ml_open1=f(a[8]), ml_open2=f(b[8]), ml_close1=f(a[9]), ml_close2=f(b[9]),
                        pl_line1=f(a[10]), pl_price1=f(a[11]), pl_line2=f(b[10]), pl_price2=f(b[11]),
                        to_line=f(a[12]), to_p1=f(a[13]), to_p2=f(b[13]), to_line2=f(b[12]),
                        tc_line=f(a[14]), tc_p1=f(a[15]), tc_p2=f(b[15]), tc_line2=f(b[14])))
    return out


def main():
    g = pd.read_parquet("data/processed/games.parquet")
    g = g[g.season.isin([20212022, 20222023]) & g.game_type.isin([2, 3])]
    key = {}
    for r in g.itertuples():
        key.setdefault((r.game_date_local, r.home, r.away), []).append(r)
    recs, unm = [], []
    for s in ("2021-22", "2022-23"):
        for o in parse_season(s):
            assert o["to_line"] == o["to_line2"] and o["tc_line"] == o["tc_line2"]
            if o["t1"] is None or o["t2"] is None:
                unm.append({**o, "why": "team name"}); continue
            # vh1 == V (visitor listed first) normally; N = neutral (SBRO lists visitor first as well)
            cand = None
            for d in (o["date"], (pd.Timestamp(o["date"]) - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                      (pd.Timestamp(o["date"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")):
                for (hm, aw, swap) in ((o["t2"], o["t1"], False), (o["t1"], o["t2"], True)):
                    if (d, hm, aw) in key:
                        cand = (key[(d, hm, aw)], swap, d); break
                if cand: break
            if not cand:
                unm.append({**o, "why": "no game"}); continue
            gm, swap, d = cand
            gm = gm[0]
            # side 1 is away unless swap (neutral/mislabelled)
            h, a = ("2", "1") if not swap else ("1", "2")
            hs, as_ = o[f"fin{h}"], o[f"fin{a}"]
            rec = dict(game_id=int(gm.game_id), season=int(gm.season), game_date=gm.game_date_local, home=gm.home, away=gm.away,
                       sbro_date=o["date"], date_shift_days=(pd.Timestamp(d) - pd.Timestamp(o["date"])).days, swapped=swap,
                       final_home_sbro=hs, final_away_sbro=as_,
                       final_matches_nhl=bool(hs == gm.home_score_box and as_ == gm.away_score_box),
                       ml_open_home=o[f"ml_open{h}"], ml_open_away=o[f"ml_open{a}"],
                       ml_close_home=o[f"ml_close{h}"], ml_close_away=o[f"ml_close{a}"],
                       pl_home_line=o[f"pl_line{h}"], pl_home_price=o[f"pl_price{h}"],
                       pl_away_line=o[f"pl_line{a}"], pl_away_price=o[f"pl_price{a}"],
                       total_open_line=o["to_line"], total_close_line=o["tc_line"],
                       total_open_price_row1=o["to_p1"], total_open_price_row2=o["to_p2"],
                       total_close_price_row1=o["tc_p1"], total_close_price_row2=o["tc_p2"],
                       source="sbro", market_note="consensus open/close; PL single (close); ou rows: row1=visitor row, row2=home row")
            recs.append(rec)
    df = pd.DataFrame(recs)
    dup = df.game_id.duplicated(keep=False)
    assert not dup.any(), df[dup]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    if unm:
        pd.DataFrame(unm).to_csv("data/processed/lines_sbro_v1_unmatched.csv", index=False)
    # coverage vs games
    cov = []
    for sn, gg in g.groupby("season"):
        m = df[df.season == sn]
        cov.append(dict(season=sn, nhl_games=len(gg), sbro_rows=len(m), nhl_regular=int((gg.game_type == 2).sum()),
                        matched_regular=int(m.game_id.isin(gg[gg.game_type == 2].game_id).sum()),
                        last_date=m.game_date.max() if len(m) else None, final_match_pct=round(100 * m.final_matches_nhl.mean(), 2) if len(m) else None))
    print(pd.DataFrame(cov).to_string())
    print("parsed", len(recs) + len(unm), "matched", len(recs), "unmatched", len(unm))
    print(df.date_shift_days.value_counts().to_dict(), "swapped", int(df.swapped.sum()))


if __name__ == "__main__":
    main()
