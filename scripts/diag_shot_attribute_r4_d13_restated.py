"""SL-R4 D13 guard as restated by D28 (fold 1 only; nothing on fold 2 is read): every SL-R1 bias check read on L3c
MINUS L0s, i.e. the deviation the trees add to the shared baseline, with the SL-R1 tolerances:
  xG_ref per attempt, L3c / L0s - 1: overall +/-2%; per strength group (n >= 2,000) +/-3%; per month (n >= 100 games) +/-4%
  location tier shares, L3c - L0s: +/-1.5 pp overall and per strength group (n >= 2,000)
  type shares, L3c - L0s: +/-1.5 pp overall
EN groups are reported, not gated (D28: they gate at stage 8). The oracle-level read (diag_shot_attribute_r4_fold1_level)
is reported alongside. Writes d13_guard_basis / d13_guard_pass / d13_guard_pass_original / d13_restated into
results/shot_attribute_r4/grade_fold1.json (the original fields are kept).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.shot_attribute.tables import GROUP_NAMES, N_CELL, N_TYPE, TIER_NAMES, TIER_OF_CELL  # noqa: E402

D = Path("results/shot_attribute_r4/fold1")
G1 = Path("results/shot_attribute_r4/grade_fold1.json")
CT = np.repeat(TIER_OF_CELL, N_TYPE)
CY = np.tile(np.arange(N_TYPE), N_CELL)
EN = ("ENF", "ENA")


def main():
    r = pd.read_parquet(D / "fold1_rows.parquet")
    lab = json.loads((D / "labels_sealed.json").read_text())
    P = {a: np.load(D / f"fold1_pred_{lab[a]}.npy").astype(np.float64) for a in ("L0s", "L3c")}
    xg = np.load(Path("data/processed/shot_attribute/xg_ref_v1_f1.npy"))
    grp = r.grp.to_numpy()
    xc = xg[:, grp].T
    px = {a: (P[a] * xc).sum(1) for a in P}
    rows = []

    def add(kind, cell, m, tol, gated, v):
        rows.append(dict(check=kind, cell=cell, n=int(m.sum()), value=float(v), tol=tol,
                         status=("reported (EN, gates at stage 8, D28)" if cell in EN else
                                 ("UNDERPOWERED" if not gated else ("PASS" if abs(v) <= tol else "FAIL")))))
    allm = np.ones(len(r), bool)
    add("xG rel", "overall", allm, 0.02, True, px["L3c"].mean() / px["L0s"].mean() - 1)
    for g in range(5):
        m = grp == g
        add("xG rel", GROUP_NAMES[g], m, 0.03, m.sum() >= 2000, px["L3c"][m].mean() / px["L0s"][m].mean() - 1)
    mon = pd.to_datetime(r.game_date_local).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = mon == mo
        add("xG rel", mo, m, 0.04, r.game_id[m].nunique() >= 100, px["L3c"][m].mean() / px["L0s"][m].mean() - 1)
    for nm, m in [("overall", allm)] + [(GROUP_NAMES[g], grp == g) for g in range(5)]:
        for k in range(3):
            d = (P["L3c"][m][:, CT == k].sum(1).mean() - P["L0s"][m][:, CT == k].sum(1).mean()) * 100
            add(f"tier {TIER_NAMES[k]} pp", nm, m, 1.5, nm == "overall" or m.sum() >= 2000, d)
    for k in range(N_TYPE):
        d = (P["L3c"][:, CY == k].sum(1).mean() - P["L0s"][:, CY == k].sum(1).mean()) * 100
        add(f"type {k} pp", "overall", allm, 1.5, True, d)
    T = pd.DataFrame(rows)
    ok = bool((T.status != "FAIL").all())
    print(T.to_string(float_format=lambda v: f"{v:+.5f}"))
    g = json.loads(G1.read_text())
    if "d13_guard_pass_original" not in g:
        g["d13_guard_pass_original"] = g["d13_guard_pass"]
    if g["d13_guard_pass_original"] is not False:
        raise ValueError("expected the original guard result to be false")
    ora = json.loads((D / "level_diag.json").read_text())["rows"]
    g.update(d13_guard_basis="L3c-minus-L0s (D28)", d13_guard_pass=ok,
             d13_restated=dict(rows=rows, max_abs_xg_rel=float(T[T.check == "xG rel"].value.abs().max()),
                               oracle_read=[x for x in ora if x["level"].startswith("O")]))
    G1.write_text(json.dumps(g, indent=1, default=float))
    T.to_csv(D / "d13_restated.csv", index=False)
    print("D13 guard (restated, L3c minus L0s):", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
