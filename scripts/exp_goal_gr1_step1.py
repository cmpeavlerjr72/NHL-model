"""G-R1 step 1 (docs/models/goal/experiments.md G-R1): conversion-level constructions, parity with the oracle row,
selection. Runs BEFORE any rating, step-0 or arm fit.

Per fold: C0 = cell table (recorded training goal rate per cell x type x strength group, nhl_sim.goal.data.cell_table)
+ level delta (logit offset, coefficient 1). Parity = C0 save percentage minus actual (pp), in sample, per genuine-prior
training season (fold 1: 2022-23; fold 2: 2022-23 and 2023-24), over gated rows (5v5 + PP + PK) and 5v5; tol +/-0.3 pp.
2021-22 has no prior: shown, not judged. Selection (LC-2 / SB-R1 rule): simplest passer (M0 < E < M1 < M2; within a
family the smaller max |parity|), else the smallest max |parity| with ties within 0.1 pp to the simpler construction
(failure listed, proceed). One selection over both folds' judged cells.
-> data/processed/goal/{cell_table_f1,f2}.npy, level_v1_f{1,2}.parquet, results/goal_g_r1/step1.json,
   docs/tests/goal_g_r1_step1_2026-10-16.md
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.goal import data as D  # noqa: E402

RES = Path("results/goal_g_r1")
REPORT = Path("docs/tests/goal_g_r1_step1_2026-10-16.md")
SPECS = {"none": ("none", None), "M0": ("M0", None), "E": ("E", None), "M1_K500": ("M1", 500),
         "M1_K2000": ("M1", 2000), "M1_K8000": ("M1", 8000), "M2_H30": ("M2", (30, 2000)), "M2_H60": ("M2", (60, 2000)),
         "O": ("O", None)}
FAMILY = {k: v[0] for k, v in SPECS.items()}
TOL = 0.3


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def main():
    RES.mkdir(parents=True, exist_ok=True)
    D.OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, info = D.load_rows()
    rows.to_parquet(RES / "rows_v1.parquet", index=False)
    print(now(), "rows", len(rows), info, flush=True)
    P = []
    for fold in (1, 2):
        tr_s, te_s = D.F[fold]
        r = rows[rows.season.isin(tr_s + [te_s])].reset_index(drop=True)
        tr = r.season.isin(tr_s).to_numpy()
        T = D.cell_table(r[tr])
        np.save(D.OUT / f"cell_table_f{fold}.npy", T)
        p_tab = D.table_prob(r, T)
        meta, LV = D.asof_levels(r, p_tab, SPECS, tr_s)
        D_ = pd.concat([D.level_frame(meta, LV[n], n) for n in SPECS], ignore_index=True)
        D_.to_parquet(D.OUT / f"level_v1_f{fold}.parquet", index=False)
        y = r.y.to_numpy().astype(float)
        for n in SPECS:
            p = D.sigmoid(D.logit(p_tab) + D.row_delta(r, D_[D_.construction == n]))
            for season in tr_s:
                for scope, mk in (("gated", r.sg.isin(D.GATED_SG)), ("5v5", r.sg == 0)):
                    m = ((r.season == season) & mk).to_numpy()
                    P.append(dict(fold=fold, construction=n, season=season, scope=scope, n=int(m.sum()),
                                  sv_pred=100 * (1 - p[m].mean()), sv_act=100 * (1 - y[m].mean()),
                                  judged=season in D.JUDGED[fold]))
        print(now(), "fold", fold, "done", flush=True)
    P = pd.DataFrame(P)
    P["diff_pp"] = P.sv_pred - P.sv_act
    P.to_csv(RES / "step1_parity_long.csv", index=False)
    J = P[P.judged]
    S = pd.DataFrame([dict(construction=n, family=FAMILY[n], max_abs_pp=J[J.construction == n].diff_pp.abs().max())
                      for n in SPECS])
    S["all_pass"] = S.max_abs_pp <= TOL
    cand = S[~S.construction.isin(["none", "O"])]
    order = ("M0", "E", "M1", "M2")
    passers = cand[cand.all_pass]
    if len(passers):
        fam = min(passers.family, key=order.index)
        sel = passers[passers.family == fam].sort_values("max_abs_pp").construction.iloc[0]
        rule = "simplest passer"
    else:
        best = {f: cand[cand.family == f].sort_values("max_abs_pp").iloc[0] for f in order}
        mn = min(v.max_abs_pp for v in best.values())
        sel = next(best[f].construction for f in order if best[f].max_abs_pp <= mn + 0.1)
        rule = "fallback: smallest max |parity|, ties within 0.1 pp to the simpler construction (failure listed)"
    out = dict(selected=sel, rule=rule, tol_pp=TOL, summary=S.to_dict("records"), row_info={str(k): v for k, v in info.items()})
    (RES / "step1.json").write_text(json.dumps(out, indent=1, default=float))
    piv = P.pivot_table(index=["fold", "construction", "season"], columns="scope", values="diff_pp")
    piv["judged"] = P[P.scope == "gated"].set_index(["fold", "construction", "season"]).judged
    seen = rows[rows.season < D.F[2][1]]    # training seasons only: the fold-2 test season is not summarised here
    raw = seen.groupby(["season", "sg"]).agg(n=("y", "size"), sv=("y", "mean")).reset_index()
    raw["sv"] = 100 * (1 - raw.sv)
    rawp = raw.pivot(index="season", columns="sg", values="sv").rename(columns=dict(enumerate(D.SG_NAMES))).round(3)
    rawn = raw.pivot(index="season", columns="sg", values="n").rename(columns=dict(enumerate(D.SG_NAMES)))
    oracle = []
    for fold in (1, 2):
        lv = pd.read_parquet(D.OUT / f"level_v1_f{fold}.parquet")
        o = lv[(lv.construction == "O") & lv.season.isin(D.F[fold][0])].groupby("season")[[f"d_{g}" for g in range(D.N_LG)]].first()
        o.columns = list(D.LG_NAMES)
        o.insert(0, "fold", fold)
        oracle.append(o)
    O = pd.concat(oracle)
    L_ = ["# G-R1 step 1: conversion-level constructions and parity (Lane G, 2026-10-16)", "",
          "Spec (binding): `docs/models/goal/experiments.md` G-R1. Script: `scripts/exp_goal_gr1_step1.py`; library "
          "`src/nhl_sim/goal/data.py`; tables `data/processed/goal/cell_table_f{1,2}.npy`, `level_v1_f{1,2}.parquet` "
          "(created_at < puck_drop asserted). Run before any rating, step-0 or arm fit.", "",
          f"Generated {now()} ({time.time() - t0:.0f} s).", "",
          "Rows: SOG with a goalie in net (empty-net st 6 and goalie-less SOG excluded): " +
          "; ".join(f"{k}: {v['sog']:,} SOG, {v['empty_net_st6']} empty-net, {v['goalie_missing_in_goalie_state']} goalie-less "
                    f"({v['goalie_missing_goals']} goals)" for k, v in info.items()) + ".", "",
          "C0 = shrunk recorded training goal rate per cell x type x strength group (K = 20 SOG toward class x group "
          "ratio, labelled) + level delta = logit(G_hat) - logit(E_hat) per level group, coefficient 1. E is the C0 table "
          "probability, so the level is the conversion relative to the training cell table. Parity = C0 save% minus actual "
          "(pp) per training season, gated (5v5 + PP + PK) and 5v5. Tolerance +/-0.3 pp. 2021-22 has no prior (look-ahead, "
          "shown, not judged). E on fold 1: every training row is era 1, so era-2 test games fall back to pooled training "
          "rates (delta ~ 0).", "",
          "## Parity (C0 save% pred - actual, pp)", "", piv.round(3).to_markdown(), "",
          "## Summary over judged cells", "", S.round(3).to_markdown(index=False), "",
          f"## Selection: **{sel}** ({rule})", "",
          "## Oracle level delta per training season (logit, relative to the fold's training table)", "", O.round(4).to_markdown(), "",
          "## Raw save% by training season and strength group (rows in scope)", "", rawp.to_markdown(), "", "n:", "",
          rawn.to_markdown(), ""]
    REPORT.write_text("\n".join(L_), encoding="utf-8")
    print(S.round(3).to_string())
    print("selected", sel, "-", rule)


if __name__ == "__main__":
    main()
