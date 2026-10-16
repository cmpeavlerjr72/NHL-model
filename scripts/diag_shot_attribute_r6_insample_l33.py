"""SL-R6 diagnostic after the in-sample stop (fold-2 TRAINING rows only; nothing on 2024-25 is read).

Question for the PM: is the 3v3 in-sample miss of L1x (-0.51% vs L0s) the L33 cross-stratum score transfer? The
variant L1x-ot0 is identical to L1x except that the fitted home / score / rest terms are switched off on OT rows
(period type OT: the centred feature row is set to 0, so OT rows get L0s levelled + the fixed-scale rating tilt),
in both fitting and serving. Same frozen s (Qa x0.75), same fold-2 training rows, same in-sample table.
Diagnostic only: not a pre-registered arm, never selectable without a PM ruling.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_shot_attribute_v6 as T  # noqa: E402
from nhl_sim.shot_attribute import models_s as MS  # noqa: E402
from nhl_sim.shot_attribute import models_x as MX  # noqa: E402


def main():
    fz = T.frozen()
    tr, te = T.frames(2)
    otr, _, _ = T.offsets(2, tr, te)
    xg = T.xgref(2)
    oc, pc = T.cols()
    l0s = MS.fit_l0s(tr)
    f, rr = MX.fitter_for(tr, l0s, otr, xg, oc, pc)
    ot = rr.ptype.to_numpy() == 1
    f.X[ot] = 0.0
    m = f.fit(s_fixed=(fz["s_f"], fz["s_a"]))
    msk = MS.booster_rows(tr)
    P0 = MS.l0s_levelled(l0s, tr, otr)
    P = P0.copy()
    P[msk] = MX._softmax(f.logits(np.asarray(m["W"]), m["s_f"], m["s_a"]))
    grp = tr.grp.to_numpy()
    xc = xg[:, grp].T
    act = xg[tr.cls.to_numpy(), grp]
    st, pt = tr.st.to_numpy(), tr.ptype.to_numpy()
    cells = [(MS.STATE_NAMES[s], st == s) for s in range(7)]
    cells += [(f"{MS.STATE_NAMES[s]} {'OT' if p_ else 'reg'}", (st == s) & (pt == p_)) for s in range(7) for p_ in (0, 1)]
    rows = []
    for nm, c in cells:
        n = int(c.sum())
        if n == 0:
            continue
        b = (P0[c] * xc[c]).sum(1).mean()
        v = (P[c] * xc[c]).sum(1).mean()
        rows.append(dict(stratum=nm, n=n, l0s_vs_actual=float(b / act[c].mean() - 1), ot0_vs_L0s=float(v / b - 1),
                         gated=bool(n >= T.N_MIN), passed=bool((n < T.N_MIN) or abs(v / b - 1) <= T.TOL)))
    D = pd.DataFrame(rows)
    out = dict(variant="L1x-ot0 (fitted terms off on OT rows); diagnostic, fold-2 training rows only",
               pass_all=bool(D.passed.all()), rows=rows, converged=m["converged"], nit=m["nit"])
    (T.RES / "insample_ot0_diag.json").write_text(json.dumps(out, indent=1))
    print(D.to_string(float_format=lambda v: f"{v:+.5f}"))
    print("all gated strata within 0.5%:", out["pass_all"])


if __name__ == "__main__":
    main()
