"""G-R4 diagnostic (labelled; no model choice): can the +/-3% score-bucket check be met by a model that is exactly right?

Parametric check on the fold-1 test rows (2023-24; fold 1 is graded and committed) and on the judged training seasons of
the parity analogue: outcomes are redrawn y* ~ Bernoulli(p) from an arm's own probabilities (so that arm is calibrated by
construction), and the served / actual ratio by bucket relative to tied (gated rows) is recomputed per draw.
Reported: per-bucket and all-four pass rates of the +/-3% band, and the band a calibrated model would pass with 95%
probability (95th percentile of max |ratio - 1| over the four buckets). No fold-2 row is read.

    diag_goal_gr4_band_power.py   -> results/goal_g_r4/band_power.json (+ stdout table)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import train_goal_v4 as T4  # noqa: E402
from nhl_sim.goal import data as D  # noqa: E402
from nhl_sim.goal import score_asof as SA  # noqa: E402

N_DRAW = 2000
SEED = 20261021


def sim(p, b, rng):
    P_ = np.bincount(b, weights=p, minlength=5)
    out = np.empty((N_DRAW, 5))
    for i in range(N_DRAW):
        y = (rng.random(len(p)) < p).astype(float)
        Y_ = np.bincount(b, weights=y, minlength=5)
        out[i] = (P_ / Y_) / (P_[SA.TIED] / Y_[SA.TIED])
    return out[:, list(SA.DEV_B)]


def summarise(R, tag):
    dev = np.abs(R - 1)
    rec = dict(tag)
    for j, b in enumerate(SA.DEV_B):
        rec[f"pass_{SA.B_NAMES[b]}"] = float((dev[:, j] <= 0.03).mean())
    rec["pass_all4"] = float((dev.max(1) <= 0.03).all() if False else (dev.max(1) <= 0.03).mean())
    rec["band_95pct_all4"] = float(np.quantile(dev.max(1), 0.95))
    rec["sd_ratio_mean"] = float(R.std(0).mean())
    return rec


def main():
    rng = np.random.default_rng(SEED)
    rows = []
    d = T4.RES / "fold1"
    r = pd.read_parquet(d / "fold1_rows.parquet")
    lab = json.loads((d / "labels_sealed.json").read_text())
    g = (r.sg <= 2).to_numpy()
    for arm in ("C1s-sa", "C1s"):
        p = np.load(d / f"fold1_pred_{lab[arm]}.npy")[g]
        rows.append(summarise(sim(p, SA.bucket(r[g]), rng), dict(rows="fold-1 test 2023-24", arm=arm)))
    sel = json.loads(T4.SELECT.read_text())["selected"]
    for fold in (1, 2):
        F = T4.frames4(fold)
        rr = F["r"]
        sc = pd.read_parquet(T4.dev_path(fold))
        sc = sc[(sc.cell == sel) & sc.season.isin(F["tr_s"])]
        m = rr.season.isin(D.JUDGED[fold]).to_numpy() & rr.sg.isin(D.GATED_SG).to_numpy()
        x = rr[m]
        p = D.sigmoid(F["ns"][m] + (F["X"][m] * SA.attach_dev(x.date.to_numpy(), sc)).sum(1))
        for s in D.JUDGED[fold]:
            k = (x.season == s).to_numpy()
            rows.append(summarise(sim(p[k], SA.bucket(x[k]), rng), dict(rows=f"fold {fold} judged {s}", arm=f"C1s-sa {sel}")))
    T = pd.DataFrame(rows)
    pa = T[T.rows != "fold-1 test 2023-24"].pass_all4.to_numpy()
    sa_f1 = float(T[(T.rows == "fold-1 test 2023-24") & (T.arm == "C1s-sa")].pass_all4.iloc[0])
    extra = dict(p_parity_all3_pass_if_independent=float(np.prod(pa)),
                 p_parity_and_fold1_guard_if_independent=float(np.prod(pa) * sa_f1))
    (T4.RES / "band_power.json").write_text(json.dumps(dict(table=T.to_dict("records"), **extra, n_draw=N_DRAW), indent=1))
    print(T.to_markdown(index=False, floatfmt=".3f"))
    print(extra)


if __name__ == "__main__":
    main()
