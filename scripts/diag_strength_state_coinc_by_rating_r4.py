"""SS-R4 supplementary: actual penalties per team-game and coincidental (offsetting, no PP) share by own taken-rating
quintile, fold 2 (2024-25). Shows whether the penalty -> PP-opportunity mapping should be team-responsive."""
import sys
from pathlib import Path

import pandas as pd

t = pd.read_parquet("data/processed/strength_state/type_rows_v2.parquet")
rows = pd.read_parquet("results/strength_state_r3/fold2_rows.parquet")
tg = rows.groupby(["game_id", "team"]).agg(taken=("taken_own", "first")).reset_index()
t = t[t.season == 20242025].assign(co=lambda d: d.cls == "coincidental")
a = t.groupby(["game_id", "team"]).agg(n=("cls", "size"), co=("co", "sum")).reset_index()
d = tg.merge(a, on=["game_id", "team"], how="left").fillna({"n": 0, "co": 0})
d["q"] = pd.qcut(d.taken.rank(method="first"), 5, labels=False)
g = d.groupby("q").agg(taken=("taken", "mean"), pen=("n", "mean"), coinc=("co", "mean"), N=("n", "size"))
g["coinc_share"] = g.coinc / g.pen
g["noncoinc_pg"] = g.pen - g.coinc
print(g.to_string(float_format=lambda x: f"{x:.4f}"))
g.to_csv("results/strength_state_r4/coinc_by_taken_quintile_fold2.csv")
