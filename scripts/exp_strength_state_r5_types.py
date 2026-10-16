"""SS-R5 steps 2: fit T1-T3, tune T3's prior strength k on fold 1, grade T1-T3 on fold 2 (multinomial LL per penalty,
paired game-block bootstrap), apply the decision rule. Writes results/strength_state_r5/ (models, predictions, report
fragment) and docs-ready tables. T1-T3 are convex multinomial logits (no random seed): the noise floor (spec-identical
retrain under another seed) is exactly zero by construction; the 2 SE bootstrap rule is the operative threshold.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.strength_state import models as M  # noqa: E402
from nhl_sim.strength_state import models_r5 as R5  # noqa: E402

OUT = Path("results/strength_state_r5")
KS = (50, 150, 450)
F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024
F2_TRAIN, F2_TEST = [20212022, 20222023, 20232024], 20242025
NB, SEED = 2000, 20261016


def frames(train, test, k):
    last = train[-1]
    tr = R5.type_frame(train, last, k)
    te = R5.type_frame([test], last, k)
    return tr, te


def ll(p, kk):
    return np.log(p[np.arange(len(kk)), kk])


def per_game(t, v):
    return pd.Series(v).groupby(t.game_id.to_numpy()).agg(["sum", "size"])


def paired_boot(t, a, b):
    """mean(a-b) per penalty, game-block bootstrap SE and 95% CI."""
    pg = per_game(t, a - b)
    s, n = pg["sum"].to_numpy(), pg["size"].to_numpy()
    G = len(s)
    w = np.random.default_rng(SEED).multinomial(G, np.ones(G) / G, size=NB).astype(float)
    bm = (w @ s) / (w @ n)
    return s.sum() / n.sum(), bm.std(ddof=1), np.percentile(bm, [2.5, 97.5])


def single_boot(t, a):
    pg = per_game(t, a)
    s, n = pg["sum"].to_numpy(), pg["size"].to_numpy()
    G = len(s)
    w = np.random.default_rng(SEED).multinomial(G, np.ones(G) / G, size=NB).astype(float)
    return s.sum() / n.sum(), ((w @ s) / (w @ n)).std(ddof=1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    L = ["# SS-R5 step 2 raw output", ""]
    # ---- tune k on fold 1 (T3 only)
    tune = []
    for k in KS:
        tr, te = frames(F1_TRAIN, F1_TEST, k)
        m = R5.fit(tr, "T3")
        p = R5.predict(m, te)
        v = ll(p, te.k.to_numpy())
        tune.append(dict(k=k, fold1_T3_ll_per_penalty=float(v.mean()), n_test=len(te)))
        print("tune", tune[-1], flush=True)
    kbest = max(tune, key=lambda d: d["fold1_T3_ll_per_penalty"])["k"]
    # fold-1 all arms for information (k = tuned)
    tr1, te1 = frames(F1_TRAIN, F1_TEST, kbest)
    f1 = {a: float(ll(R5.predict(R5.fit(tr1, a), te1), te1.k.to_numpy()).mean()) for a in ("T1", "T2", "T3")}
    L += ["## Fold 1 tuning of T3 prior strength (train 2021-22 + 2022-23, test 2023-24)", "",
          pd.DataFrame(tune).to_markdown(floatfmt=".5f", index=False), "", f"Selected k = {kbest} (max fold-1 LL).", "",
          "Fold-1 LL per penalty, all arms at the selected k (information only): " + json.dumps(f1), ""]
    # ---- fold 2
    tr, te = frames(F2_TRAIN, F2_TEST, kbest)
    kk = te.k.to_numpy()
    models, preds = {}, {}
    for a in ("T1", "T2", "T3"):
        models[a] = R5.fit(tr, a)
        preds[a] = R5.predict(models[a], te)
        (OUT / f"{a}_fold2.json").write_text(json.dumps(dict(models[a], k_off=kbest)))
        np.save(OUT / f"fold2_type_{a}.npy", preds[a])
    te[["game_id", "game_type", "team", "team_id", "st", "sc", "period", "k", "taken_own", "taken_opp", "off_own",
        "off_opp"]].to_parquet(OUT / "fold2_types_r5.parquet", index=False)
    lls = {a: ll(preds[a], kk) for a in preds}
    rows = []
    for a in preds:
        m, se = single_boot(te, lls[a])
        rows.append(dict(arm=a, ll_per_penalty=m, se=se))
    T = pd.DataFrame(rows).set_index("arm")
    comps = {}
    for a, b in (("T2", "T1"), ("T3", "T1"), ("T3", "T2")):
        m, se, ci = paired_boot(te, lls[a], lls[b])
        comps[f"{a} minus {b}"] = dict(diff=m, se=se, lo=ci[0], hi=ci[1], gt_2se=bool(m > 2 * se))
    L += ["## Fold 2 (train through 2023-24, test 2024-25), multinomial LL per penalty (higher is better)", "",
          f"n penalties in test = {len(te)}, games = {te.game_id.nunique()}. Prior strength k = {kbest}.", "",
          T.to_markdown(floatfmt=".5f"), "", "Paired differences (game-block bootstrap, 2000 reps):", "",
          pd.DataFrame(comps).T.to_markdown(floatfmt=".5f"), ""]
    # decision rule: more complex beats simpler only by > 2 SE
    sel = "T1"
    if comps["T2 minus T1"]["gt_2se"]:
        sel = "T2"
    if comps["T3 minus T2"]["gt_2se"] and (sel == "T2" or comps["T3 minus T1"]["gt_2se"]):
        sel = "T3"
    elif sel == "T1" and comps["T3 minus T1"]["gt_2se"]:
        sel = "T3"
    L += [f"**Decision (fold 2, 2 SE rule, ties to simpler): selected arm {sel}.**", ""]
    # ---- segments
    seg = []
    for nm, msk in (("RS", te.game_type.to_numpy() == 2), ("PO", te.game_type.to_numpy() == 3)):
        sub = te[msk].reset_index(drop=True)
        r = dict(segment=nm, n=int(msk.sum()))
        for a in ("T2", "T3"):
            m, se, ci = paired_boot(sub, lls[a][msk], lls["T1"][msk])
            r[f"{a}-T1"] = m
            r[f"{a}-T1 SE"] = se
        seg.append(r)
    L += ["### Paired difference vs T1 by segment (PO UNDERPOWERED)", "", pd.DataFrame(seg).to_markdown(floatfmt=".5f", index=False), ""]
    # ---- per strength state
    sr = []
    for s in range(6):
        msk = te.st.to_numpy() == s
        r = dict(state=M.STRENGTH_NAMES[s], n=int(msk.sum()))
        if msk.sum() >= 30:
            for a in ("T2", "T3"):
                m, se, _ = paired_boot(te[msk].reset_index(drop=True), lls[a][msk], lls["T1"][msk])
                r[f"{a}-T1"], r[f"{a}-T1 SE"] = m, se
        else:
            r["note"] = "UNDERPOWERED"
        sr.append(r)
    L += ["### Paired difference vs T1 by strength state (team view)", "", pd.DataFrame(sr).to_markdown(floatfmt=".5f", index=False), ""]
    # ---- responsiveness: coincidental share by own taken-rating quintile (event level) and per team
    co = (kk == 3).astype(float)
    q = pd.qcut(te.taken_own.rank(method="first"), 5, labels=False).to_numpy()
    resp = pd.DataFrame({"q": q, "actual": co, **{a: preds[a][:, 3] for a in preds}}).groupby("q").agg(
        n=("actual", "size"), actual=("actual", "mean"), T1=("T1", "mean"), T2=("T2", "mean"), T3=("T3", "mean"))
    L += ["### Coincidental share by own taken-rating quintile of the penalty event (fold 2): actual vs predicted", "",
          resp.to_markdown(floatfmt=".4f"), "",
          f"Q5-Q1: actual {resp.actual.iloc[4] - resp.actual.iloc[0]:+.4f}, T1 {resp.T1.iloc[4] - resp.T1.iloc[0]:+.4f}, "
          f"T2 {resp.T2.iloc[4] - resp.T2.iloc[0]:+.4f}, T3 {resp.T3.iloc[4] - resp.T3.iloc[0]:+.4f}.", ""]
    tm = pd.DataFrame({"team_id": te.team_id.to_numpy(), "actual": co, **{a: preds[a][:, 3] for a in preds}}).groupby(
        "team_id").agg(n=("actual", "size"), actual=("actual", "mean"), T1=("T1", "mean"), T2=("T2", "mean"), T3=("T3", "mean"))
    cr = {a: float(np.corrcoef(tm.actual, tm[a])[0, 1]) for a in ("T1", "T2", "T3")}
    L += [f"Per-team (n=32 teams, ~{int(tm.n.mean())} penalties each, every cell UNDERPOWERED individually) correlation of "
          f"predicted vs actual coincidental share: {json.dumps({a: round(v, 3) for a, v in cr.items()})}.", ""]
    # fitted coefficients
    names = lambda a: [f"season{s}" for s in models[a]["seasons_ref"][1:]] + [f"st{k}" for k in range(1, 6)] + \
        ["sc0", "sc1", "sc3", "sc4", "per2", "per3", "per4"] + R5.RATING_FEATURES[a]
    cf = pd.DataFrame(np.asarray(models["T3"]["coef"]).T, index=names("T3"), columns=M.TYPE_CLASSES)
    L += ["### T3 coefficients (log-odds vs class 0 baseline is not imposed; sklearn multinomial)", "", cf.to_markdown(floatfmt=".3f"), ""]
    res = dict(k=kbest, selected=sel, tune=tune, fold1=f1, fold2=T.reset_index().to_dict("records"), comps=comps)
    (OUT / "types_result.json").write_text(json.dumps(res, indent=1, default=float))
    (OUT / "types_report_fragment.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
