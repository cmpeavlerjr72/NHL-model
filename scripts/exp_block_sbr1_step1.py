"""SB-R1 step 1: level constructions, parity table with the oracle row, selection (docs/models/block/experiments.md
SB-R1). Runs BEFORE any B1 / B2 fit. B0 (level only) is fit on each fold's training rows with each construction as the
offset; parity = B0 block share minus actual per genuine-prior training season (fold 1: 2022-23; fold 2: 2022-23 and
2023-24), overall (grp ES / PP / PK) and ES, tolerance +/-0.3 pp. 2021-22 has no prior season and is shown, not judged.
Selection: simplest passer (M0 < E < M1 < M2; within M1 / M2 the smaller max |parity|), else the smallest max |parity|
with ties within 0.1 pp to the simpler construction; the failure is listed and the run proceeds (LC-2 / SL-R2 rule).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.block import data as D  # noqa: E402
from nhl_sim.block import models as BM  # noqa: E402

RES = Path("results/block_sb_r1")
REPORT = Path("docs/tests/block_sb_r1_step0_2026-10-16.md")
F = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}
JUDGED = {1: [20222023], 2: [20222023, 20232024]}
TOL = 0.3
FAMILY = {"none": "none", "M0": "M0", "E": "E", "M1_K500": "M1", "M1_K2000": "M1", "M1_K8000": "M1",
          "M2_H30": "M2", "M2_H60": "M2", "O": "O"}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def level_for(name, fold, a_all, games, L):
    """-> frame (game_id, s_0..s_2) for all games."""
    if name == "none":
        f = L[L.construction == "M0"][["game_id"]].copy()
        s_tr = D.share_table(a_all[a_all.season.isin(F[fold])])
        for g in range(3):
            f[f"s_{g}"] = s_tr[g]
        return f
    if name == "E":
        gm = games.sort_values(["date", "game_id"]).reset_index(drop=True)
        S = D.era_level(a_all[a_all.season.isin(F[fold])], gm)
        f = pd.DataFrame({"game_id": gm.game_id.to_numpy()})
        for g in range(3):
            f[f"s_{g}"] = S[:, g]
        return f
    return L[L.construction == name]


def main():
    RES.mkdir(parents=True, exist_ok=True)
    a = D.load_attempts()
    games = pd.read_parquet(D.OUT / "games_v1.parquet")
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    a = a.merge(games[["game_id"]], on="game_id")
    a["y"] = a.blocked.astype(np.int8)
    a["l0"] = (a.grp.astype(np.int64) * 2 + a.ptype).astype(np.int8)
    rows = []
    for fold in (1, 2):
        tr = a[a.season.isin(F[fold])].reset_index(drop=True)
        s_train = D.share_table(tr)
        for name in FAMILY:
            lf = level_for(name, fold, a, games, L)
            off = D.row_offset(tr, lf, s_train)
            m = BM.fit_b0(tr, off)
            p = BM.predict_b0(m, tr, off)
            for season in F[fold]:
                for scope, mask in (("overall", (tr.grp <= 2)), ("ES", (tr.grp == 0))):
                    mk = ((tr.season == season) & mask).to_numpy()
                    rows.append(dict(fold=fold, construction=name, season=season, scope=scope, n=int(mk.sum()),
                                     pred_pct=100 * p[mk].mean(), act_pct=100 * tr.y.to_numpy()[mk].mean(),
                                     judged=season in JUDGED[fold]))
        print(now(), "fold", fold, "done", flush=True)
    P = pd.DataFrame(rows)
    P["diff_pp"] = P.pred_pct - P.act_pct
    P.to_csv(RES / "step0_parity_long.csv", index=False)
    J = P[P.judged]
    summ = []
    for name in FAMILY:
        j = J[J.construction == name]
        mx = j.diff_pp.abs().max()
        summ.append(dict(construction=name, family=FAMILY[name], max_abs_pp=mx, all_pass=bool(mx <= TOL)))
    S = pd.DataFrame(summ)
    cand = S[~S.construction.isin(["none", "O"])]
    passers = cand[cand.all_pass]
    order = ("M0", "E", "M1", "M2")
    if len(passers):
        fam = min(passers.family, key=order.index)
        sel = passers[passers.family == fam].sort_values("max_abs_pp").construction.iloc[0]
        rule = "simplest passer"
    else:
        best = {f: cand[cand.family == f].sort_values("max_abs_pp").iloc[0] for f in order}
        mn = min(v.max_abs_pp for v in best.values())
        sel = None
        for f in order:
            if best[f].max_abs_pp <= mn + 0.1:
                sel = best[f].construction
                break
        rule = "fallback: smallest max |parity|, ties within 0.1 pp to the simpler construction (failure listed)"
    out = dict(selected=sel, rule=rule, tol_pp=TOL, summary=S.to_dict("records"))
    (RES / "step0.json").write_text(json.dumps(out, indent=1, default=float))
    L_ = ["# SB-R1 step 1: block-share level constructions and parity (Lane B, 2026-10-16)", "",
          "Spec (binding): `docs/models/block/experiments.md` SB-R1. Script: `scripts/exp_block_sbr1_step1.py`; library: "
          "`src/nhl_sim/block/data.py`; level table `data/processed/block/level_v1.parquet` (created_at < puck_drop asserted).", "",
          "B0 = one-hot (strength group x period type) + level offset logit(s_asof) - logit(s_train), coefficient 1, fit on the "
          "fold's training rows (ES level group also serves EN rows, labelled). Parity = B0 predicted minus actual block share "
          "(pp) per training season, over graded rows (ES + PP + PK) and over ES. Tolerance +/-0.3 pp. The first season "
          "(2021-22) has no prior and is shown, not judged. E: on fold 1 every training row is era 1, so E = no level "
          "there (era-2 test games fall back to the pooled training share).", "",
          "Block share by season (all attempts): see section 'Raw block share'.", ""]
    piv = P.pivot_table(index=["fold", "construction", "season"], columns="scope", values="diff_pp")
    piv["judged"] = P[P.scope == "overall"].set_index(["fold", "construction", "season"]).judged
    L_ += ["## Parity (pred - actual, pp)", "", piv.round(3).to_markdown(), "", "## Summary over judged cells", "",
           S.round(3).to_markdown(index=False), "", f"## Selection: **{sel}** ({rule})", ""]
    shr = a[a.grp <= 2].groupby(["season", "grp"]).y.mean().unstack().mul(100).round(2)
    shr.columns = ["ES", "PP", "PK"]
    L_ += ["## Raw block share by season (%, goalie-in attempts)", "", shr.to_markdown(), ""]
    REPORT.write_text("\n".join(L_), encoding="utf-8")
    print(S.round(3).to_string()); print("selected", sel, "-", rule)


if __name__ == "__main__":
    main()
