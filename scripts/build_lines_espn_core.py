"""Build data/processed/lines_espn_core_v1.parquet from data/raw/espn_core_odds/. Fails on ambiguous provider sets."""
import json
import sys
from collections import Counter

import pandas as pd

from nhl_sim.clients import espn_core_odds as C
from nhl_sim.lines_espn_core import parse_event, vig_outliers

OUT = C.ROOT / "data" / "processed" / "lines_espn_core_v1.parquet"


def main():
    m = C.event_map()
    rows, live_ct, live_names, no_odds, missing = [], 0, Counter(), [], 0
    for r in m.itertuples():
        p = C.RAW / f"{r.event_id}.json"
        if not p.exists():
            missing += 1
            continue
        rr, info = parse_event(json.loads(p.read_text(encoding="utf-8")), r.game_id, r.season)
        live_ct += info["n_live_dropped"]
        live_names.update(info["live_names"])
        if not rr:
            no_odds.append(r.game_id)
        rows += rr
    df = pd.DataFrame(rows)
    out, series = vig_outliers(df)
    bad = set(zip(out.game_id, out.provider))
    # flag (not drop): ML rows whose close two-way implied-prob sum is outside [1.00, 1.10] are unusable as a close
    df["close_ml_vig_ok"] = [(g, p) not in bad if mk == "ml" else None for g, p, mk in zip(df.game_id, df.provider, df.market)]
    df.to_parquet(OUT, index=False)
    print(f"rows {len(df)}, games with rows {df.game_id.nunique()}, raw missing {missing}, games without pregame item {len(no_odds)}")
    print(f"live items dropped {live_ct}: {dict(live_names)}")
    print("pregame providers by season:\n", df.groupby("season").provider.value_counts().to_string())
    print(f"vig outliers {len(out)} of {len(series)} game x provider close ML pairs")
    print(out.assign(season=out.game_id.astype(str).str[:4]).groupby(["season", "provider"]).size().to_string())
    print("vig_sum range of outliers", out.vig_sum.min(), out.vig_sum.max(), "; series min/max", series.vig_sum.min(), series.vig_sum.max())
    print("ESPN BET outliers:", (out.provider == "ESPN BET").sum(), "; ESPN BET pairs:", (series.provider == "ESPN BET").sum())
    print(series.assign(season=series.game_id.astype(str).str[:4]).groupby("season").size().to_string())
    ml = df[df.market == "ml"].merge(m[["game_id", "game_type"]], on="game_id")
    cov = []
    for (s, mk), g in df.merge(m[["game_id", "game_type"]], on="game_id").groupby(["season", "market"]):
        n_all = (m.season == s).sum()
        # ESPN BET (id 58) coverage and any-provider coverage
        for label, gg in (("any", g), ("ESPN BET", g[g.provider_id == "58"])):
            o = gg[gg.open_price.notna()].game_id.nunique()
            c = gg[gg.close_price.notna()].game_id.nunique()
            cov.append({"season": s, "market": mk, "provider": label, "games": n_all,
                        "pct_open": round(100 * o / n_all, 1), "pct_close": round(100 * c / n_all, 1)})
    cov = pd.DataFrame(cov)
    print(cov.to_string(index=False))
    cov.to_csv(C.ROOT / "data" / "processed" / "lines_espn_core_v1_coverage.csv", index=False)
    out.to_csv(C.ROOT / "data" / "processed" / "lines_espn_core_v1_vig_outliers.csv", index=False)


if __name__ == "__main__":
    sys.exit(main())
