"""SM-R3 step 0 (docs/models/miss/experiments.md SM-R3): per-season score-bucket logistic coefficients on top of S0t, with SEs and a
trend z per bucket (L35). TRAINING seasons of fold 2 only (2021-22, 2022-23, 2023-24); 2024-25 is not read here (load_rows is
called for the training seasons only). Buckets from the row's sc (shooter-view score diff BEFORE the attempt, clip +-3):
trail2+ (sc 0,1), trail1 (2), tied (3, reference), lead1 (4), lead2+ (5,6). Gated rows (grp 0..2); the S0t logit is the offset;
the 10 level intercepts are free (unpenalised) as in S1t, so the dummies are relative to the matched level. Trend z = WLS slope of
the 3 per-season coefficients on season index / its SE (inverse-variance weights). Writes results/miss_sm_r3/step0.json and
docs/tests/miss_sm_r3_step0_2026-10-21.md."""
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhl_sim.block.models import fit_logit_offset  # noqa: E402
from nhl_sim.miss import models as MM  # noqa: E402
import train_miss_v2 as T2  # noqa: E402

BUCKET_OF_SC = np.array([0, 0, 1, 2, 3, 4, 4])
NAMES = ["trail2+", "trail1", "tied", "lead1", "lead2+"]
OUT = Path("results/miss_sm_r3")


def design(r, extra_cols=0):
    b = BUCKET_OF_SC[r.sc.to_numpy()]
    return np.hstack([np.eye(MM.N_L0)[r.l0.to_numpy()], np.eye(5)[b][:, [0, 1, 3, 4]]])


def fit_se(X, y, off):
    w, _ = fit_logit_offset(X, y, off, n_free=X.shape[1])
    p = 1 / (1 + np.exp(-(X @ w + off)))
    H = (X * (p * (1 - p))[:, None]).T @ X
    k = np.flatnonzero(X.any(0))                 # drop empty level columns (EN groups are not in the gated rows)
    se = np.zeros(X.shape[1])
    se[k] = np.sqrt(np.diag(np.linalg.inv(H[np.ix_(k, k)])))
    return w, se


def main():
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "start", flush=True)
    tr, te, m0, ltr, lte = T2.frames(2)           # te (2024-25) is built by the shared loader but never touched below
    g = (tr.grp <= 2).to_numpy()
    rows, seasons = [], sorted(tr.season.unique())
    for s in seasons:
        m = g & (tr.season == s).to_numpy()
        X = design(tr[m])
        w, se = fit_se(X, tr.y.to_numpy()[m].astype(float), ltr[m])
        rows.append(dict(season=int(s), n=int(m.sum()), coef=w[MM.N_L0:].tolist(), se=se[MM.N_L0:].tolist()))
    C = np.array([r["coef"] for r in rows])
    S = np.array([r["se"] for r in rows])
    x = np.arange(len(seasons), dtype=float)
    trend = []
    for j, nm in enumerate([n for n in NAMES if n != "tied"]):
        w = 1 / S[:, j] ** 2
        xb = (w * x).sum() / w.sum()
        sl = (w * (x - xb) * C[:, j]).sum() / (w * (x - xb) ** 2).sum()
        sse = 1 / np.sqrt((w * (x - xb) ** 2).sum())
        trend.append(dict(bucket=nm, slope_per_season=float(sl), se=float(sse), z=float(sl / sse)))
    pooled_w, pooled_se = fit_se(design(tr[g]), tr.y.to_numpy()[g].astype(float), ltr[g])
    res = dict(seasons=[int(s) for s in seasons], per_season=rows, trend=trend, pooled_coef=pooled_w[MM.N_L0:].tolist(),
               pooled_se=pooled_se[MM.N_L0:].tolist(), max_abs_z=float(max(abs(t["z"]) for t in trend)))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step0.json").write_text(json.dumps(res, indent=1))
    nm4 = [n for n in NAMES if n != "tied"]
    t1 = pd.DataFrame([{"season": r["season"], "n": r["n"], **{f"{n}": f"{c:+.3f} ({s:.3f})" for n, c, s in zip(nm4, r["coef"], r["se"])}}
                       for r in rows])
    t1.loc[len(t1)] = {"season": "pooled", "n": int(g.sum()), **{n: f"{c:+.3f} ({s:.3f})" for n, c, s in zip(nm4, res["pooled_coef"], res["pooled_se"])}}
    L = ["# SM-R3 step 0: per-season score-bucket coefficients on S0t (Lane M3, 2026-10-21)", "",
         f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} by `scripts/exp_miss_smr3_step0.py`. TRAINING seasons of fold 2 only "
         "(2021-22, 2022-23, 2023-24); fold 2 (2024-25) is not read. Gated rows (ES / PP / PK, goalie in); offset = the S0t logit "
         "(M2_H30 tier level, frozen); 10 level intercepts free; unpenalised logistic; coefficients are logit differences vs tied "
         "(shooter-view score before the attempt), SE in parentheses.", "", t1.to_markdown(index=False), "",
         "Trend (WLS of the 3 per-season coefficients on season index, inverse-variance weights; 3 points, 1 df, so the z is a weak test):", "",
         pd.DataFrame(trend).to_markdown(index=False, floatfmt=".3f"), "",
         f"- max |z| = {res['max_abs_z']:.2f}. " + ("**A bucket has |z| > 2: the round STOPS here (as-of construction needed, pre-registered separately).**"
                                                    if res["max_abs_z"] > 2 else "No bucket has |z| > 2: the pooled dummies proceed.")]
    Path("docs/tests/miss_sm_r3_step0_2026-10-21.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "done")


if __name__ == "__main__":
    main()
