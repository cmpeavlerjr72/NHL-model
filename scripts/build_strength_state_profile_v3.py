"""SS-R3 step 1: season-phase profile + de-seasonalised as-of league level, written as `_v3` tables per fold
(v2 untouched):  data/processed/strength_state/profile_v3_f{1,2}.json, league_level_v3_f{1,2}.parquet.
Fold 1 profile uses 2021-22 and 2022-23 only; fold 2 uses 2021-22 .. 2023-24. Levels for k in {15, 50, 150}."""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import PROCESSED, load_games  # noqa: E402
from nhl_sim.strength_state.seasonality import BINS, asof_level_adj, estimate_profile, game_bins  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

OUT = PROCESSED / "strength_state"
KS = (15, 50, 150)
FOLDS = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}


def main():
    long = pd.read_parquet(OUT / "team_game_v2.parquet")
    games = load_games(sorted(long.season.unique()), columns=["game_id", "game_type", "game_date_local"])
    gbin = game_bins(long, games)
    for f, tr in FOLDS.items():
        p = estimate_profile(long, gbin, tr)
        lv = asof_level_adj(long, gbin, p, KS)
        assert_pregame(lv)
        lv.to_parquet(OUT / f"league_level_v3_f{f}.parquet", index=False)
        (OUT / f"profile_v3_f{f}.json").write_text(json.dumps(
            {"fold": f, "train_seasons": tr, "bins": BINS, "p": [float(x) for x in p]}, indent=1))
        print("fold", f, {b: round(float(x), 4) for b, x in zip(BINS, p)})
        for s in sorted(lv.season.unique()):
            m = lv[lv.season == s]
            print("  ", s, {k: round(float(m[f"level_k{k}"].mean()), 4) for k in KS})


if __name__ == "__main__":
    main()
