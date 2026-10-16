"""G-R1 POST-HOC level diagnostic (run AFTER the blind fold-2 grade; nothing here is selectable; L29: read the oracle
level before blaming the level). C0 on the fold-2 / fold-1 test season under every step-1 level construction:
save% (gated, 5v5, PP, PK) pred - actual and regular-season goals from SOG (pred / actual - 1).
-> results/goal_g_r1/level_post.json, printed table (copied into the report).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.goal import data as D  # noqa: E402

RES = Path("results/goal_g_r1")

if __name__ == "__main__":
    rows = pd.read_parquet(RES / "rows_v1.parquet")
    out = []
    for fold in (2, 1):
        tr_s, te_s = D.F[fold]
        r = rows[rows.season == te_s].reset_index(drop=True)
        T = np.load(D.OUT / f"cell_table_f{fold}.npy")
        lv = pd.read_parquet(D.OUT / f"level_v1_f{fold}.parquet")
        y = r.y.to_numpy(float)
        rs = (r.game_type == 2).to_numpy()
        for n in lv.construction.unique():
            p = D.sigmoid(D.c0_logit(r, T, lv[lv.construction == n]))
            d = dict(fold=fold, construction=n)
            for nm, m in (("gated", r.sg.isin(D.GATED_SG).to_numpy()), ("5v5", (r.sg == 0).to_numpy()),
                          ("PP", (r.sg == 1).to_numpy()), ("PK", (r.sg == 2).to_numpy())):
                d[f"sv_{nm}_pp"] = 100 * (y[m].mean() - p[m].mean())
            d["goals_pct"] = 100 * (p[rs].sum() / y[rs].sum() - 1)
            out.append(d)
    O = pd.DataFrame(out)
    (RES / "level_post.json").write_text(json.dumps(out, indent=1, default=float))
    print(O.set_index(["fold", "construction"]).to_markdown(floatfmt=".3f"))
