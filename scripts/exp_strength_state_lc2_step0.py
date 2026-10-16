"""LC-2 step 0 (INV-33): level constructions L1, L2c, L2a, L2b, O on the SS-R3 profile; level-only H0'' per-season parity
on both folds' training seasons, fold-1 test (2023-24) bias by month (diagnostic), selection rule as written.
Writes data/processed/strength_state/league_level_v5_f{1,2}.parquet (all columns) and
results/strength_state_lc2/step0.json."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import PROCESSED, load_games  # noqa: E402
from nhl_sim.league_level_lc1 import lc1_level  # noqa: E402
from nhl_sim.league_level_lc2 import lc2_level  # noqa: E402
from nhl_sim.strength_state import models_r2 as R  # noqa: E402
from nhl_sim.strength_state.seasonality import BINS, game_bins  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

SS = PROCESSED / "strength_state"
RES = Path("results/strength_state_lc2")
W, B = 1.0, 1800
FOLDS = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
GENUINE = {1: [20222023], 2: [20222023, 20232024]}
SPECS = {"L2c": ("L2c", None), "O": ("O", None)}
for k in (50, 200, 800):
    SPECS[f"L2a_k{k}"] = ("L2a", k)
for hl in (14, 30, 60):
    SPECS[f"L2b_hl{hl}"] = ("L2b", (hl, 5))
FAMILY = {"L1": 0, "L2c": 0, "L2a": 1, "L2b": 2}      # simplicity order: L2c < L2a < L2b


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def fam(n):
    return n.split("_")[0] if n.startswith("L2") else n


def main():
    long = pd.read_parquet(SS / "team_game_v2.parquet")
    games = load_games(sorted(long.season.unique()), columns=["game_id", "game_type", "game_date_local"])
    gbin = game_bins(long, games)
    month = pd.to_datetime(games.drop_duplicates("game_id").set_index("game_id").game_date_local).dt.month
    out = {}
    for fold, (train, test) in FOLDS.items():
        print(now(), "fold", fold, flush=True)
        p = np.array(json.loads((SS / f"profile_v3_f{fold}.json").read_text())["p"])
        l1 = lc1_level(long, gbin, p, [5])
        lv = lc2_level(long, gbin, p, SPECS)
        assert_pregame(lv)
        lv["L1"] = l1.set_index("game_id").loc[lv.game_id, "level_k5"].to_numpy()
        lv.to_parquet(SS / f"league_level_v5_f{fold}.parquet", index=False)
        rows = R.load_rows(train + [test])
        base = R.attach_features(rows, W, B, 15, profile_fold=fold).drop(columns=["level"])
        base = base.merge(lv[["game_id", "p"]], on="game_id", how="left", validate="many_to_one")
        base["bin"] = base.game_id.map(gbin).to_numpy()
        res = {}
        for name in ["L1"] + list(SPECS):
            r = base.assign(level=base.game_id.map(lv.set_index("game_id")[name]).to_numpy() + base.p.to_numpy())
            assert not r.level.isna().any()
            tr, te = r[r.season.isin(train)], r[r.season == test]
            m = R.fit_glm(tr, "H0")
            mu_tr = R.predict_glm(m, tr)
            d = pd.DataFrame({"s": tr.season.to_numpy(), "mu": mu_tr, "y": tr.y.to_numpy(float)}).groupby("s").sum()
            par = (d.mu / d.y - 1).to_dict()
            g = [s for s in GENUINE[fold]]
            wm = float(d.loc[g, "mu"].sum() / d.loc[g, "y"].sum() - 1)
            entry = {"parity": {int(s): float(v) for s, v in par.items()},
                     "max_abs_genuine": float(max(abs(par[s]) for s in g)), "wmean_genuine": wm}
            if fold == 1:
                mu_te = R.predict_glm(m, te)
                entry["test_overall"] = float(mu_te.sum() / te.y.sum() - 1)
                t = pd.DataFrame({"b": te.bin.to_numpy(), "mu": mu_te, "y": te.y.to_numpy(float)}).groupby("b").sum()
                entry["test_by_bin"] = {BINS[int(b)]: float(v) for b, v in (t.mu / t.y - 1).items()}
            res[name] = entry
            print(now(), fold, name, {int(s): round(v * 100, 2) for s, v in par.items()},
                  "maxG %.2f%%" % (entry["max_abs_genuine"] * 100), flush=True)
        out[fold] = res
    (RES / "step0.json").write_text(json.dumps(out, indent=1))
    print(now(), "done")


if __name__ == "__main__":
    main()
