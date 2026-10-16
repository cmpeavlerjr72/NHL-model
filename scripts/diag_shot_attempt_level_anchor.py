"""SA-R1 diagnostic (fold 1 ONLY; not an arm, no selection effect): is the -5% level bias of every SA-R1 arm the
anchoring of the SS-R3 league level?

The SS-R3 level is log(shrunk season-to-date rate / r_prev), r_prev = the PREVIOUS season's final rate. Used as a
fixed offset in a model pooled over several training seasons, its reference changes every season, so the cell
effects learn a blend of past season rates and a test season inherits the product of earlier season-to-season
ratios. An anchored level adds the per-season constant log(r_prev_s / r_first), i.e. it is a log ratio vs ONE fixed
reference (the first data season's de-seasonalised final rate), using only completed earlier seasons.

This script refits A0 and A2 on fold 1 (train 2021-22 + 2022-23, test 2023-24) with the frozen SA-R1 params under
both levels and prints predicted / actual. Fold 2 is not touched.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.shot_attempt import models as S  # noqa: E402
from nhl_sim.shot_attempt.tables import ST_NAMES  # noqa: E402
from nhl_sim.strength_state.seasonality import game_bins  # noqa: E402

F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024


def main():
    fz = json.loads(Path("docs/models/shot_attempt/sa_r1_frozen_params.json").read_text())
    p = np.array(json.loads((S.SA / "profile_v1_f1.json").read_text())["p"])
    tgm = pd.read_parquet(S.SA / "team_game_v1.parquet")
    games = load_games(F1_TRAIN + [F1_TEST], columns=["game_id", "game_type", "game_date_local"])
    tgm = tgm[tgm.season.isin(F1_TRAIN + [F1_TEST])]
    gb = game_bins(tgm, games)
    tgm = tgm.assign(adj=tgm.att / np.exp(p[tgm.game_id.map(gb).to_numpy()]))
    rate = tgm.groupby("season").apply(lambda d: d.adj.sum() / (d.minutes.sum() / 60.0))
    first = rate.index.min()
    const = {s: (0.0 if s == first else float(np.log(rate[sorted(rate.index)[sorted(rate.index).index(s) - 1]]
                                                      / rate[first]))) for s in rate.index}
    rows = S.load_rows(F1_TRAIN + [F1_TEST])
    r = S.attach_features(rows, fz["w"], fz["prior_strength_min"], fz["k"], 1)
    out = {"deseasonalised_final_rate_per_team_hour": rate.round(4).to_dict(), "anchor_constant": const}
    for nm, rr in (("SS-R3 level (SA-R1 literal)", r),
                   ("anchored level (diagnostic)", r.assign(level=r.level + r.season.map(const)))):
        tr, te = rr[rr.season.isin(F1_TRAIN)], rr[rr.season == F1_TEST]
        for arm in ("A0", "A2"):
            m = S.fit_glm(tr, arm)
            mu = S.predict_glm(m, te)
            out[f"{nm} | {arm} | fold-1 pred/actual - 1"] = float(mu.sum() / te.y.sum() - 1)
            out[f"{nm} | {arm} | fold-1 LL/game"] = float(S.per_game_ll(te, mu).mean())
            st = te.assign(mu=mu).groupby("st")[["mu", "y"]].sum()
            out[f"{nm} | {arm} | fold-1 pred/actual - 1 by state"] = {
                ST_NAMES[i]: round(float(v.mu / v.y - 1), 4) for i, v in st.iterrows()}
    print(json.dumps(out, indent=1))
    Path("results/shot_attempt_r1/diag_level_anchor_fold1.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
