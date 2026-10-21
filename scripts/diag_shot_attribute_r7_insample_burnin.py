"""SL-R7 diagnostic (training rows only; no fold-2 row is read): where the in-sample 4v4 miss of L1x-as comes from.
Per state x training-season and, for 2021-22, the burn-in window (dates up to 2021-10-25, the last date on which the
as-of scale needed direct evaluation) vs the rest of the season. -> results/shot_attribute_r7/insample_burnin_diag.json"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import train_shot_attribute_v7 as T  # noqa: E402
from nhl_sim.shot_attribute import models_s as MS  # noqa: E402

D, tr, otr, P = T.arm_preds(2, "train")
xg = D["xg"]
grp = tr.grp.to_numpy()
xc = xg[:, grp].T
d = pd.to_datetime(tr.game_date_local)
seg = np.where(tr.season != T.FIRST, tr.season.astype(str),
               np.where(d <= pd.Timestamp("2021-10-25"), "2021-22 to 10-25 (burn-in jump)", "2021-22 after 10-25"))
F = T.snapshots(2)
sel = T.selected()["selected"]
sf, sa = T.cell_scale(F, sel, tr.game_date_local.to_numpy())
rows = []
for st in range(5):
    for sg in sorted(set(seg)):
        m = (tr.st.to_numpy() == st) & (seg == sg)
        if not m.any():
            continue
        b = (P["L0s"][m] * xc[m]).sum(1).mean()
        a = (P["L1xas"][m] * xc[m]).sum(1).mean()
        rows.append(dict(state=MS.STATE_NAMES[st], segment=sg, n=int(m.sum()), L1xas_vs_L0s=float(a / b - 1),
                         max_abs_s_for_raw=float(np.abs(sf[m]).max() / D["sd"][0]),
                         max_abs_s_against_raw=float(np.abs(sa[m]).max() / D["sd"][1])))
R = pd.DataFrame(rows)
print(R.to_string(float_format=lambda v: f"{v:+.5f}"))
(T.RES / "insample_burnin_diag.json").write_text(json.dumps(rows, indent=1))
