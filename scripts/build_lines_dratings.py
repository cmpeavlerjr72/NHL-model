"""Build data/processed/lines_dratings_v1.parquet from cached DRatings pages (data/raw/dratings/).
Long format, one row per (game, market, book-group, side, column): open / each book close / best / no-vig close.
Only pregame fields exist on completed-game pages; a page showing any in-game marker is REJECTED (L18).
Game ids come from the index rows (uuid -> teams + start) matched to data/processed/games.parquet.
2025-26 (sealed) and later are never included: rows with start_utc >= 2025-07-01 are dropped."""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from nhl_sim import dratings as D  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "dratings"
OUT = ROOT / "data" / "processed" / "lines_dratings_v1.parquet"
WIN_LO, WIN_HI = "2021-09-01", "2025-07-01"
SIDES = {"ml": ("away", "home"), "pl": ("away", "home"), "total": ("over", "under")}
LIVE_RE = re.compile(r"in-?game|live\s+(odds|line|bet)|in-?play|inplay", re.I)


def index_rows():
    seen = {}
    for f in list(RAW.glob("index_full_*.html")) + list(RAW.glob("index_[0-9]*.html")):
        for r in D.parse_index(f.read_text(encoding="utf-8")):
            if WIN_LO <= r["start_utc"][:10] < WIN_HI:
                seen.setdefault(r["uuid"], r)
    return seen


def match_games(idx):
    g = pd.read_parquet(ROOT / "data" / "processed" / "games.parquet")
    g = g[g.season.isin([20212022, 20222023, 20232024, 20242025]) & g.game_type.isin([2, 3])].copy()
    g["t"] = pd.to_datetime(g.puck_drop_utc, utc=True)
    by = {k: v for k, v in g.groupby(["home", "away"])}
    out = {}
    for u, r in idx.items():
        h, a = r["home"], r["away"]
        if r["start_utc"][:10] < "2024-07-01":  # DRatings labels pre-2024 Arizona games "Utah Mammoth" (current name)
            h, a = ("ARI" if h == "UTA" else h), ("ARI" if a == "UTA" else a)
        c = by.get((h, a))
        if c is None:
            continue
        st = pd.Timestamp(r["start_utc"])
        d = (c.t - st).abs()
        if d.min() < pd.Timedelta(hours=36):
            out[u] = int(c.loc[d.idxmin(), "game_id"])
    return out, g


def parse_page(html):
    """-> (rows, status). status 'ok' | 'reject_live' | 'incomplete'."""
    body = re.sub(r"<(script|style).*?</\1>", "", html, flags=re.S | re.I)
    if LIVE_RE.search(re.sub(r"<[^>]+>", " ", body)):
        return [], "reject_live"
    g = D.parse_game(html)
    rows = []
    for mk, tables in g["markets"].items():
        for t in tables:
            if len(t["rows"]) != 2:
                continue
            for side, (label, cells) in zip(SIDES[mk], t["rows"]):
                for head, c in zip(t["heads"], cells):
                    h = head.strip()
                    if h.startswith("Open"):
                        field, book = "open", "open"
                    elif h.startswith("Best"):
                        field, book = "best", "best"
                    elif h.startswith("No-Vig"):
                        field, book = "novig_close", "novig"
                    else:
                        field, book = "close", h
                    line, price = D.cell(c)
                    rows.append(dict(market=mk, group=t["group"], side=side, field=field, book=book, line=line, price=price))
    markets = {r["market"] for r in rows}
    return rows, ("ok" if markets == {"ml", "pl", "total"} else "incomplete")


def build_df():
    idx = index_rows()
    gid, g = match_games(idx)
    recs, stat = [], {}
    for u, r in idx.items():
        f = RAW / f"game_{u}.html"
        if not f.exists():
            continue
        rows, s = parse_page(f.read_text(encoding="utf-8"))
        stat[s] = stat.get(s, 0) + 1
        if s == "reject_live" or u not in gid:
            if u not in gid:
                stat["no_game_match"] = stat.get("no_game_match", 0) + 1
            continue
        for x in rows:
            x.update(uuid=u, game_id=gid[u], start_utc=r["start_utc"], home=r["home"], away=r["away"],
                     dr_team_label_remapped=bool(r["start_utc"][:10] < "2024-07-01" and "UTA" in (r["home"], r["away"])))
        recs += rows
    df = pd.DataFrame(recs)
    assert df.empty or df.start_utc.str[:10].lt(WIN_HI).all()
    return df, idx, gid, g, stat


def main():
    df, idx, gid, g, stat = build_df()
    df.to_parquet(OUT, index=False)
    ng = df.game_id.nunique() if len(df) else 0
    print("index rows in window", len(idx), "matched", len(gid), "pages parsed", stat, "games in parquet", ng, "rows", len(df))
    if ng:
        cov = g.assign(has=g.game_id.isin(df.game_id)).groupby("season").has.agg(["sum", "size"])
        print(cov.to_string())


if __name__ == "__main__":
    main()
