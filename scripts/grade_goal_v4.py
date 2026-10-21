"""G-R4 blind grader (docs/models/goal/experiments.md G-R4; the G-R3 checks frozen: `grade_goal_v3.grade_label` is the
check code, imported unchanged). One code path scores every hash-labelled arm BEFORE `labels_sealed.json` is opened.

Primary: Bernoulli LL per SOG (gated rows: 5v5, PP-for, PK), pairwise differences with a 1,000-resample game-block
bootstrap SE (ratio of resampled sums). LL per game reported too.
Eligibility (both folds; fold 1 = the D13 guard, same checks):
  every G-R3 bias check (save % overall / group / tier / month, RS goals from SOG), goalie and team R in [0.8, 1.2]
  (point estimate gates, D18), AND served / actual conversion by score bucket relative to tied within +/-3% for each of
  trail 2+, trail 1, lead 1, lead 2+ (gated rows; point estimate; game-bootstrap SE reported).
Decision (fold 2): among arms eligible on fold 2 with the fold-1 guard holding, those not worse than C1s by > 2 SE on
LL per SOG; the best LL among them; the simplest (C1s < C1s-sa < C1s-sp < C1s-sap) within 2 SE of the best.
Floor 0 (deterministic logistic; stated). C0 is flat in goalie and team and not adoptable (D24).

    grade_goal_v4.py --fold 1   -> docs/tests/goal_g_r4_grade_2026-10-21.md (fold-1 diagnostic + D13 guard, written first)
    grade_goal_v4.py --fold 2   -> the same file, fold-2 selection appended
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import grade_goal_v3 as G3  # noqa: E402
from nhl_sim.goal import score_asof as SA  # noqa: E402

RES = ROOT / "results/goal_g_r4"
REPORT = ROOT / "docs/tests/goal_g_r4_grade_2026-10-21.md"
ARMS = ("C0", "C1s", "C1s-sa", "C1s-sp", "C1s-sap")
ORDER = ("C1s", "C1s-sa", "C1s-sp", "C1s-sap")          # complexity
NB, BSEED = 1000, 20261021
TOL3 = 0.03
BAND = G3.BAND


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


def bucket_check(p, r, gp_all, W):
    g = (r.sg <= 2).to_numpy()
    b = SA.bucket(r)[g]
    games, gp = np.unique(gp_all[g], return_inverse=True)
    rat, se = SA.bucket_ratio(p[g], r.y.to_numpy(float)[g], b, gp, len(games), W[:, games])
    rows = []
    for k in range(5):
        rows.append(dict(bucket=SA.B_NAMES[k], n_sog=int((b == k).sum()), goals=int(r.y.to_numpy()[g][b == k].sum()),
                         pred_pct=100 * p[g][b == k].mean(), act_pct=100 * r.y.to_numpy()[g][b == k].mean(),
                         ratio_vs_tied=rat[k], se=se[k],
                         status="ref" if k == SA.TIED else ("PASS" if abs(rat[k] - 1) <= TOL3 else "FAIL")))
    return pd.DataFrame(rows)


def period_bucket(p, r):
    g = (r.sg <= 2).to_numpy() & (r.period <= 3).to_numpy()
    x = pd.DataFrame({"period": r.period.to_numpy()[g], "bucket": SA.bucket(r)[g], "p": p[g], "y": r.y.to_numpy(float)[g]})
    t = x.groupby(["period", "bucket"]).agg(n=("p", "size"), pred=("p", "sum"), goals=("y", "sum"))
    t["pred_over_act"] = t.pred / t.goals
    t = t.reset_index()
    t["bucket"] = t.bucket.map(dict(enumerate(SA.B_NAMES)))
    return t.pivot(index="period", columns="bucket", values="pred_over_act")[list(SA.B_NAMES)]


def grade(fold):
    d = RES / f"fold{fold}"
    r = pd.read_parquet(d / f"fold{fold}_rows.parquet")
    games = np.sort(r.game_id.unique())
    gp = np.searchsorted(games, r.game_id.to_numpy())
    G = len(games)
    W = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)
    g = (r.sg <= 2).to_numpy()
    n_game = np.bincount(gp[g], minlength=G).astype(float)
    res, bc, pb = {}, {}, {}
    for f in sorted(d.glob(f"fold{fold}_pred_*.npy")):
        h = f.stem.rsplit("_", 1)[1]
        p = np.load(f).astype(np.float64)
        if p.shape != (len(r),):
            raise ValueError(f"{h}: shape {p.shape}")
        res[h] = G3.grade_label(p, r, gp, G)
        bc[h] = bucket_check(p, r, gp, W)
        pb[h] = period_bucket(p, r)
        print(now(), "graded", h, f"LL/SOG {res[h]['ll_sog']:.5f}", flush=True)
    pairs = []
    hs = sorted(res)
    for i in hs:
        for j in hs:
            if i != j:
                dv = res[i]["ll_game"] - res[j]["ll_game"]
                per_sog_b = (W @ dv) / (W @ n_game)
                pairs.append(dict(a=i, b=j, diff_per_sog=dv.sum() / n_game.sum(), se_sog=float(per_sog_b.std()),
                                  diff_per_game=dv.mean(), se_game=float(np.std(W @ dv / G))))
    pairs = pd.DataFrame(pairs)
    lab = json.loads((d / "labels_sealed.json").read_text())       # unsealed only now
    name = {v: k for k, v in lab.items()}
    print(now(), "unsealed", name, flush=True)
    return r, res, bc, pb, pairs, name, G


def write(fold):
    r, res, bc, pb, pairs, name, G = grade(fold)
    h = {v: k for k, v in name.items()}
    assert set(ARMS) <= set(h)
    rows = []
    for a in ARMS:
        R = res[h[a]]
        B = R["bias"]
        fails = B[B.status == "FAIL"]
        bf = [f"{c} {v:+.2f}pp" for c, v in zip(fails.cell, fails.diff_pp)]
        if R["goals"]["status"] == "FAIL":
            bf.append(f"goals/game {R['goals']['diff_pct']:+.2f}%")
        gq, tq = R["resp"][("goalie", "gated")], R["resp"][("team", "gated")]
        C = bc[h[a]].set_index("bucket")
        q = pairs[(pairs.a == h[a]) & (pairs.b == h["C1s"])]
        rows.append(dict(arm=a, ll_sog=R["ll_sog"],
                         ll_sog_vs_C1s=0.0 if a == "C1s" else float(q.diff_per_sog.iloc[0]),
                         se_sog=np.nan if a == "C1s" else float(q.se_sog.iloc[0]),
                         sv_overall_pp=float(B[B.level == "overall"].diff_pp.iloc[0]), goals_pct=R["goals"]["diff_pct"],
                         bias_fails=", ".join(bf) or "none", R_goalie=gq["R"], R_team=tq["R"],
                         **{f"r_{b}": float(C.loc[b, "ratio_vs_tied"]) for b in SA.B_NAMES if b != "tied"},
                         bucket_fails=", ".join(f"{b} {C.loc[b, 'ratio_vs_tied']:.3f}" for b in C.index
                                                if C.loc[b, "status"] == "FAIL") or "none"))
    S = pd.DataFrame(rows).set_index("arm")
    S["bias_gate"] = np.where(S.bias_fails == "none", "PASS", "FAIL")
    S["resp_gate"] = [("PASS" if (BAND[0] <= g_ <= BAND[1] and BAND[0] <= t_ <= BAND[1]) else "FAIL")
                      for g_, t_ in zip(S.R_goalie, S.R_team)]
    S.loc["C0", "resp_gate"] = "FAIL (flat, D24)"
    S["bucket_gate"] = np.where(S.bucket_fails == "none", "PASS", "FAIL")
    S["all_checks"] = (S.bias_gate == "PASS") & (S.resp_gate == "PASS") & (S.bucket_gate == "PASS")
    hn = {v: k for k, v in h.items()}
    P = pairs.assign(a=pairs.a.map(hn), b=pairs.b.map(hn))
    order = {a: i for i, a in enumerate(ARMS)}
    P = P[P.a.map(order) > P.b.map(order)].sort_values(["a", "b"])
    P["z_sog"] = P.diff_per_sog / P.se_sog
    L = [f"## Fold {fold} ({'selection' if fold == 2 else 'diagnostic + D13 guard'}): {r.season.iloc[0]} test, "
         f"{int((r.sg <= 2).sum()):,} gated SOG ({len(r):,} in scope), {G} games", "",
         f"Generated {now()} by `scripts/grade_goal_v4.py --fold {fold}` (blind: every label scored before "
         "`labels_sealed.json` was opened; salt `G-R4-2026-10-21`). Floor 0 (deterministic logistic; stated).", "",
         "### Summary", "", md(S.drop(columns=["bias_fails"]), ".4f"), "",
         "Bias failures: " + "; ".join(f"{a}: {S.loc[a, 'bias_fails']}" for a in ARMS), "",
         "- ll_sog_vs_C1s = LL per gated SOG minus C1s's (nats), game-block bootstrap SE. r_* = served / actual conversion "
         "of the bucket relative to tied (gated rows), band +/-3%.", "",
         "### Pairwise LL differences (a minus b)", "", md(P.set_index(["a", "b"]), ".6f"), ""]
    for a in ARMS:
        R = res[h[a]]
        RR = pd.DataFrame({" ".join(k): {kk: (str(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}
                           for k, v in R["resp"].items()}).T
        L += [f"### {a}", "", "Score bucket check (gated rows; served / actual relative to tied):", "",
              md(bc[h[a]].set_index("bucket"), ".4f"), "",
              "Predicted / actual goals by period x bucket (gated, regulation; no gate):", "", md(pb[h[a]], ".3f"), "",
              "Save percentage, predicted vs actual:", "", md(R["bias"].set_index(["level", "cell"]), ".3f"), "",
              f"Goals from SOG, regular season: {R['goals']['pred_per_game']:.4f} predicted vs {R['goals']['act_per_game']:.4f} "
              f"actual per game ({R['goals']['games']} games): {R['goals']['diff_pct']:+.2f}% -> {R['goals']['status']}.", "",
              "Responsiveness (decile goal % predicted / actual):", "", md(RR, ".3f"), ""]
        if a != "C0":
            L += ["Per goalie (n >= 500 gated SOG):", "", md(R["goalies"], ".3f"), "",
                  f"Goalies with |z| > 2: {int((R['goalies'].z.abs() > 2).sum())} of {len(R['goalies'])}.", "",
                  "Per shooting team (no gate):", "", md(R["shooting team"], ".3f"), ""]
    out = dict(fold=fold, summary=S.reset_index().to_dict("records"), pairs=P.to_dict("records"))
    sel = None
    if fold == 1:
        L += ["### D13 guard (fold 1, every arm: the same checks)", ""]
        for a in ORDER:
            L.append(f"- {a}: bias {S.loc[a, 'bias_gate']}, R {S.loc[a, 'resp_gate']} (goalie {S.loc[a, 'R_goalie']:.3f}, "
                     f"team {S.loc[a, 'R_team']:.3f}), bucket {S.loc[a, 'bucket_gate']} -> "
                     f"{'HOLDS' if S.loc[a, 'all_checks'] else 'FAILS'}")
        L.append("")
        out["guard"] = {a: bool(S.loc[a, "all_checks"]) for a in ORDER}
    else:
        g1 = json.loads((RES / "grade_fold1.json").read_text())["guard"]
        L += ["### Decision rule (fold 2)", ""]
        el = []
        for a in ORDER:
            ok2 = bool(S.loc[a, "all_checks"])
            L.append(f"- {a}: fold-2 checks {'PASS' if ok2 else 'FAIL'} (bias {S.loc[a, 'bias_gate']}, R {S.loc[a, 'resp_gate']}, "
                     f"bucket {S.loc[a, 'bucket_gate']}: {S.loc[a, 'bucket_fails']}); fold-1 guard "
                     f"{'holds' if g1[a] else 'fails'} -> {'ELIGIBLE' if ok2 and g1[a] else 'not eligible'}")
            if ok2 and g1[a]:
                el.append(a)

        def diff(a, b):
            q = P[((P.a == a) & (P.b == b))]
            if len(q):
                return float(q.diff_per_sog.iloc[0]), float(q.se_sog.iloc[0])
            q = P[((P.a == b) & (P.b == a))]
            return -float(q.diff_per_sog.iloc[0]), float(q.se_sog.iloc[0])
        ok = []
        for a in el:
            if a == "C1s":
                ok.append(a)
                continue
            dv, se = diff(a, "C1s")
            fine = dv >= -2 * se
            L.append(f"- {a} vs C1s: {dv:+.6f} nats/SOG (SE {se:.6f}) -> {'not worse by > 2 SE' if fine else 'WORSE by > 2 SE'}")
            if fine:
                ok.append(a)
        if ok:
            best = max(ok, key=lambda a: S.loc[a, "ll_sog"])
            L.append(f"- Best LL among the remaining: {best}.")
            for a in ORDER:
                if a not in ok:
                    continue
                if a == best:
                    sel = a
                    break
                dv, se = diff(a, best)
                L.append(f"- {a} vs {best}: {dv:+.6f} (SE {se:.6f}) -> {'within 2 SE: simpler wins' if dv >= -2 * se else 'not within 2 SE'}")
                if dv >= -2 * se:
                    sel = a
                    break
        L += [f"- **Selected: {sel}**" if sel else "- **No arm eligible: the goal model stays C1s; the PM rules.**", ""]
        out["selected"] = sel
        out["eligible"] = el
    text = "\n".join(L) + "\n"
    if fold == 1:
        REPORT.write_text("# G-R4 blind grade (Lane G4, 2026-10-21)\n\nSpec: `docs/models/goal/experiments.md` G-R4 (G-R3 / "
                          "D40 frozen). Fold 1 is written first (diagnostic + the D13 guard for every arm); fold 2 is the "
                          "selection, appended after.\n\n" + text, encoding="utf-8")
    else:
        with REPORT.open("a", encoding="utf-8") as fh:
            fh.write("\n" + text)
    (RES / f"grade_fold{fold}.json").write_text(json.dumps(out, indent=1, default=float))
    print(md(S.drop(columns=["bias_fails"]), ".4f"))
    print("\n".join(L[-12:]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, choices=[1, 2], required=True)
    write(ap.parse_args().fold)
