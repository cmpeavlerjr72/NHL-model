"""SL-R4 D13-guard diagnostic (fold 1 only; nothing on fold 2 is read). Splits the fold-1 bias failure into the level
and the arm: re-predicts the fold-1 test season (2023-24) with L0s and L3c under (a) level E as graded (zero on fold 1,
since era 2 has no fold-1 training rows), (b) the ORACLE level O (2023-24's own final shares; diagnostic, never
selectable), and reports xG_ref per attempt pred / actual overall and by strength group, tier shares, and the ES
responsiveness spread ratio. Not a gate and not blind (labelled).

    diag_shot_attribute_r4_fold1_level.py  -> results/shot_attribute_r4/fold1/level_diag.json (+ stdout table)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhl_sim.shot_attribute import mix_level as ML  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute.tables import GROUP_NAMES, TIER_NAMES, TIER_OF_CELL, N_TYPE  # noqa: E402
import train_shot_attribute_v4 as T  # noqa: E402

CT = np.repeat(TIER_OF_CELL, N_TYPE)


def spread(pred, act, r):
    m = r.grp.to_numpy() == 0
    x = r[m].assign(p=pred[m], a=act[m])
    out = {}
    for col in ("own_r", "opp_r"):
        tg = x.groupby(["game_id", "team"])[col].first()
        q = pd.qcut(tg.rank(method="first"), 5, labels=False).rename("q")
        g = x.join(q, on=["game_id", "team"]).groupby("q")[["p", "a"]].mean()
        out[col] = float((g.p.iloc[4] - g.p.iloc[0]) / (g.a.iloc[4] - g.a.iloc[0]))
    return out


def main():
    _, l0s, bs = T.load_fold(1)
    tr, te = T.frames(1)
    _, oE, s_train = T.offsets(1, tr, te)
    L = pd.read_parquet(T.LEVELS)
    oO = ML.row_offset(te, L[L.construction == "O"], s_train)
    xg = np.load(M.SA / "xg_ref_v1_f1.npy")
    grp = te.grp.to_numpy()
    xc = xg[:, grp].T
    act = xg[te.cls.to_numpy(), grp]
    res = {}
    rows = []
    for lev, off in (("E (as graded)", oE), ("O oracle (diagnostic)", oO)):
        for arm in ("L0s", "L3c"):
            P = T.predict(arm, l0s, bs, te, off)
            pred = (P * xc).sum(1)
            rec = dict(level=lev, arm=arm, xg_all=float(pred.mean() / act.mean() - 1))
            for g in range(5):
                m = grp == g
                rec[f"xg_{GROUP_NAMES[g]}"] = float(pred[m].mean() / act[m].mean() - 1)
            At = np.eye(3)[CT[te.cls.to_numpy()]]
            for k in range(3):
                rec[f"{TIER_NAMES[k]}_pp"] = float((P[:, CT == k].sum(1).mean() - At[:, k].mean()) * 100)
                m = grp == 0
                rec[f"ES_{TIER_NAMES[k]}_pp"] = float((P[m][:, CT == k].sum(1).mean() - At[m, k].mean()) * 100)
            rec.update({f"resp_{k}": v for k, v in spread(pred, act, te).items()})
            rows.append(rec)
    D = pd.DataFrame(rows)
    print(D.to_string(float_format=lambda v: f"{v:+.4f}"))
    res["rows"] = rows
    res["note"] = "fold 1 only; oracle level O is 2023-24's own final shares (never selectable); not blind, not a gate"
    (T.RES / "fold1" / "level_diag.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
