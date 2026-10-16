"""SB-R4 step 0 (docs/models/block/experiments.md SB-R4): per-season rating coefficients for the incumbent SB-R1 ratings,
Rr and Ra. B1-style fits (SB-R1 design: B0 + score + home + rest + arena factor + the two ratings), unpenalised, level M1_K500,
on each training season alone and on the fold-1 / fold-2 training sets, with model-based and game-cluster SEs. Training seasons
2021-22..2023-24 only; 2024-25 is not read. Report only: no decision.
-> results/block_sb_r4/step0.json, docs/tests/block_sb_r4_step0_2026-10-16.md
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.block import data as D  # noqa: E402
from nhl_sim.block import models as BM  # noqa: E402
from nhl_sim.block import response as R  # noqa: E402

RES = Path("results/block_sb_r4")
OUTMD = Path("docs/tests/block_sb_r4_step0_2026-10-16.md")
SEAS = [20212022, 20222023, 20232024]
F = {1: [20212022, 20222023], 2: SEAS}
IR = {"own_r": 19, "opp_r": 20, "arena_f": 21}
RT = {"incumbent": "ratings_v1", "Rr": "ratings_r4_Rr", "Ra": "ratings_r4_Ra"}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def md(df, f=".4f"):
    return df.to_markdown(floatfmt=f)


def main():
    RES.mkdir(parents=True, exist_ok=True)
    a = D.load_attempts(SEAS)
    assert set(a.season.unique()) == set(SEAS)
    games = pd.read_parquet(D.OUT / "games_v1.parquet")
    af = pd.read_parquet(D.OUT / "arena_v1.parquet")
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    L = L[L.construction == "M1_K500"]
    rows, cors, sds = [], [], []
    for cn, f in RT.items():
        rt = pd.read_parquet(D.OUT / f"{f}.parquet")
        r = D.assemble(a, games, rt, af, 0.7, 1000).reset_index(drop=True)
        gated = (r.grp <= 2).to_numpy()
        for nm, ss in (("fold-1 train (21-22, 22-23)", F[1]), ("fold-2 train (21-22..23-24)", F[2]),
                       *((f"season {s} alone", [s]) for s in SEAS)):
            m = r.season.isin(ss).to_numpy()
            # level offset share table: always the fold-2 training pool for single seasons, the fold's pool otherwise
            pool = F[1] if nm.startswith("fold-1") else F[2]
            off = D.row_offset(r, L, D.share_table(r[r.season.isin(pool)]))
            X = BM.design_b1(r[m])
            fit = R.fit_se(X, r.y.to_numpy()[m], off[m], cluster=r.game_id.to_numpy()[m])
            for v in ("own_r", "opp_r", "arena_f"):
                i = IR[v]
                sd = float(r.loc[m, v].std())
                rows.append(dict(construction=cn, fit=nm, feature=v, coef=fit["coef"][i], se_model=fit["se_model"][i],
                                 se_cluster=fit["se_cluster"][i], rating_sd=sd, coef_x_sd=fit["coef"][i] * sd))
            print(now(), cn, nm, "done", flush=True)
        m2 = r.season.isin(F[2]).to_numpy() & gated
        cors.append(dict(construction=cn, corr_own_r_arena_f=float(np.corrcoef(r.own_r[m2], r.arena_f[m2])[0, 1]),
                         corr_opp_r_arena_f=float(np.corrcoef(r.opp_r[m2], r.arena_f[m2])[0, 1]),
                         sd_own_r=float(r.own_r[m2].std()), sd_opp_r=float(r.opp_r[m2].std())))
    CO = pd.DataFrame(rows)
    CR = pd.DataFrame(cors)
    # flatness across the three single seasons: weighted linear trend of coef on season index (cluster SEs) and chi2 of equality
    fl = []
    for cn in RT:
        for v in ("own_r", "opp_r"):
            s = CO[(CO.construction == cn) & (CO.feature == v) & CO.fit.str.startswith("season")].sort_values("fit")
            c, se = s.coef.to_numpy(), s.se_cluster.to_numpy()
            w = 1 / se ** 2
            mu = (w * c).sum() / w.sum()
            chi2 = float((w * (c - mu) ** 2).sum())
            t = np.arange(3.0)
            tb = float(np.polyfit(t, c, 1, w=1 / se)[0])
            tse = float(1 / np.sqrt((w * (t - (w * t).sum() / w.sum()) ** 2).sum()))
            fl.append(dict(construction=cn, feature=v, coef_21_22=c[0], coef_22_23=c[1], coef_23_24=c[2], chi2_equal_2df=chi2,
                           trend_per_season=tb, trend_se=tse, trend_z=tb / tse))
    FL = pd.DataFrame(fl)
    out = dict(coef=CO.to_dict("records"), corr=CR.to_dict("records"), flat=FL.to_dict("records"))
    (RES / "step0.json").write_text(json.dumps(out, indent=1, default=float))
    L_ = ["# SB-R4 step 0: per-season rating coefficients, incumbent vs Rr vs Ra (Lane B4, 2026-10-16)", "",
          "Spec: `docs/models/block/experiments.md` SB-R4 step 0. Seasons 2021-22..2023-24 only; 2024-25 not read. Ratings b 1000, w 0.7; "
          "level M1_K500; B1 design (SB-R1) with the arena factor as a feature, unpenalised fits. 'for' = shooting team's as-of "
          "blocked-against rating (`own_r`), 'against' = defending team's as-of blocks-for rating (`opp_r`). Raw rating units. "
          f"Generated {now()} by `scripts/diag_block_sbr4_step0.py`. Report only, no decision.", "",
          "## Coefficients (SE model-based and game-cluster)", "", md(CO.set_index(["construction", "fit", "feature"]), ".4f"), "",
          "## Flatness across the three single seasons", "",
          "chi2 = inverse-variance-weighted heterogeneity (2 df; > 5.99 rejects equality at 5%); trend = weighted slope of the "
          "coefficient on season index, with its SE and z. Each season's cluster SE is wide, so a flat verdict is "
          "only as strong as these SEs.", "", md(FL.set_index(["construction", "feature"]), ".4f"), "",
          "## Correlation of the as-of ratings with the arena factor (fold-2 train, gated rows)", "", md(CR.set_index("construction"), ".4f"), ""]
    OUTMD.write_text("\n".join(L_), encoding="utf-8")
    print("\n".join(L_), flush=True)


if __name__ == "__main__":
    main()
