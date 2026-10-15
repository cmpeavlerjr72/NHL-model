"""Cross-check DRatings (cached sample pages) against ESPN core lines on the same 2024-25 games."""
import json
import statistics as st
from collections import Counter
from pathlib import Path

import pandas as pd

from nhl_sim import dratings as D
from nhl_sim.clients import espn_core_odds as C

RAW = C.ROOT / "data" / "raw" / "dratings"
OUTCSV = C.ROOT / "data" / "processed" / "lines_crosscheck_espn_dratings_v1.csv"


def mode(xs):
    xs = [x for x in xs if x is not None]
    return Counter(xs).most_common(1)[0][0] if xs else None


def prices(table_row_cells, with_line=False):
    return [D.cell(c) for c in table_row_cells]


def dr_game(html):
    g = D.parse_game(html)
    res = {"start_utc": g["start_utc"], "title": g["title"]}
    # ML: rows[0] = away, rows[1] = home. cells: open, 5 books, best, novig
    for mk in ("ml", "pl", "total"):
        for t in g["markets"][mk]:
            grp = t["group"]
            if len(t["rows"]) < 2:
                continue
            a = [D.cell(c) for c in t["rows"][0][1]]
            h = [D.cell(c) for c in t["rows"][1][1]]
            res[(mk, grp)] = (a, h)  # each cell list: [open, b1..b5, best, novig] of (line, price)
    return res


def main():
    g = pd.read_parquet(C.ROOT / "data" / "processed" / "games.parquet")
    g = g[(g.season == 20242025) & g.game_type.isin([2, 3])].copy()
    g["t"] = pd.to_datetime(g.puck_drop_utc, utc=True)
    L = pd.read_parquet(C.ROOT / "data" / "processed" / "lines_espn_core_v1.parquet")
    L = L[(L.provider_id == "58")]
    rows = []
    # map uuid -> index row (teams)
    idx = {}
    for f in RAW.glob("index_*.html"):
        for r in D.parse_index(f.read_text(encoding="utf-8")):
            idx[r["uuid"]] = r
    for f in sorted(RAW.glob("game_*.html")):
        uuid = f.stem[5:]
        r = idx.get(uuid)
        if not r or not r["home"]:
            continue
        st_ = pd.Timestamp(r["start_utc"])
        c = g[(g.home == r["home"]) & (g.away == r["away"]) & ((g.t - st_).abs() < pd.Timedelta(hours=36))]
        if c.empty:
            rows.append({"uuid": uuid, "note": "no game match"}); continue
        gm = c.iloc[(c.t - st_).abs().argsort()[:1]].iloc[0]
        gid = int(gm.game_id)
        e = L[L.game_id == gid]
        d = dr_game(f.read_text(encoding="utf-8"))
        row = {"uuid": uuid, "game_id": gid, "date": str(gm.game_date_local), "game_type": int(gm.game_type), "note": ""}
        if e.empty:
            row["note"] = "no espn"; rows.append(row); continue

        def ev(mk, side, col):
            x = e[(e.market == mk) & (e.side_or_line == side)]
            return x[col].iloc[0] if len(x) and pd.notna(x[col].iloc[0]) else None
        # ML close
        ea, eh = ev("ml", "away", "close_price"), ev("ml", "home", "close_price")
        if ea is not None and eh is not None:
            row["espn_ml_home_nv"] = D.nov_vig_home(ea, eh)
        oa, oh = ev("ml", "away", "open_price"), ev("ml", "home", "open_price")
        if oa is not None and oh is not None:
            row["espn_ml_home_open_nv"] = D.nov_vig_home(oa, oh)
        for grp in ("offshore", "vegas"):
            k = ("ml", grp)
            if k in d:
                a, h = d[k]
                try:
                    row[f"dr_ml_home_nv_{grp}"] = D.american_to_prob(h[-1][1]) if h[-1][1] is not None else None  # novig col
                    row[f"dr_ml_home_open_nv_{grp}"] = D.nov_vig_home(a[0][1], h[0][1])
                    row[f"dr_ml_home_bookmed_{grp}"] = st.median([D.nov_vig_home(x[1], y[1]) for x, y in zip(a[1:6], h[1:6])
                                                                  if x[1] is not None and y[1] is not None])
                except Exception as ex:
                    row["note"] += f"ml_{grp}:{type(ex).__name__} "
        # total: Over row cells[1:6] book lines
        tl = []
        for grp in ("offshore", "vegas"):
            if ("total", grp) in d:
                tl += [x[0] for x in d[("total", grp)][0][1:6]]
        row["dr_total_close_mode"] = mode(tl)
        row["dr_total_close_novig_col"] = d[("total", "offshore")][0][-1][0] if ("total", "offshore") in d else None
        row["dr_total_open"] = d[("total", "offshore")][0][0][0] if ("total", "offshore") in d else None
        row["espn_total_close"] = ev("total", "over", "close_line")
        row["espn_total_open"] = ev("total", "over", "open_line")
        pl = []
        for grp in ("offshore", "vegas"):
            if ("pl", grp) in d:
                pl += [x[0] for x in d[("pl", grp)][0][1:6]]
        row["dr_pl_away_close_mode"] = mode(pl)
        row["dr_pl_away_open"] = d[("pl", "offshore")][0][0][0] if ("pl", "offshore") in d else None
        row["espn_pl_away_close"] = ev("pl", "away", "close_line")
        row["espn_pl_away_open"] = ev("pl", "away", "open_line")
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUTCSV, index=False)
    ok = df[df.get("game_id").notna()] if "game_id" in df else df
    print(f"dratings pages {len(rows)}, matched to games {len(ok)}, with espn rows {ok.espn_ml_home_nv.notna().sum()}")
    print(ok.groupby(ok.date.str[:7]).size().to_string())
    out = {}
    for col in ("dr_ml_home_nv_offshore", "dr_ml_home_nv_vegas", "dr_ml_home_bookmed_offshore", "dr_ml_home_bookmed_vegas"):
        x = ok.dropna(subset=["espn_ml_home_nv", col])
        diff = (x[col] - x.espn_ml_home_nv).abs()
        out[col] = dict(n=len(x), mean=diff.mean(), median=diff.median(), p95=diff.quantile(.95), max=diff.max(), argmax=x.loc[diff.idxmax(), "uuid"] if len(x) else None)
    for col in ("dr_ml_home_open_nv_offshore", "dr_ml_home_open_nv_vegas"):
        x = ok.dropna(subset=["espn_ml_home_open_nv", col])
        diff = (x[col] - x.espn_ml_home_open_nv).abs()
        out[col + "_vs_espn_open"] = dict(n=len(x), mean=diff.mean(), median=diff.median(), max=diff.max())
    for a, b in (("dr_total_close_mode", "espn_total_close"), ("dr_total_close_novig_col", "espn_total_close"),
                 ("dr_total_open", "espn_total_open"), ("dr_pl_away_close_mode", "espn_pl_away_close"),
                 ("dr_pl_away_open", "espn_pl_away_open")):
        x = ok.dropna(subset=[a, b])
        out[f"{a}=={b}"] = dict(n=len(x), pct_identical=float((x[a] == x[b]).mean() * 100) if len(x) else None)
    x = ok.dropna(subset=["dr_total_close_mode", "espn_total_close"])
    out["total_close_diff_counts(dr-espn)"] = {str(k): int(v) for k, v in (x.dr_total_close_mode - x.espn_total_close).value_counts().sort_index().items()}
    out["total_close_by_month_identical_pct"] = {k: round(float(v) * 100, 1) for k, v in (x.dr_total_close_mode == x.espn_total_close).groupby(x.date.str[:7]).mean().items()}
    x = ok.dropna(subset=["dr_total_open", "espn_total_open"])
    out["total_open_diff_counts(dr-espn)"] = {str(k): int(v) for k, v in (x.dr_total_open - x.espn_total_open).value_counts().sort_index().items()}
    x = ok.dropna(subset=["dr_total_close_mode", "dr_total_open", "espn_total_close", "espn_total_open"])
    out["total_n_where_dr_open_eq_espn_open_but_close_differs"] = int(((x.dr_total_open == x.espn_total_open) & (x.dr_total_close_mode != x.espn_total_close)).sum())
    out["n_games_by_month"] = {k: int(v) for k, v in ok.groupby(ok.date.str[:7]).size().items()}
    out["n_regular_season"] = int((ok.game_type == 2).sum())
    print(json.dumps(out, indent=1, default=float))
    (C.ROOT / "data" / "processed" / "lines_crosscheck_espn_dratings_v1.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
