"""SM-R2 step 1: tier level constructions, parity table with the oracle row, selection (docs/models/miss/experiments.md SM-R2).
Before any S1t fit. S0t (cell x type x group table + tier level offset + ten intercepts) is fit on each fold's training rows with
each construction as the offset; parity = S0t predicted minus actual miss share per genuine-prior training season (2021-22 has no
prior season: shown, not judged), judged on overall graded rows and each danger tier (high / medium / low), tolerance +/-0.5 pp
(SM-R2). ES and per (group x tier) cells are reported. Selection: SB-R1 rule with the D35 exclusion (E reported, not selectable):
simplest passer (M0 < M1 < M2; within a family the smaller max |parity|), else the smallest max |parity| with ties within 0.1 pp
to the simpler construction; failure listed."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.miss import data as M  # noqa: E402
from nhl_sim.miss import models as MM  # noqa: E402
from nhl_sim.miss import tier as T  # noqa: E402
from nhl_sim.shot_attribute.tables import TIER_NAMES, TIER_OF_CELL  # noqa: E402

RES = Path("results/miss_sm_r2")
REPORT = Path("docs/tests/miss_sm_r2_step1_2026-10-16.md")
F = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}
JUDGED = {1: [20222023], 2: [20222023, 20232024]}
TOL = 0.5
FAMILY = {"none": "none", "M0": "M0", "E": "E", "M1_K500": "M1", "M1_K2000": "M1", "M1_K8000": "M1",
          "M2_H30": "M2", "M2_H60": "M2", "O": "O"}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def level_for(name, fold, a_all, games, L):
    gm = games.sort_values(["date", "game_id"]).reset_index(drop=True)
    tr = a_all[a_all.season.isin(F[fold])]
    if name == "none":
        S = np.tile(T.share_table(tr), (len(gm), 1))
    elif name == "E":
        S = T.era_level(tr, gm)
    else:
        return L[L.construction == name]
    f = pd.DataFrame({"game_id": gm.game_id.to_numpy()})
    for g in range(T.NC):
        f[f"s_{g}"] = S[:, g]
    return f


def main():
    RES.mkdir(parents=True, exist_ok=True)
    games = pd.read_parquet(M.OUT / "games_v1.parquet")
    a = M.load_rows()
    L = pd.read_parquet(M.OUT / "level_tier_v2.parquet")
    a = a.merge(games[["game_id"]], on="game_id")
    a["l0"] = (a.grp.astype(np.int64) * 2 + a.ptype).astype(np.int8)
    a["tier"] = TIER_OF_CELL[a.cell.to_numpy()]
    rows = []
    for fold in (1, 2):
        tr = a[a.season.isin(F[fold])].reset_index(drop=True)
        s_train = T.share_table(tr)
        for name in FAMILY:
            lf = level_for(name, fold, a, games, L)
            off = T.row_offset(tr, lf, s_train)
            m = MM.fit_s0(tr, off)
            p = MM.predict_s0(m, tr, off)
            y = tr.y.to_numpy()
            for season in F[fold]:
                base = ((tr.season == season) & (tr.grp <= 2)).to_numpy()
                scopes = {"overall": base, "ES": base & (tr.grp == 0).to_numpy()}
                for k, nm in enumerate(TIER_NAMES):
                    scopes[f"tier {nm}"] = base & (tr.tier == k).to_numpy()
                    for gname, gk in (("ES", 0), ("PP", 1), ("PK", 2)):
                        scopes[f"{nm}/{gname}"] = base & (tr.tier == k).to_numpy() & (tr.grp == gk).to_numpy()
                for scope, mk in scopes.items():
                    rows.append(dict(fold=fold, construction=name, season=season, scope=scope, n=int(mk.sum()),
                                     pred_pct=100 * p[mk].mean(), act_pct=100 * y[mk].mean(),
                                     judged=(season in JUDGED[fold]) and (scope == "overall" or scope.startswith("tier "))))
        print(now(), "fold", fold, "done", flush=True)
    P = pd.DataFrame(rows)
    P["diff_pp"] = P.pred_pct - P.act_pct
    P.to_csv(RES / "step1_parity_long.csv", index=False)
    J = P[P.judged]
    S = pd.DataFrame([dict(construction=n + (" (not selectable, D35)" if n == "E" else ""), family=FAMILY[n],
                           max_abs_pp=J[J.construction == n].diff_pp.abs().max(),
                           all_pass=bool(J[J.construction == n].diff_pp.abs().max() <= TOL)) for n in FAMILY])
    cand = S[~S.construction.isin(["none", "O", "E (not selectable, D35)"])]
    passers = cand[cand.all_pass]
    order = ("M0", "M1", "M2")
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
    L_ = ["# SM-R2 step 1: tier-specific miss level constructions and parity (Lane M2, 2026-10-16)", "",
          "Spec (binding): `docs/models/miss/experiments.md` SM-R2. Script `scripts/exp_miss_smr2_step1.py`; library "
          "`src/nhl_sim/miss/tier.py`; level table `data/processed/miss/level_tier_v2.parquet` (created_at < puck_drop asserted). "
          "Generated " + now() + ".", "",
          "Level cell = (ES+EN / PP / PK) x (high / medium / low danger tier of the location cell). M1 / M2 pseudo-attempts K are "
          "split over the three tiers of a group by the tier's share of the group's attempts in the prior season (a labelled "
          "construction choice implementing 'scaled by the tier's share of attempts'). S0t = recorded cell x type x group table "
          "(K = 20, as SM-R1) + tier level offset + ten (group x period type) intercepts. Parity = S0t predicted minus actual miss "
          "share (pp) per training season; judged = overall graded rows and each of 3 tiers, +/-0.5 pp, genuine-prior seasons only "
          "(2022-23 fold 1; 2022-23 and 2023-24 fold 2). ES and tier x group cells are reported in the long csv "
          "`results/miss_sm_r2/step1_parity_long.csv`. 'none' = training-pooled level (no as-of), E = era-pooled "
          "(not selectable, D35), O = oracle.", "",
          "## Parity, judged scopes (pred - actual, pp)", ""]
    Q = P[(P.scope == "overall") | P.scope.str.startswith("tier ") | (P.scope == "ES")]
    piv = Q.pivot_table(index=["fold", "construction", "season"], columns="scope", values="diff_pp")[
        ["overall", "ES", "tier high", "tier medium", "tier low"]]
    piv["judged"] = P[P.scope == "overall"].set_index(["fold", "construction", "season"]).judged
    L_ += [piv.round(3).to_markdown(), "", "## Summary over judged cells", "", S.round(3).to_markdown(index=False), "",
           f"## Selection: **{sel}** ({rule})", ""]
    sh = a[a.grp <= 2].groupby(["season", "tier"]).y.mean().unstack().mul(100).round(2)
    sh.columns = list(TIER_NAMES)
    L_ += ["## Raw miss share by season and tier (% of unblocked ES / PP / PK attempts)", "", sh.to_markdown(), ""]
    REPORT.write_text("\n".join(L_), encoding="utf-8")
    print(S.round(3).to_string())
    print("selected", sel, "-", rule)


if __name__ == "__main__":
    main()
