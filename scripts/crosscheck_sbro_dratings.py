"""Cross-check SBRO (2021-23) against DRatings on games both have. Same tolerance logic as crosscheck_espn_dratings.py:
|no-vig home prob difference| stats for ML close/open, % identical lines for total/PL, +-0.5 diff counts.
Reads DRatings straight from the page cache (read-only; does not write lines_dratings_v1.parquet).
Writes data/processed/lines_crosscheck_sbro_dratings_v1.{csv,json}. PARTIAL by construction while the DRatings pull is running."""
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_lines_dratings as B  # noqa: E402
from nhl_sim import dratings as D  # noqa: E402

ROOT = B.ROOT


def mode(xs):
    xs = [x for x in xs if x is not None and x == x]
    return Counter(xs).most_common(1)[0][0] if xs else None


def nv(a, h):
    return D.nov_vig_home(a, h)


def main():
    dr, *_ = B.build_df()
    sb = pd.read_parquet(ROOT / "data/processed/lines_sbro_v1.parquet")
    dr = dr[dr.game_id.isin(sb.game_id)]
    rows = []
    for gid, d in dr.groupby("game_id"):
        s = sb[sb.game_id == gid].iloc[0]
        r = dict(game_id=int(gid), date=s.game_date, season=int(s.season), n_dr_rows=len(d))
        ml = d[d.market == "ml"]
        # DRatings ML close, per book no-vig home prob; median across all books both groups
        probs = []
        for grp in ("offshore", "vegas"):
            a = ml[(ml.group == grp) & (ml.side == "away") & (ml.field == "close")].set_index("book").price
            h = ml[(ml.group == grp) & (ml.side == "home") & (ml.field == "close")].set_index("book").price
            for b in a.index.intersection(h.index):
                if pd.notna(a[b]) and pd.notna(h[b]):
                    probs.append(nv(a[b], h[b]))
        r["dr_ml_home_bookmed"] = st.median(probs) if probs else None
        r["dr_n_books"] = len(probs)
        o = {}
        for grp in ("offshore", "vegas"):
            a = ml[(ml.group == grp) & (ml.side == "away") & (ml.field == "open")].price
            h = ml[(ml.group == grp) & (ml.side == "home") & (ml.field == "open")].price
            if len(a) and len(h) and pd.notna(a.iloc[0]) and pd.notna(h.iloc[0]):
                o[grp] = nv(a.iloc[0], h.iloc[0])
        r["dr_ml_home_open_offshore"] = o.get("offshore")
        r["dr_ml_home_open_vegas"] = o.get("vegas")
        r["sbro_ml_home_nv"] = nv(s.ml_close_away, s.ml_close_home)
        r["sbro_ml_home_open_nv"] = nv(s.ml_open_away, s.ml_open_home)
        tt = d[(d.market == "total") & (d.side == "over")]
        r["dr_total_close_mode"] = mode(tt[tt.field == "close"].line.tolist())
        op = tt[tt.field == "open"].line.dropna().tolist()
        r["dr_total_open_offshore"] = tt[(tt.field == "open") & (tt.group == "offshore")].line.iloc[0] if len(op) else None
        r["sbro_total_close"], r["sbro_total_open"] = s.total_close_line, s.total_open_line
        pl = d[(d.market == "pl") & (d.side == "away") & (d.field == "close")]
        r["dr_pl_away_close_mode"] = mode(pl.line.tolist())
        r["sbro_pl_away"] = s.pl_away_line
        rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "data/processed/lines_crosscheck_sbro_dratings_v1.csv", index=False)
    out = {"n_games_both": len(df), "by_season": {str(k): int(v) for k, v in df.groupby("season").size().items()},
           "sbro_games_total": {str(k): int(v) for k, v in sb.groupby("season").size().items()}}
    for col, ref in (("dr_ml_home_bookmed", "sbro_ml_home_nv"), ("dr_ml_home_open_offshore", "sbro_ml_home_open_nv"),
                     ("dr_ml_home_open_vegas", "sbro_ml_home_open_nv")):
        x = df.dropna(subset=[col, ref])
        diff = (x[col] - x[ref]).abs()
        out[f"{col}_vs_{ref}"] = dict(n=len(x), mean=diff.mean(), median=diff.median(), p95=diff.quantile(.95), max=diff.max(),
                                      mean_signed=(x[col] - x[ref]).mean(), argmax_game=int(x.loc[diff.idxmax(), "game_id"]) if len(x) else None,
                                      pct_within_0_02=float((diff <= 0.02).mean() * 100))
    for a, b in (("dr_total_close_mode", "sbro_total_close"), ("dr_total_open_offshore", "sbro_total_open"),
                 ("dr_pl_away_close_mode", "sbro_pl_away")):
        x = df.dropna(subset=[a, b])
        out[f"{a}=={b}"] = dict(n=len(x), pct_identical=float((x[a] == x[b]).mean() * 100) if len(x) else None,
                                diff_counts={str(k): int(v) for k, v in (x[a] - x[b]).value_counts().sort_index().items()})
    # PL sign: SBRO away line sign vs DR away line (both are the away side)
    print(json.dumps(out, indent=1, default=float))
    (ROOT / "data/processed/lines_crosscheck_sbro_dratings_v1.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
