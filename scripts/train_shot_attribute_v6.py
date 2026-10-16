"""SL-R6 trainer: L1x = L0s (levelled by E) + fixed-scale rating tilt along the class log-xG_ref direction + fitted
home / score / rest terms (docs/models/shot_attribute/experiments.md SL-R6; D32; src/nhl_sim/shot_attribute/models_x.py).
Everything else as SL-R4: L0s baseline / strata, EN served L0s only, level E, xG_ref per fold, bias checks (EN
reported), the D28 guard (L1x minus L0s on fold 1), grading, floor (seed-2 start-point retrain).

    train_shot_attribute_v6.py step0   training seasons only (2021-22..2023-24; fold-2 ratings): per-season free fit of
                                       (s_f, s_a) on each construction (SL-R1 rating "orig", Qr, Qa), each season alone
                                       with its own L0s, with SEs; pooled fits for reference; flatness tests.
                                       -> docs/models/shot_attribute/sl_r6_step0.json (committed before step 1)
    train_shot_attribute_v6.py grid    fold 1 only: per construction (Qr, Qa) the free fit s_hat on fold-1 training,
                                       then s = m x s_hat for m in {0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0} (W refit at
                                       fixed s), predicting 2023-24: LL per game (paired game-block bootstrap SE vs the
                                       best cell, 1,000), D32 R for / against on ES rows (deciles of the row's as-of
                                       rating; slope_ratio). Selection: among all 14 cells within 2 SE of the best LL,
                                       the smallest max(|log R_for|, |log R_against|); ties within 0.02 go to Qr, then
                                       to m closest to 1. -> sl_r6_frozen_params.json + sl_r6_grid_fold1.csv
    train_shot_attribute_v6.py fit2    fold-2 fits: L0s, L1x (W refit at the frozen s), L1xs2 (same, seeded start)
    train_shot_attribute_v6.py insample  fold-2 TRAINING rows: L1x within +/-0.5% xG_ref of L0s in every stratum with
                                       n >= 2,000 (SL-R4 check, inherited); exits 3 on a failure
    train_shot_attribute_v6.py fold1   fold-1 fits at the frozen s + hash-labelled 2023-24 predictions
    train_shot_attribute_v6.py guard   D28 guard on fold 1 (every SL-R1 bias check read on L1x MINUS L0s; EN reported) +
                                       oracle-level read (reported); exits 4 on a failure
    train_shot_attribute_v6.py pred2   only after insample AND guard passed: hash-labelled 2024-25 predictions
                                       -> results/shot_attribute_r6 (graded blind: grade_shot_attribute.py --round r6)
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.engine.rules import recording_era  # noqa: E402
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402
from nhl_sim.shot_attribute import mix_level as ML  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute import models_s as MS  # noqa: E402
from nhl_sim.shot_attribute import models_x as MX  # noqa: E402
from nhl_sim.shot_attribute.tables import (GROUP_NAMES, N_CELL, N_CLASS, N_TYPE, OPP_RATING_GROUP,  # noqa: E402
                                           RATING_GROUP, TIER_NAMES, TIER_OF_CELL)

RES = Path("results/shot_attribute_r6")
RES2 = Path("results/shot_attribute_r2")
FROZEN = Path("docs/models/shot_attribute/sl_r6_frozen_params.json")
GRIDCSV = Path("docs/models/shot_attribute/sl_r6_grid_fold1.csv")
STEP0 = Path("docs/models/shot_attribute/sl_r6_step0.json")
LEVELS = M.SA / "mix_level_v2.parquet"
SALT = "SL-R6-2026-10-16"
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
ARMS = ("L0s", "L1x", "L1xs2")
MULTS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
CONS = ("Qr", "Qa")
NB, BSEED = 1000, 20261016
TIE = 0.02
N_MIN = 2000
TOL = 0.005
KEEP = ["game_id", "season", "game_type", "game_date_local", "t", "team", "team_id", "opp_id", "is_home", "st", "grp",
        "sc", "period", "ptype", "cls", "cell", "type6", "is_goal", "d", "rebound", "rush", "own_r", "opp_r",
        "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena", "arena_f", "clock", "l0"]
CLASS_TIER = np.repeat(TIER_OF_CELL, N_TYPE)
CLASS_TYPE = np.tile(np.arange(N_TYPE), N_CELL)
EN = ("ENF", "ENA")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def attach_q(r, fold):
    """own / opp ratings of each new construction, in the row's rating group (same mapping as models.attach_features)."""
    q = pd.read_parquet(M.SA / f"sq_ratings_v2_f{fold}.parquet")
    rg = RATING_GROUP[r.grp.to_numpy()]
    og = OPP_RATING_GROUP[rg]
    ix = np.arange(len(r))
    for con in CONS:
        cols = [f"{p}_{g}_{con}" for p in ("rf", "ra") for g in ("es", "pp", "pk")]
        own = r[["game_id", "team_id"]].merge(q[["game_id", "team_id", *cols]], on=["game_id", "team_id"], how="left",
                                              validate="many_to_one")
        opp = r[["game_id", "opp_id"]].merge(q[["game_id", "team_id", *cols]].rename(columns={"team_id": "opp_id"}),
                                             on=["game_id", "opp_id"], how="left", validate="many_to_one")
        r[f"own_{con}"] = own[[f"rf_{g}_{con}" for g in ("es", "pp", "pk")]].to_numpy()[ix, rg]
        r[f"opp_{con}"] = opp[[f"ra_{g}_{con}" for g in ("es", "pp", "pk")]].to_numpy()[ix, og]
        if r[[f"own_{con}", f"opp_{con}"]].isna().any().any():
            raise ValueError(f"missing {con} ratings")
    r["own_orig"], r["opp_orig"] = r.own_r, r.opp_r
    return r


def frames(fold):
    tr, te = F[fold]
    r = attach_q(M.attach_features(M.load_rows(tr + [te]), fold, 0.7, 1000), fold)
    return r[r.season.isin(tr)].reset_index(drop=True), r[r.season == te].reset_index(drop=True)


def offsets(fold, tr, te):
    if json.loads((RES2 / "step0.json").read_text())["selected"] != "E":
        raise ValueError("SL-R6 inherits level E")
    s_train = ML.share_table(tr)
    L = pd.read_parquet(LEVELS)
    L = L[L.construction == f"E_f{fold}"]
    return ML.row_offset(tr, L, s_train), ML.row_offset(te, L, s_train), s_train


def xgref(fold):
    return np.load(M.SA / f"xg_ref_v1_f{fold}.npy")


def resp(pred, act, r, col_own, col_opp, n_boot=NB):
    """D32 R on ES rows (deciles of the row's as-of rating), for and against."""
    m = r.grp.to_numpy() == 0
    out = {}
    for nm, col in (("for", col_own), ("against", col_opp)):
        s = slope_ratio(pred[m], act[m], r[col].to_numpy()[m], np.ones(int(m.sum())), r.game_id.to_numpy()[m],
                        n_boot=n_boot, seed=0)
        out[nm] = {k: v for k, v in s.items() if k != "table"}
        out[nm]["table"] = s["table"].round(6).reset_index().to_dict("records")
    return out


def crit(R):
    v = [R["for"]["R"], R["against"]["R"]]
    return float(max(abs(np.log(x)) if x > 0 else np.inf for x in v))


# ---------------------------------------------------------------------------------------------------- step 0
def _step0_fit(d, con, scope, xg):
    t1 = time.time()
    l0s = MS.fit_l0s(d)
    fz, dd = MX.fitter_for(d, l0s, np.zeros((len(d), N_CELL)), xg, f"own_{con}", f"opp_{con}")
    m = fz.fit()
    se = fz.s_se(m, dd.game_id.to_numpy())
    return dict(construction=con, scope=scope, n=int(fz.n), s_f=m["s_f"], s_a=m["s_a"],
                se_f_model=se["se_model"][0], se_a_model=se["se_model"][1],
                se_f_cluster=se["se_cluster"][0], se_a_cluster=se["se_cluster"][1],
                converged=m["converged"], nit=m["nit"], secs=round(time.time() - t1))


def cmd_step0():
    t0 = time.time()
    tr, _ = frames(2)
    xg = xgref(2)
    arena = tr.groupby(["game_id", "team"]).arena_f.first()
    res = dict(spec="SL-R6 step 0", note="training seasons only (2021-22..2023-24), fold-2 ratings and xG_ref; each "
               "season alone with its own L0s (unlevelled); free fit of (s_f, s_a) + the fitted home / score / rest "
               "terms; SEs conditional on W (model-based and game-cluster sandwich)", fits=[], rating_stats=[])
    for con in ("orig",) + CONS:
        oc, pc = f"own_{con}", f"opp_{con}"
        es = tr[tr.grp == 0]
        tgv = es.groupby(["game_id", "team"])[[oc, pc]].first().join(arena)
        res["rating_stats"].append(dict(construction=con, sd_own_es=float(tgv[oc].std()), sd_opp_es=float(tgv[pc].std()),
                                        corr_own_arena=float(tgv[oc].corr(tgv.arena_f)),
                                        corr_opp_arena=float(tgv[pc].corr(tgv.arena_f))))
    from joblib import Parallel, delayed
    tasks = [(con, scope, seasons) for con in ("orig",) + CONS
             for scope, seasons in [(str(s), [s]) for s in F[2][0]] + [("fold-1 train", F[1][0]), ("fold-2 train", F[2][0])]]
    need = list(dict.fromkeys(KEEP + ["own_orig", "opp_orig"] + [f"{p}_{c}" for c in CONS for p in ("own", "opp")]))
    out = Parallel(n_jobs=5, backend="loky")(delayed(_step0_fit)(tr.loc[tr.season.isin(se_), need].reset_index(drop=True),
                                                                 con, sc_, xg) for con, sc_, se_ in tasks)
    for rec in out:
        res["fits"].append(rec)
        print(now(), {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rec.items()}, flush=True)
    D = pd.DataFrame(res["fits"])
    flat = []
    for con in ("orig",) + CONS:
        S = D[(D.construction == con) & D.scope.str.isdigit()].sort_values("scope")
        for k in ("f", "a"):
            b, s = S[f"s_{k}"].to_numpy(), S[f"se_{k}_cluster"].to_numpy()
            w = 1 / s ** 2
            mu = (w * b).sum() / w.sum()
            Q = float((w * (b - mu) ** 2).sum())
            x = np.arange(len(b)) - 1.0
            slope = float((w * x * (b - mu)).sum() / (w * x * x).sum())
            sse = float(np.sqrt(1 / (w * x * x).sum()))
            from scipy.stats import chi2
            flat.append(dict(construction=con, rating="for" if k == "f" else "against",
                             per_season=np.round(b, 4).tolist(), se=np.round(s, 4).tolist(), weighted_mean=float(mu),
                             Q_het=Q, p_het=float(chi2.sf(Q, len(b) - 1)), trend_per_season=slope, trend_se=sse,
                             trend_z=slope / sse))
    res["flatness"] = flat
    res["elapsed_s"] = round(time.time() - t0)
    STEP0.write_text(json.dumps(res, indent=1))
    print(D.to_string(float_format=lambda v: f"{v:.4f}"), flush=True)
    print(pd.DataFrame(flat).to_string(float_format=lambda v: f"{v:.4f}"), flush=True)
    print(pd.DataFrame(res["rating_stats"]).to_string(float_format=lambda v: f"{v:.4f}"), flush=True)


# ---------------------------------------------------------------------------------------------------- grid (fold 1)
def _grid_fit(tr, te, otr, ote, l0s, xg, con, s_fixed):
    t1 = time.time()
    oc, pc = f"own_{con}", f"opp_{con}"
    fz, _ = MX.fitter_for(tr, l0s, otr, xg, oc, pc)
    m = fz.fit(s_fixed=s_fixed)
    m["secs"] = round(time.time() - t1)
    if s_fixed is None:
        return m, None, None
    P = MX.predict_l1x(m, l0s, te, ote, xg, oc, pc)
    grp = te.grp.to_numpy()
    return m, M.joint_ll(P, te.cls.to_numpy()), (P * xg[:, grp].T).sum(1)


def cmd_grid():
    t0 = time.time()
    (RES / "grid").mkdir(parents=True, exist_ok=True)
    tr, te = frames(1)
    otr, ote, _ = offsets(1, tr, te)
    xg = xgref(1)
    l0s = MS.fit_l0s(tr)
    grp = te.grp.to_numpy()
    xc = xg[:, grp].T
    act = xg[te.cls.to_numpy(), grp]
    games = np.sort(te.game_id.unique())
    gp = np.searchsorted(games, te.game_id.to_numpy())
    G = len(games)
    W = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)
    P0 = MS.l0s_levelled(l0s, te, ote)
    ll0 = np.bincount(gp, weights=M.joint_ll(P0, te.cls.to_numpy()), minlength=G)
    rows, llg, shat = [], {}, {}
    from joblib import Parallel, delayed
    t1 = time.time()
    frees = Parallel(n_jobs=2, backend="loky")(delayed(_grid_fit)(tr, te, otr, ote, l0s, xg, con, None) for con in CONS)
    for con, (free, _, _) in zip(CONS, frees):
        shat[con] = dict(s_f=free["s_f"], s_a=free["s_a"], converged=free["converged"], nit=free["nit"])
        print(now(), con, "free fit", shat[con], f"({time.time() - t1:.0f}s)", flush=True)
    tasks = [(con, mlt) for con in CONS for mlt in MULTS]
    outs = Parallel(n_jobs=7, backend="loky")(
        delayed(_grid_fit)(tr, te, otr, ote, l0s, xg, con, (mlt * shat[con]["s_f"], mlt * shat[con]["s_a"]))
        for con, mlt in tasks)
    for (con, mlt), (m, lp, pred) in zip(tasks, outs):
        oc, pc = f"own_{con}", f"opp_{con}"
        lg = np.bincount(gp, weights=lp, minlength=G)
        key = f"{con}_m{mlt}"
        llg[key] = lg
        R = resp(pred, act, te, oc, pc, n_boot=200)
        rec = dict(cell=key, construction=con, mult=mlt, s_f=m["s_f"], s_a=m["s_a"], ll_game=float(lg.mean()),
                   ll_game_vs_L0s=float((lg - ll0).mean()), R_for=R["for"]["R"], R_against=R["against"]["R"],
                   R_for_ci=R["for"]["ci"], R_against_ci=R["against"]["ci"], old_q5q1_for=R["for"]["old_q5q1"],
                   old_q5q1_against=R["against"]["old_q5q1"], crit=crit(R), xg_rel=float(pred.mean() / act.mean() - 1),
                   converged=m["converged"], nit=m["nit"], secs=m["secs"])
        rows.append(rec)
        print(now(), {k: (round(v, 4) if isinstance(v, float) else v) for k, v in rec.items()}, flush=True)
    D = pd.DataFrame(rows)
    best = D.ll_game.idxmax()
    bk = D.cell[best]
    D["diff_vs_best"] = D.ll_game - D.ll_game[best]
    D["se_vs_best"] = [float(np.std(W @ (llg[k] - llg[bk]) / G)) if k != bk else 0.0 for k in D.cell]
    D["within_2se"] = (D.cell == bk) | (D.diff_vs_best >= -2 * D.se_vs_best)
    C = D[D.within_2se]
    T = C[C.crit <= C.crit.min() + TIE].copy()
    T["con_order"] = T.construction.map({"Qr": 0, "Qa": 1})
    T["m_dist"] = (T.mult - 1.0).abs()
    sel = T.sort_values(["con_order", "m_dist", "crit"]).iloc[0]
    D["selected"] = D.cell == sel.cell
    D.to_csv(GRIDCSV, index=False)
    # the construction pick, reported: each construction's best cell by the same criterion
    per_con = {}
    for con in CONS:
        Cc = C[C.construction == con]
        per_con[con] = (None if Cc.empty else dict(cell=Cc.sort_values("crit").iloc[0].cell,
                                                   crit=float(Cc.crit.min())))
    fz = dict(spec="docs/models/shot_attribute/experiments.md SL-R6", level="E", w=0.7, prior_strength_attempts=1000,
              tuned_on="fold 1 only: free fit on fold-1 training (2021-22 + 2022-23), grid cells refit W at fixed s and "
                       "predict 2023-24 (fold-1 test); LL per game paired game-block bootstrap (1,000) SE vs the best cell; "
                       "R = D32 slope ratio on ES rows, deciles of the row's as-of rating (200 boots for the grid CI)",
              selection="among the 14 cells within 2 SE of the best LL, the smallest max(|log R_for|, |log R_against|); "
                        "ties within 0.02 to Qr (fewer inputs), then m closest to 1",
              s_hat_fold1=shat, best_ll_cell=bk, n_within_2se=int(len(C)), tie_set=T.cell.tolist(), per_construction=per_con,
              construction=str(sel.construction), mult=float(sel.mult), s_f=float(sel.s_f), s_a=float(sel.s_a),
              fold1=dict(R_for=float(sel.R_for), R_against=float(sel.R_against), ll_game_vs_L0s=float(sel.ll_game_vs_L0s)),
              l0s_fold1_ll_game=float(ll0.mean()), xg_floor=MX.XG_FLOOR, ridge=MX.RIDGE, features=MX.FEATS,
              grid_csv=str(GRIDCSV).replace("\\", "/"), elapsed_s=round(time.time() - t0))
    FROZEN.write_text(json.dumps(fz, indent=1))
    show = D.drop(columns=["R_for_ci", "R_against_ci", "secs", "nit"])
    print(show.to_string(float_format=lambda v: f"{v:.4f}"), flush=True)
    print(now(), "selected", sel.cell, {k: fz[k] for k in ("construction", "mult", "s_f", "s_a")}, flush=True)


# ---------------------------------------------------------------------------------------------------- fits
def frozen():
    return json.loads(FROZEN.read_text())


def cols():
    c = frozen()["construction"]
    return f"own_{c}", f"opp_{c}"


def outdir(fold):
    return RES if fold == 2 else RES / "fold1"


def fit_fold(fold):
    fzp = frozen()
    out = outdir(fold)
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te = frames(fold)
    otr, _, _ = offsets(fold, tr, te)
    xg = xgref(fold)
    oc, pc = cols()
    l0s = MS.fit_l0s(tr)
    (out / "models" / "L0s.json").write_text(json.dumps(l0s))
    fzr, _ = MX.fitter_for(tr, l0s, otr, xg, oc, pc)
    for arm, seed in (("L1x", None), ("L1xs2", 2)):
        t1 = time.time()
        m = fzr.fit(s_fixed=(fzp["s_f"], fzp["s_a"]), seed=seed)
        m.update(arm=arm, construction=fzp["construction"], start="zeros" if seed is None else f"normal(0, 0.05) seed {seed}")
        (out / "models" / f"{arm}.json").write_text(json.dumps(m))
        print(now(), f"fold {fold} {arm} fit: loss {m['loss']:.7f} nit {m['nit']} conv {m['converged']} "
              f"({time.time() - t1:.0f}s)", flush=True)


def load_fold(fold):
    out = outdir(fold)
    l0s = json.loads((out / "models" / "L0s.json").read_text())
    ms = {a: json.loads((out / "models" / f"{a}.json").read_text()) for a in ("L1x", "L1xs2")}
    return out, l0s, ms


def predict(arm, l0s, ms, r, off, xg):
    if arm == "L0s":
        return MS.l0s_levelled(l0s, r, off)
    oc, pc = cols()
    return MX.predict_l1x(ms[arm], l0s, r, off, xg, oc, pc)


def insample(fold):
    out, l0s, ms = load_fold(fold)
    tr, te = frames(fold)
    otr, _, _ = offsets(fold, tr, te)
    xg = xgref(fold)
    grp = tr.grp.to_numpy()
    xg_cls = xg[:, grp].T
    act = xg[tr.cls.to_numpy(), grp]
    P = {a: predict(a, l0s, ms, tr, otr, xg) for a in ARMS}
    st, pt = tr.st.to_numpy(), tr.ptype.to_numpy()
    cells = [(f"{MS.STATE_NAMES[s]}", st == s) for s in range(7)]
    cells += [(f"{MS.STATE_NAMES[s]} {'OT' if p_ else 'reg'}", (st == s) & (pt == p_)) for s in range(7) for p_ in (0, 1)]
    rows = []
    for nm, m in cells:
        n = int(m.sum())
        if n == 0:
            continue
        base = (P["L0s"][m] * xg_cls[m]).sum(1).mean()
        rec = dict(stratum=nm, n=n, actual=float(act[m].mean()), L0s=float(base), L0s_vs_actual=float(base / act[m].mean() - 1))
        for a in ("L1x", "L1xs2"):
            v = (P[a][m] * xg_cls[m]).sum(1).mean()
            rec[f"{a}_vs_L0s"] = float(v / base - 1)
            for k in range(3):
                rec[f"{a}_{TIER_NAMES[k]}_pp"] = float((P[a][m][:, CLASS_TIER == k].sum(1).mean()
                                                        - P["L0s"][m][:, CLASS_TIER == k].sum(1).mean()) * 100)
        rec["gated"] = n >= N_MIN
        rec["pass"] = (not rec["gated"]) or abs(rec["L1x_vs_L0s"]) <= TOL
        rows.append(rec)
    ok = all(x["pass"] for x in rows)
    en = np.isin(st, MS.EN_STATES)
    res = dict(fold=fold, rule=f"L1x xG_ref per attempt within +/-{TOL:.1%} of L0s in every stratum with n >= {N_MIN} "
               "(state x period type, and state), training rows", pass_all=bool(ok), rows=rows,
               en_identical=bool(np.array_equal(P["L1x"][en], P["L0s"][en])),
               ll_per_attempt={a: float(M.joint_ll(P[a], tr.cls.to_numpy()).mean()) for a in ARMS},
               max_abs_l1x_minus_l1xs2=float(np.abs(P["L1x"] - P["L1xs2"]).max()))
    (out / "insample.json").write_text(json.dumps(res, indent=1))
    print(pd.DataFrame(rows).to_string(), flush=True)
    print(now(), "EN identical", res["en_identical"], "max |L1x - L1xs2|", res["max_abs_l1x_minus_l1xs2"], "LL/att",
          res["ll_per_attempt"], "PASS" if ok else "FAIL", flush=True)
    return ok


def pred_fold(fold):
    out, l0s, ms = load_fold(fold)
    tr, te = frames(fold)
    _, ote, _ = offsets(fold, tr, te)
    xg = xgref(fold)
    oc, pc = cols()
    era = recording_era(te.season.to_numpy())
    print(now(), f"fold {fold} test eras {np.unique(era).tolist()}; max |offset| {float(np.abs(ote).max()):.4f}; "
          f"ratings {oc} / {pc}", flush=True)
    te2 = te.copy()
    te2["own_r"], te2["opp_r"] = te[oc], te[pc]          # the grader buckets by the arm's own construction
    te2.assign(**{f"off{c}": ote[:, c] for c in range(ote.shape[1])})[KEEP + [f"off{c}" for c in range(ote.shape[1])]] \
        .to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    for a in ARMS:
        P = predict(a, l0s, ms, te, ote, xg).astype(np.float32)
        if P.shape != (len(te), N_CLASS) or not np.allclose(P.sum(1), 1, atol=1e-4):
            raise ValueError(f"{a}: bad probability matrix")
        np.save(out / f"fold{fold}_pred_{label(a)}.npy", P)
    labels = {a: label(a) for a in ARMS}
    (out / "labels_sealed.json").write_text(json.dumps(labels))
    (out / "hashes.json").write_text(json.dumps(sorted(labels.values())))
    print(now(), f"fold {fold}: wrote {len(ARMS)} hash-labelled prediction files", flush=True)


# ---------------------------------------------------------------------------------------------------- D28 guard
def cmd_guard():
    D = RES / "fold1"
    r = pd.read_parquet(D / "fold1_rows.parquet")
    lab = json.loads((D / "labels_sealed.json").read_text())
    P = {a: np.load(D / f"fold1_pred_{lab[a]}.npy").astype(np.float64) for a in ("L0s", "L1x")}
    xg = xgref(1)
    grp = r.grp.to_numpy()
    xc = xg[:, grp].T
    px = {a: (P[a] * xc).sum(1) for a in P}
    rows = []

    def add(kind, cell, m, tol, gated, v):
        rows.append(dict(check=kind, cell=cell, n=int(m.sum()), value=float(v), tol=tol,
                         status=("reported (EN, gates at stage 8, D28)" if cell in EN else
                                 ("UNDERPOWERED" if not gated else ("PASS" if abs(v) <= tol else "FAIL")))))
    allm = np.ones(len(r), bool)
    add("xG rel", "overall", allm, 0.02, True, px["L1x"].mean() / px["L0s"].mean() - 1)
    for g in range(5):
        m = grp == g
        add("xG rel", GROUP_NAMES[g], m, 0.03, m.sum() >= 2000, px["L1x"][m].mean() / px["L0s"][m].mean() - 1)
    mon = pd.to_datetime(r.game_date_local).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = mon == mo
        add("xG rel", mo, m, 0.04, r.game_id[m].nunique() >= 100, px["L1x"][m].mean() / px["L0s"][m].mean() - 1)
    for nm, m in [("overall", allm)] + [(GROUP_NAMES[g], grp == g) for g in range(5)]:
        for k in range(3):
            d = (P["L1x"][m][:, CLASS_TIER == k].sum(1).mean() - P["L0s"][m][:, CLASS_TIER == k].sum(1).mean()) * 100
            add(f"tier {TIER_NAMES[k]} pp", nm, m, 1.5, nm == "overall" or m.sum() >= 2000, d)
    for k in range(N_TYPE):
        d = (P["L1x"][:, CLASS_TYPE == k].sum(1).mean() - P["L0s"][:, CLASS_TYPE == k].sum(1).mean()) * 100
        add(f"type {k} pp", "overall", allm, 1.5, True, d)
    T = pd.DataFrame(rows)
    ok = bool((T.status != "FAIL").all())
    print(T.to_string(float_format=lambda v: f"{v:+.5f}"), flush=True)
    _, l0s, ms = load_fold(1)
    tr, te = frames(1)
    _, oE, s_train = offsets(1, tr, te)
    L = pd.read_parquet(LEVELS)
    oO = ML.row_offset(te, L[L.construction == "O"], s_train)
    if not np.array_equal(te.game_id.to_numpy(), r.game_id.to_numpy()):
        raise ValueError("fold-1 rows misaligned")
    act = xg[te.cls.to_numpy(), grp]
    At = np.eye(3)[CLASS_TIER[te.cls.to_numpy()]]
    oc, pc = cols()
    ora = []
    for lev, off in (("E (as graded)", oE), ("O oracle (diagnostic)", oO)):
        for arm in ("L0s", "L1x"):
            Pa = predict(arm, l0s, ms, te, off, xg)
            pred = (Pa * xc).sum(1)
            rec = dict(level=lev, arm=arm, xg_all=float(pred.mean() / act.mean() - 1))
            for g in range(5):
                m = grp == g
                rec[f"xg_{GROUP_NAMES[g]}"] = float(pred[m].mean() / act[m].mean() - 1)
            for k in range(3):
                rec[f"{TIER_NAMES[k]}_pp"] = float((Pa[:, CLASS_TIER == k].sum(1).mean() - At[:, k].mean()) * 100)
            R = resp(pred, act, te, oc, pc, n_boot=200)
            rec.update(R_for=R["for"]["R"], R_against=R["against"]["R"])
            ora.append(rec)
    print(pd.DataFrame(ora).to_string(float_format=lambda v: f"{v:+.4f}"), flush=True)
    g = dict(guard_basis="L1x-minus-L0s (D28)", guard_pass=ok, rows=rows,
             max_abs_xg_rel=float(T[T.check == "xG rel"].value.abs().max()), level_read=ora)
    (D / "guard.json").write_text(json.dumps(g, indent=1, default=float))
    T.to_csv(D / "guard.csv", index=False)
    print(now(), "D28 guard (L1x minus L0s):", "PASS" if ok else "FAIL", flush=True)
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["step0", "grid", "fit2", "insample", "fold1", "guard", "pred2"])
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    if a.cmd == "step0":
        cmd_step0()
    elif a.cmd == "grid":
        if not STEP0.exists():
            raise SystemExit("step 0 must be run and committed first")
        cmd_grid()
    elif a.cmd == "fit2":
        fit_fold(2)
    elif a.cmd == "insample":
        if not insample(2):
            print(now(), "IN-SAMPLE CHECK FAILED: stop; nothing on fold 2 is read", flush=True)
            sys.exit(3)
    elif a.cmd == "fold1":
        fit_fold(1)
        insample(1)
        pred_fold(1)
    elif a.cmd == "guard":
        if not cmd_guard():
            print(now(), "D28 GUARD FAILED: stop; nothing on fold 2 is read", flush=True)
            sys.exit(4)
    else:
        if not json.loads((RES / "insample.json").read_text())["pass_all"]:
            raise SystemExit("in-sample check did not pass; fold 2 is not predicted")
        g1 = RES / "fold1" / "guard.json"
        if not g1.exists() or not json.loads(g1.read_text()).get("guard_pass"):
            raise SystemExit("fold-1 D28 guard has not passed; fold 2 is not predicted")
        pred_fold(2)
    print(now(), "done", a.cmd, flush=True)
