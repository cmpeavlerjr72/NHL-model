"""INV-14: independent finals check. NHL feed (v1, 3 views of one feed) vs ESPN scoreboard (independent).
Writes data/reference/verified_finals_v2.parquet and prints mismatches. ESPN rows in the sealed 2025-26 date
window are dropped by date BEFORE their scores are read."""
import gzip
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_verified_finals  # noqa: E402

RAW = Path("data/raw/espn_scoreboard")
SEALED_START, SEALED_END = date(2025, 9, 1), date(2026, 8, 31)  # 2025-26 window incl. preseason/playoffs
ABBR = {"NJ": "NJD", "TB": "TBL", "SJ": "SJS", "LA": "LAK", "WSH": "WSH", "UTAH": "UTA"}


def espn_rows():
    rows = []
    for f in sorted(RAW.glob("*.json.gz")):
        d = datetime.strptime(f.name[:8], "%Y%m%d").date()
        if SEALED_START <= d <= SEALED_END:
            continue
        j = json.loads(gzip.decompress(f.read_bytes()))
        for e in j.get("events", []):
            t = e["status"]["type"]
            comp = e["competitions"][0]["competitors"]
            h = next(c for c in comp if c["homeAway"] == "home")
            a = next(c for c in comp if c["homeAway"] == "away")
            sd = t["shortDetail"]
            es = "SO" if "SO" in sd and sd.startswith("Final") else "OT" if sd.startswith("Final/") else \
                "REG" if sd == "Final" else None
            rows.append(dict(espn_id=e["id"], espn_query_date=d, espn_utc=e["date"], espn_status=t["name"],
                             espn_detail=sd, espn_season_slug=e["season"]["slug"],
                             espn_home=ABBR.get(h["team"]["abbreviation"], h["team"]["abbreviation"]),
                             espn_away=ABBR.get(a["team"]["abbreviation"], a["team"]["abbreviation"]),
                             espn_home_score=int(h["score"]), espn_away_score=int(a["score"]), espn_end_state=es))
    return pd.DataFrame(rows)


def main():
    v1 = load_verified_finals("v1")
    es = espn_rows()
    es = es[es.espn_status == "STATUS_FINAL"].copy()
    es["_used"] = False
    out = []
    for r in v1.itertuples():
        gd = datetime.strptime(r.game_date_local, "%Y-%m-%d").date()
        c = es[(es.espn_home == r.home) & (es.espn_away == r.away) & ~es._used]
        c = c[(c.espn_query_date - gd).apply(lambda x: abs(x.days) <= 1)]
        if len(c):
            c = c.assign(_dd=(c.espn_query_date - gd).apply(lambda x: abs(x.days))).sort_values("_dd")
            m = c.iloc[0]
            es.loc[m.name, "_used"] = True
            out.append(m.drop(["_dd", "_used"], errors="ignore").to_dict())
        else:
            out.append({})
    e = pd.DataFrame(out, index=v1.index)
    df = pd.concat([v1, e], axis=1)
    df["espn_matched"] = df.espn_id.notna()
    df["score_agree"] = (df.espn_home_score == df.home_score) & (df.espn_away_score == df.away_score)
    df["end_agree"] = df.espn_end_state == df.end_state
    nhl = ["nhl_schedule", "nhl_boxscore", "nhl_pbp"]
    srcs = []
    for r in df.itertuples():
        s = list(nhl) if r.verified else []
        if r.espn_matched and r.score_agree and r.end_agree:
            s.append("espn")
        srcs.append("|".join(s))
    df["verified_sources"] = srcs
    df["verified_v2"] = df.verified & df.espn_matched & df.score_agree & df.end_agree
    df["espn_home_score"] = df.espn_home_score.astype("Int64")
    df["espn_away_score"] = df.espn_away_score.astype("Int64")
    df = df.drop(columns=["espn_query_date"]).assign(espn_query_date=e.espn_query_date.astype("string"))
    df.to_parquet("data/reference/verified_finals_v2.parquet")
    print("games", len(df), "matched", int(df.espn_matched.sum()), "score_agree", int(df.score_agree.sum()),
          "end_agree", int(df.end_agree.sum()), "verified_v2", int(df.verified_v2.sum()))
    leftover = es[~es._used & (es.espn_season_slug != "preseason")]
    leftover.drop(columns="_used").to_csv("data/reference/_espn_unmatched_tmp.csv", index=False)
    print("unmatched ESPN non-preseason finals", len(leftover))


if __name__ == "__main__":
    main()
