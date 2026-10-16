"""G-R1 step 0 (docs/models/goal/experiments.md G-R1, L35): per-season rating-response trend test. Committed before any arm
is fit.

For each training season alone (2021-22, 2022-23, 2023-24; 2024-25 is not read), an unpenalised C1-style logistic (C0
offset from the fold-2 training table + level E, strength-group intercepts, score, home, b2b own / opp, arena distance
factor as a separate covariate, goalie as-of save rating and shooting team's as-of finishing rating, both free) on every
in-scope SOG row of that season. Coefficients with model-based and game-cluster SEs; trend = inverse-variance-weighted
slope of the coefficient on season index (cluster SEs), with its z. The read is the reference cell (goalie b 3000 w 0.7,
team b 3000 w 0.7, mid-grid, fixed before running); every other grid cell's trend z is shown as a robustness table.
-> results/goal_g_r1/step0.json, docs/tests/goal_g_r1_step0_2026-10-16.md
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.block.response import fit_se  # noqa: E402
from nhl_sim.goal import data as D  # noqa: E402
from nhl_sim.goal import models as GM  # noqa: E402

RES = Path("results/goal_g_r1")
OUTMD = Path("docs/tests/goal_g_r1_step0_2026-10-16.md")
SEAS = [20212022, 20222023, 20232024]
REF_G, REF_T = "b3000_w0.7", "b3000_w0.7"


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def trend(c, se):
    w = 1 / se ** 2
    t = np.arange(len(c), dtype=float)
    tb = float(np.polyfit(t, c, 1, w=1 / se)[0])
    tse = float(1 / np.sqrt((w * (t - (w * t).sum() / w.sum()) ** 2).sum()))
    mu = (w * c).sum() / w.sum()
    return tb, tse, tb / tse, float((w * (c - mu) ** 2).sum())


def main():
    t0 = time.time()
    sel = json.loads((RES / "step1.json").read_text())["selected"]
    rows = pd.read_parquet(RES / "rows_v1.parquet")
    r = rows[rows.season.isin(SEAS)].reset_index(drop=True)
    assert set(r.season.unique()) == set(SEAS)
    T = np.load(D.OUT / "cell_table_f2.npy")
    lv = pd.read_parquet(D.OUT / "level_v1_f2.parquet")
    off = D.c0_logit(r, T, lv[lv.construction == sel])
    RG = pd.read_parquet(D.OUT / "ratings_goalie_v1_f2.parquet")
    RT = pd.read_parquet(D.OUT / "ratings_team_v1_f2.parquet")
    gcells = [c for c in RG.columns if c.startswith("b")]
    tcells = [c for c in RT.columns if c.startswith("b")]
    res = []

    def run(gc, tc, full):
        x = r.assign(g_r=D.attach_rating(r, RG.rename(columns={gc: "r"}), "goalie_id"),
                     t_r=D.attach_rating(r, RT.rename(columns={tc: "r"}), "team_id"))
        out = []
        for s in SEAS:
            m = (x.season == s).to_numpy()
            X = GM.design_free(x[m])
            f = fit_se(X, x.y.to_numpy()[m], off[m], cluster=x.game_id.to_numpy()[m])
            for nm, i in (("goalie", -2), ("team", -1), ("arena_f", GM.I_ARENA)):
                out.append(dict(g_cell=gc, t_cell=tc, season=s, feature=nm, coef=float(f["coef"][i]),
                                se_model=float(f["se_model"][i]), se_cluster=float(f["se_cluster"][i]),
                                rating_sd=float(x[["g_r", "t_r", "arena_f"]].to_numpy()[m][:, {"goalie": 0, "team": 1, "arena_f": 2}[nm]].std())))
        return out

    res += run(REF_G, REF_T, True)
    print(now(), "reference cell done", flush=True)
    for gc in gcells:
        if gc != REF_G:
            res += [z for z in run(gc, REF_T, False) if z["feature"] == "goalie"]
    for tc in tcells:
        if tc != REF_T:
            res += [z for z in run(REF_G, tc, False) if z["feature"] == "team"]
    print(now(), "grid done", flush=True)
    C = pd.DataFrame(res)
    C["coef_x_sd"] = C.coef * C.rating_sd
    fl = []
    for (gc, tc, ft), g in C.groupby(["g_cell", "t_cell", "feature"]):
        g = g.sort_values("season")
        tb, tse, z, chi2 = trend(g.coef.to_numpy(), g.se_cluster.to_numpy())
        fl.append(dict(g_cell=gc, t_cell=tc, feature=ft, **{f"coef_{s}": v for s, v in zip(SEAS, g.coef)},
                       **{f"se_{s}": v for s, v in zip(SEAS, g.se_cluster)}, trend_per_season=tb, trend_se=tse,
                       trend_z=z, chi2_equal_2df=chi2))
    FL = pd.DataFrame(fl)
    ref = FL[(FL.g_cell == REF_G) & (FL.t_cell == REF_T)]
    verdict = {ft: dict(z=float(ref[ref.feature == ft].trend_z.iloc[0]),
                        trend=bool(abs(ref[ref.feature == ft].trend_z.iloc[0]) > 2)) for ft in ("goalie", "team")}
    (RES / "step0.json").write_text(json.dumps(dict(level=sel, ref=[REF_G, REF_T], verdict=verdict, coef=C.to_dict("records"),
                                                    trend=FL.to_dict("records")), indent=1, default=float))
    gz = FL[FL.feature == "goalie"].set_index("g_cell")[["coef_20212022", "coef_20222023", "coef_20232024", "trend_z"]]
    tz = FL[FL.feature == "team"].set_index("t_cell")[["coef_20212022", "coef_20222023", "coef_20232024", "trend_z"]]
    L = ["# G-R1 step 0: per-season rating-response trend test (Lane G, 2026-10-16)", "",
         "Spec: `docs/models/goal/experiments.md` G-R1 step 0 (L35). Committed before any arm is fit. Script "
         f"`scripts/diag_goal_gr1_step0.py`; generated {now()} ({time.time() - t0:.0f} s). Training seasons 2021-22..2023-24 "
         f"only; 2024-25 not read. C0 offset = fold-2 training cell table + level {sel}. Ratings from "
         "`data/processed/goal/ratings_{goalie,team}_v1_f2.parquet` (as-of, created_at < puck_drop). Unpenalised logistic "
         "per season on every in-scope SOG row: C0 offset + strength-group intercepts + score + home + b2b own / opp + "
         "arena distance factor + goalie save rating + team finishing rating (raw rating units; goalie rating is "
         "saves-above-expected, so its expected coefficient is negative; team rating is goals-above-expected, positive). "
         "SE = game-cluster sandwich. Trend = inverse-variance-weighted slope on season index, z = slope / SE.", "",
         f"## Reference cell (goalie {REF_G}, team {REF_T}): the read", "",
         C[(C.g_cell == REF_G) & (C.t_cell == REF_T)].drop(columns=["g_cell", "t_cell"]).set_index(["feature", "season"])
         .to_markdown(floatfmt=".4f"), "",
         ref.drop(columns=["g_cell", "t_cell"]).set_index("feature").to_markdown(floatfmt=".4f"), "",
         "## Verdict (|z| > 2 = trend)", ""]
    for ft, v in verdict.items():
        L.append(f"- **{ft}**: trend z {v['z']:+.2f} -> {'TREND: listed; the rating still enters the arms at the D32 fixed scale (an as-of scale is INV-53, deferred)' if v['trend'] else 'no trend at |z| > 2'}.")
    L += ["", "## Robustness: every goalie cell (team at the reference cell)", "", gz.to_markdown(floatfmt=".4f"), "",
          "## Robustness: every team cell (goalie at the reference cell)", "", tz.to_markdown(floatfmt=".4f"), ""]
    OUTMD.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)


if __name__ == "__main__":
    main()
