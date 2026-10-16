"""SL-R2 step 0: as-of league location-mix level constructions, per-training-season parity of L0m, oracle row, and the
pre-registered selection (docs/models/shot_attribute/experiments.md SL-R2). No arm other than L0m is fit here.

Parity (per genuine-prior training season, both folds; L0m = L0 fit on the fold's training rows x exp(offset)):
  ES high-danger share pred - actual within +/-0.5 pp; mean xG_ref per unblocked attempt pred / actual within +/-0.5%.
Selection: simplest passer (M0 < E < M1 < M2; within a family the smallest max |parity| / tolerance, labelled);
otherwise the smallest max |xG_ref parity|, ties within 0.2% to the simpler. O is never selectable.

    diag_shot_attribute_mixlevel_step0.py   -> data/processed/shot_attribute/mix_level_v2.parquet,
                                               results/shot_attribute_r2/step0.json, step0_tables.md
Test seasons are not evaluated here (2024-25 untouched by step 0; 2025-26 sealed).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import PROCESSED  # noqa: E402
from nhl_sim.shot_attribute import mix_level as ML  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CELL, N_TYPE, TIER_OF_CELL  # noqa: E402

SA = PROCESSED / "shot_attribute"
RES = Path("results/shot_attribute_r2")
SEASONS = [20212022, 20222023, 20232024, 20242025]
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
SPECS = {"M0": ("M0", None), "M1_K500": ("M1", 500), "M1_K2000": ("M1", 2000), "M1_K8000": ("M1", 8000),
         "M2_H30": ("M2", (30, 2000)), "M2_H60": ("M2", (60, 2000)), "O": ("O", None)}
HD_TOL, XG_TOL, TIE = 0.5, 0.005, 0.002
HIGH = np.repeat(TIER_OF_CELL == 0, N_TYPE)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def main():
    print(now(), "start", flush=True)
    RES.mkdir(parents=True, exist_ok=True)
    rows = M.load_rows(SEASONS)
    u = rows[~rows.blocked].copy()
    u["l0"] = (u.grp.astype(np.int64) * 2 + u.ptype).astype(np.int8)
    tg = pd.read_parquet(PROCESSED / "strength_state" / "team_game_v2.parquet", columns=["game_id", "season", "date", "drop"])
    games = tg[tg.season.isin(SEASONS)].drop_duplicates("game_id").reset_index(drop=True)
    meta, lv = ML.asof_levels(u, games, SPECS)
    frames = [ML.level_frame(meta, S).assign(construction=n) for n, S in lv.items()]
    for f, (tr, te) in F.items():
        E = ML.era_level(u[u.season.isin(tr)], meta)
        frames.append(ML.level_frame(meta, E).assign(construction=f"E_f{f}"))
    L = pd.concat(frames, ignore_index=True)
    L.to_parquet(SA / "mix_level_v2.parquet", index=False)
    print(now(), "levels", L.shape, flush=True)
    par, keep = [], []
    for f, (tr, te) in F.items():
        utr = u[u.season.isin(tr)]
        m0 = M.fit_l0(utr)
        P0 = M.predict_l0(m0, utr)
        s_train = ML.share_table(utr)
        xg = np.load(SA / f"xg_ref_v1_f{f}.npy")
        cls, grp = utr.cls.to_numpy(), utr.grp.to_numpy()
        act_xg = xg[cls, grp]
        xg_cls = xg[:, grp].T
        es = grp == 0
        act_hd = HIGH[cls]
        for cname in ["none (L0)", "M0", f"E_f{f}", "M1_K500", "M1_K2000", "M1_K8000", "M2_H30", "M2_H60", "O"]:
            if cname == "none (L0)":
                P = P0
            else:
                off = ML.row_offset(utr, L[L.construction == cname], s_train)
                P = ML.apply_cell_offset(P0, off)
            pxg = (P * xg_cls).sum(1)
            phd = P[:, HIGH].sum(1)
            for s in tr:
                m = (utr.season == s).to_numpy()
                me = m & es
                par.append(dict(fold=f, construction=cname.replace(f"E_f{f}", "E"), season=s,
                                genuine_prior=s != SEASONS[0], n=int(m.sum()),
                                es_hd_pred=phd[me].mean() * 100, es_hd_act=act_hd[me].mean() * 100,
                                hd_pp=(phd[me].mean() - act_hd[me].mean()) * 100,
                                xg_pred=pxg[m].mean(), xg_act=act_xg[m].mean(), xg_rel=pxg[m].mean() / act_xg[m].mean() - 1,
                                pp_xg_rel=pxg[m & (grp == 1)].mean() / act_xg[m & (grp == 1)].mean() - 1,
                                pk_xg_rel=pxg[m & (grp == 2)].mean() / act_xg[m & (grp == 2)].mean() - 1))
        keep.append(dict(fold=f, s_train=s_train.tolist()))
    T = pd.DataFrame(par)
    T["pass"] = (T.hd_pp.abs() <= HD_TOL) & (T.xg_rel.abs() <= XG_TOL)
    G = T[T.genuine_prior]
    summ = G.groupby("construction").agg(n_cells=("pass", "size"), all_pass=("pass", "all"),
                                         max_abs_hd_pp=("hd_pp", lambda x: x.abs().max()),
                                         max_abs_xg_rel=("xg_rel", lambda x: x.abs().max()))
    summ["max_parity_over_tol"] = np.maximum(summ.max_abs_hd_pp / HD_TOL, summ.max_abs_xg_rel / XG_TOL)
    fam = lambda c: c.split("_")[0]  # noqa: E731
    summ["family"] = [fam(c) for c in summ.index]
    cand = summ[summ.family.isin(ML.SIMPLICITY)].copy()
    cand["order"] = cand.family.map({k: i for i, k in enumerate(ML.SIMPLICITY)})
    passers = cand[cand.all_pass]
    if len(passers):
        first = passers.order.min()
        sel = passers[passers.order == first].sort_values("max_parity_over_tol").index[0]
        rule = (f"passer(s): {passers.index.tolist()}; simplest family {ML.SIMPLICITY[first]}; within it the smallest "
                "max |parity| / tolerance (labelled reading of 'smallest max |parity|')")
    else:
        best = cand.max_abs_xg_rel.min()
        tied = cand[cand.max_abs_xg_rel <= best + TIE].sort_values(["order", "max_abs_xg_rel"])
        sel = tied.index[0]
        rule = (f"no construction passes; smallest max |xG parity| {best:.4%}; within {TIE:.1%}: {tied.index.tolist()}; "
                f"simplest taken")
    out = dict(selected=sel, rule=rule, specs={k: list(v) if isinstance(v, tuple) else v for k, v in SPECS.items()},
               tolerances=dict(hd_pp=HD_TOL, xg_rel=XG_TOL, tie=TIE), s_train=keep,
               parity=T.to_dict("records"), summary=summ.reset_index().to_dict("records"))
    (RES / "step0.json").write_text(json.dumps(out, indent=1, default=float))
    txt = ["## Parity per (fold, construction, training season); 2021-22 rows: prior = own final shares (labelled), not judged", "",
           T.set_index(["fold", "construction", "season"]).to_markdown(floatfmt=".4f"), "",
           "## Summary over genuine-prior cells (fold 1: 2022-23; fold 2: 2022-23, 2023-24)", "",
           summ.to_markdown(floatfmt=".4f"), "", f"Selected: **{sel}**. Rule: {rule}", ""]
    (RES / "step0_tables.md").write_text("\n".join(txt), encoding="utf-8")
    print("\n".join(txt))
    print(now(), "done", flush=True)


if __name__ == "__main__":
    main()
