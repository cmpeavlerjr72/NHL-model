"""SM-R1 step 1: level constructions, parity table with the oracle row, selection (docs/models/miss/experiments.md SM-R1).
Runs BEFORE any S1 / S2 fit. S0 (recorded cell x type x strength-group frequency + level offset) is fit on each fold's
training rows with each construction as the offset; parity = S0 miss share minus actual per genuine-prior training season,
overall (ES / PP / PK graded rows) and ES, tolerance +/-0.3 pp. 2021-22 has no prior season and is shown, not judged.
Selection (LC-2 / SB-R1 rule): simplest passer (M0 < E < M1 < M2; within M1 / M2 the smaller max |parity|), else the smallest
max |parity| with ties within 0.1 pp to the simpler construction; the failure is listed and the run proceeds.
Also reports the post / crossbar share of misses by season (data only, no decision).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.miss import data as M  # noqa: E402
from nhl_sim.miss import models as MM  # noqa: E402

RES = Path("results/miss_sm_r1")
REPORT = Path("docs/tests/miss_sm_r1_step1_2026-10-16.md")
F = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}
JUDGED = {1: [20222023], 2: [20222023, 20232024]}
TOL = 0.3
FAMILY = {"none": "none", "M0": "M0", "E": "E", "M1_K500": "M1", "M1_K2000": "M1", "M1_K8000": "M1",
          "M2_H30": "M2", "M2_H60": "M2", "O": "O"}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def level_for(name, fold, a_all, games, L):
    if name == "none":
        f = L[L.construction == "M0"][["game_id"]].copy()
        s_tr = M.share_table(a_all[a_all.season.isin(F[fold])])
        for g in range(3):
            f[f"s_{g}"] = s_tr[g]
        return f
    if name == "E":
        gm = games.sort_values(["date", "game_id"]).reset_index(drop=True)
        S = M.era_level(a_all[a_all.season.isin(F[fold])], gm)
        f = pd.DataFrame({"game_id": gm.game_id.to_numpy()})
        for g in range(3):
            f[f"s_{g}"] = S[:, g]
        return f
    return L[L.construction == name]


def postbar():
    rows = []
    for s in M.SEASONS:
        ev = pd.read_parquet(M.PROCESSED / "events" / f"events_{s}.parquet",
                             columns=["game_id", "sort_order", "event", "reason"])
        ev = ev[ev.event == "MISS"]
        a = pd.read_parquet(M.SA / f"attempt_attr_v1_{s}.parquet", columns=["game_id", "sort_order", "event", "grp"])
        a = a[a.event == "MISS"].merge(ev[["game_id", "sort_order", "reason"]], on=["game_id", "sort_order"], how="left",
                                       validate="one_to_one")
        pb = a.reason.isin(["hit-left-post", "hit-right-post", "hit-crossbar", "goalpost"])   # 2021-23 feed codes posts "goalpost"
        n_un = int(len(pd.read_parquet(M.SA / f"attempt_attr_v1_{s}.parquet", columns=["blocked"]).query("~blocked")))
        es = (a.grp == 0).to_numpy()
        rows.append(dict(season=s, misses=len(a), post_bar=int(pb.sum()), pct_of_misses=100 * pb.mean(),
                         pct_of_unblocked=100 * pb.sum() / n_un, pct_of_misses_ES=100 * pb[es].mean(),
                         over_net_pct_of_misses=100 * a.reason.isin(["above-crossbar", "over-net"]).mean(),
                         missing_reason=int(a.reason.isna().sum())))
    out = pd.DataFrame(rows)
    out["season"] = out.season.astype(str)
    return out


def main():
    RES.mkdir(parents=True, exist_ok=True)
    games = pd.read_parquet(M.OUT / "games_v1.parquet")
    a = M.load_rows()
    L = pd.read_parquet(M.OUT / "level_v1.parquet")
    a = a.merge(games[["game_id"]], on="game_id")
    a["l0"] = (a.grp.astype(np.int64) * 2 + a.ptype).astype(np.int8)
    rows = []
    for fold in (1, 2):
        tr = a[a.season.isin(F[fold])].reset_index(drop=True)
        s_train = M.share_table(tr)
        for name in FAMILY:
            lf = level_for(name, fold, a, games, L)
            off = M.row_offset(tr, lf, s_train)
            m = MM.fit_s0(tr, off)
            p = MM.predict_s0(m, tr, off)
            for season in F[fold]:
                for scope, mask in (("overall", (tr.grp <= 2)), ("ES", (tr.grp == 0))):
                    mk = ((tr.season == season) & mask).to_numpy()
                    rows.append(dict(fold=fold, construction=name, season=season, scope=scope, n=int(mk.sum()),
                                     pred_pct=100 * p[mk].mean(), act_pct=100 * tr.y.to_numpy()[mk].mean(),
                                     judged=season in JUDGED[fold]))
        print(now(), "fold", fold, "done", flush=True)
    P = pd.DataFrame(rows)
    P["diff_pp"] = P.pred_pct - P.act_pct
    P.to_csv(RES / "step1_parity_long.csv", index=False)
    J = P[P.judged]
    S = pd.DataFrame([dict(construction=n, family=FAMILY[n], max_abs_pp=J[J.construction == n].diff_pp.abs().max(),
                           all_pass=bool(J[J.construction == n].diff_pp.abs().max() <= TOL)) for n in FAMILY])
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
    (RES / "step1.json").write_text(json.dumps(dict(selected=sel, rule=rule, tol_pp=TOL, summary=S.to_dict("records")),
                                               indent=1, default=float))
    pb = postbar()
    L_ = ["# SM-R1 step 1: miss-share level constructions and parity (Lane M, 2026-10-16)", "",
          "Spec (binding): `docs/models/miss/experiments.md` SM-R1. Script: `scripts/exp_miss_smr1_step1.py`; library "
          "`src/nhl_sim/miss/`; level table `data/processed/miss/level_v1.parquet` (created_at < puck_drop asserted). "
          "Generated " + now() + ".", "",
          "S0 = recorded training-row miss rate per (cell x type x strength group), shrunk (K = 20 pseudo-attempts, a labelled "
          "construction choice, not tuned) + the level offset logit(s_asof) - logit(s_train) per level group (ES+EN, PP, PK) + "
          "ten (strength group x period type) intercepts fitted under the offset. Parity = S0 predicted minus actual miss "
          "share (pp) per training season, over graded rows (ES + PP + PK) and over ES; tolerance +/-0.3 pp. 2021-22 has no "
          "prior season and is shown, not judged. E: on fold 1 every training row is era 1, so E = no level there.", "",
          "## Parity (pred - actual, pp)", ""]
    piv = P.pivot_table(index=["fold", "construction", "season"], columns="scope", values="diff_pp")
    piv["judged"] = P[P.scope == "overall"].set_index(["fold", "construction", "season"]).judged
    L_ += [piv.round(3).to_markdown(), "", "## Summary over judged cells", "", S.round(3).to_markdown(index=False), "",
           f"## Selection: **{sel}** ({rule})", ""]
    shr = a[a.grp <= 2].groupby(["season", "grp"]).y.mean().unstack().mul(100).round(2)
    shr.columns = ["ES", "PP", "PK"]
    shr["n_gated"] = a[a.grp <= 2].groupby("season").size()
    L_ += ["## Raw miss share by season (% of unblocked goalie-in attempts)", "", shr.to_markdown(), "",
           "## Post / crossbar share by season (a post or crossbar shot is a miss in the NHL feed; data only)", "",
           pb.round(3).to_markdown(index=False), ""]
    REPORT.write_text("\n".join(L_), encoding="utf-8")
    print(S.round(3).to_string())
    print("selected", sel, "-", rule)
    print(pb.round(3).to_string())


if __name__ == "__main__":
    main()
