"""SL-R5 trainer: L3d = the L3c structure (L0s start, EN rows on L0s only and excluded from the booster) at a booster
capacity re-tuned under the L0s start (docs/models/shot_attribute/experiments.md SL-R5; D30, D27 selection form, D29).
Everything else as SL-R4: L0s baseline / strata, level E, features, ratings cell w = 0.7, b = 1,000, floor 0.

    train_shot_attribute_v5.py tune      fold 1 only. Grid lr {0.02, 0.05, 0.1} x num_leaves {15, 31, 63} x
                                         min_data_in_leaf {200, 800}; early stopping (50) on the time-ordered fold-1
                                         inner split (last 20% of fold-1 training games by date; inner L0s fit on the
                                         inner-training rows), max 2,000 rounds. Per cell: inner LL per game (paired
                                         game-block bootstrap SE vs the best cell, 1,000 resamples), rounds used, and
                                         the fold-1 ES spread ratios (for / against) of the cell refit on all fold-1
                                         training rows at its rounds and predicting 2023-24 (the grader's
                                         responsiveness definition). Selection (D27 form): among cells within 2 SE of the
                                         best inner LL, the smallest max(|log for|, |log against|); ties within 0.02 go to
                                         the fewer num_leaves x rounds. -> docs/models/shot_attribute/sl_r5_frozen_params.json
                                         + docs/models/shot_attribute/sl_r5_grid_fold1.csv
    train_shot_attribute_v5.py fit2      fold-2 fits: L0s, L3d (seed 1), L3ds2 (seed 2). Nothing on the test season.
    train_shot_attribute_v5.py insample  fold-2 TRAINING rows: L3d vs L0s xG_ref per attempt in every stratum with
                                         n >= 2,000 within +/-0.5%; exits 3 on a failure.
    train_shot_attribute_v5.py fold1     fold-1 fits + in-sample table (diagnostic) + hash-labelled 2023-24 predictions
    train_shot_attribute_v5.py guard     D28 guard on fold 1: every SL-R1 bias check read on L3d MINUS L0s (EN reported),
                                         plus the oracle-level read (reported); exits 4 on a failure.
    train_shot_attribute_v5.py pred2     only after insample AND guard passed: hash-labelled 2024-25 predictions for L0s,
                                         L3d, L3ds2 -> results/shot_attribute_r5 (graded blind: grade_shot_attribute.py
                                         --round r5 --fold 2)
"""
import argparse
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.engine.rules import recording_era  # noqa: E402
from nhl_sim.shot_attribute import mix_level as ML  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute import models_s as MS  # noqa: E402
from nhl_sim.shot_attribute.tables import GROUP_NAMES, N_CELL, N_CLASS, TIER_NAMES, TIER_OF_CELL, N_TYPE  # noqa: E402

RES = Path("results/shot_attribute_r5")
RES2 = Path("results/shot_attribute_r2")
FROZEN3 = Path("docs/models/shot_attribute/sl_r3_frozen_params.json")
FROZEN5 = Path("docs/models/shot_attribute/sl_r5_frozen_params.json")
GRIDCSV = Path("docs/models/shot_attribute/sl_r5_grid_fold1.csv")
LEVELS = M.SA / "mix_level_v2.parquet"
SALT = "SL-R5-2026-10-16"
SEED1, SEED2 = 1, 2
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
ARMS = ("L0s", "L3d", "L3ds2")
GRID = list(itertools.product((0.02, 0.05, 0.1), (15, 31, 63), (200, 800)))
MAX_ROUNDS, ES_ROUNDS = 2000, 50
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


def wb():
    fz = json.loads(FROZEN3.read_text())
    if (fz["w"], fz["prior_strength_attempts"]) != (0.7, 1000):
        raise ValueError("SL-R5 keeps the ratings cell w = 0.7, b = 1,000")
    return fz["w"], fz["prior_strength_attempts"]


def frames(fold):
    w, b = wb()
    tr, te = F[fold]
    r = M.attach_features(M.load_rows(tr + [te]), fold, w, b)
    return r[r.season.isin(tr)].reset_index(drop=True), r[r.season == te].reset_index(drop=True)


def offsets(fold, tr, te):
    if json.loads((RES2 / "step0.json").read_text())["selected"] != "E":
        raise ValueError("SL-R5 inherits level E")
    s_train = ML.share_table(tr)
    L = pd.read_parquet(LEVELS)
    L = L[L.construction == f"E_f{fold}"]
    return ML.row_offset(tr, L, s_train), ML.row_offset(te, L, s_train), s_train


def params(lr, nl, md, seed, threads):
    p = M.lgb_params(nl, md, seed, threads)
    p["learning_rate"] = lr
    return p


def frozen5():
    return json.loads(FROZEN5.read_text())["lgb"]


def spread(pred, act, r):
    """ES responsiveness exactly as grade_shot_attribute.py: team-game quintiles of own_r / opp_r on ES rows,
    Q5 - Q1 of mean xG_ref per attempt, predicted / actual."""
    m = r.grp.to_numpy() == 0
    x = r[m].assign(p=pred[m], a=act[m])
    out = {}
    for col, nm in (("own_r", "for"), ("opp_r", "against")):
        tg = x.groupby(["game_id", "team"])[col].first()
        q = pd.qcut(tg.rank(method="first"), 5, labels=False).rename("q")
        g = x.join(q, on=["game_id", "team"]).groupby("q")[["p", "a"]].mean()
        out[nm] = float((g.p.iloc[4] - g.p.iloc[0]) / (g.a.iloc[4] - g.a.iloc[0]))
    return out


def predict_iter(bst, l0s, r, off, n_iter):
    P = MS.l0s_levelled(l0s, r, off)
    m = MS.booster_rows(r)
    if m.any() and n_iter > 0:
        raw = bst.predict(r[m][M.LGB_FEATURES].astype(float), raw_score=True, num_iteration=n_iter)
        P[m] = MS._softmax(raw + np.log(P[m]))
    return P


# ---------------------------------------------------------------------------------------------------- tune (fold 1)
def cmd_tune(a):
    import lightgbm as lgb
    t0 = time.time()
    (RES / "tune").mkdir(parents=True, exist_ok=True)
    tr, te = frames(1)
    otr, ote, _ = offsets(1, tr, te)
    print(now(), "fold-1 max |offset| train / test (E is zero on fold 1)", float(np.abs(otr).max()),
          float(np.abs(ote).max()), flush=True)
    gd = tr.groupby("game_id").game_date_local.first().sort_values(kind="stable")
    last = set(gd.index[int(len(gd) * 0.8):])
    mi = tr.game_id.isin(last).to_numpy()
    l0s_in = MS.fit_l0s(tr[~mi])
    dtr = MS.lgb_dataset_c(tr[~mi], otr[~mi], l0s_in)
    dva = MS.lgb_dataset_c(tr[mi], otr[mi], l0s_in, ref=dtr)
    va = tr[mi].reset_index(drop=True)
    ova = otr[mi]
    vgames = np.sort(va.game_id.unique())
    vgp = np.searchsorted(vgames, va.game_id.to_numpy())
    G = len(vgames)
    W = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)
    base_P = MS.l0s_levelled(l0s_in, va, ova)
    base_ll_game = np.bincount(vgp, weights=M.joint_ll(base_P, va.cls.to_numpy()), minlength=G)
    # full fold-1 fits (for the spread ratios on 2023-24)
    l0s_full = MS.fit_l0s(tr)
    dfull = MS.lgb_dataset_c(tr, otr, l0s_full)
    xg = np.load(M.SA / "xg_ref_v1_f1.npy")
    grp = te.grp.to_numpy()
    xc = xg[:, grp].T
    act = xg[te.cls.to_numpy(), grp]
    P0 = MS.l0s_levelled(l0s_full, te, ote)
    s0 = spread((P0 * xc).sum(1), act, te)
    print(now(), f"inner split {int((~mi).sum())} / {int(mi.sum())} rows, {G} inner-val games; L0s inner LL/game "
          f"{base_ll_game.mean():.4f}; L0s fold-1 spread {s0}", flush=True)
    res, llg = [], {}
    for lr, nl, md in GRID:
        t1 = time.time()
        ev = {}
        bst = lgb.train(params(lr, nl, md, SEED1, a.threads), dtr, num_boost_round=MAX_ROUNDS, valid_sets=[dva],
                        valid_names=["va"], callbacks=[lgb.early_stopping(ES_ROUNDS, verbose=False),
                                                       lgb.record_evaluation(ev)])
        bi = int(bst.best_iteration)
        Pv = predict_iter(bst, l0s_in, va, ova, bi)
        lg = np.bincount(vgp, weights=M.joint_ll(Pv, va.cls.to_numpy()), minlength=G)
        t_inner = time.time() - t1
        key = f"lr{lr}_nl{nl}_md{md}"
        llg[key] = lg
        # refit on all fold-1 training rows at bi rounds; spread ratios on 2023-24
        t2 = time.time()
        if bi > 0:
            bf = lgb.train(params(lr, nl, md, SEED1, a.threads), dfull, num_boost_round=bi)
            bf.save_model(str(RES / "tune" / f"{key}.txt"))
            Pt = predict_iter(bf, l0s_full, te, ote, bi)
        else:
            Pt = P0
        pred = (Pt * xc).sum(1)
        s = spread(pred, act, te)
        lf, la = (np.log(s[k]) if s[k] > 0 else np.inf for k in ("for", "against"))
        rec = dict(cell=key, learning_rate=lr, num_leaves=nl, min_data_in_leaf=md, rounds=bi,
                   stopped_at_max=bool(bi >= MAX_ROUNDS), leaves_x_rounds=nl * bi,
                   inner_ll_game=float(lg.mean()), inner_ll_game_vs_L0s=float((lg - base_ll_game).mean()),
                   inner_logloss_lgb=float(ev["va"]["multi_logloss"][bi - 1]) if bi > 0 else np.nan,
                   spread_for=s["for"], spread_against=s["against"], crit=float(max(abs(lf), abs(la))),
                   fold1_test_ll_att=float(M.joint_ll(Pt, te.cls.to_numpy()).mean()),
                   fold1_xg_rel=float(pred.mean() / act.mean() - 1),
                   secs_inner=round(t_inner), secs_refit=round(time.time() - t2))
        res.append(rec)
        print(now(), {k: (round(v, 5) if isinstance(v, float) else v) for k, v in rec.items()}, flush=True)
    D = pd.DataFrame(res)
    best = D.inner_ll_game.idxmax()
    bk = D.cell[best]
    se = []
    for k in D.cell:
        dv = llg[k] - llg[bk]
        se.append(float(np.std(W @ dv / G)) if k != bk else 0.0)
    D["diff_vs_best"] = D.inner_ll_game - D.inner_ll_game[best]
    D["se_vs_best"] = se
    D["within_2se"] = (D.cell == bk) | (D.diff_vs_best >= -2 * D.se_vs_best)
    C = D[D.within_2se]
    cmin = C.crit.min()
    T = C[C.crit <= cmin + TIE]
    sel = T.sort_values(["leaves_x_rounds", "crit"]).iloc[0]
    D["selected"] = D.cell == sel.cell
    D.to_csv(GRIDCSV, index=False)
    np.savez(RES / "tune" / "inner_ll_game.npz", **llg, L0s=base_ll_game)
    fz = dict(spec="docs/models/shot_attribute/experiments.md SL-R5", level="E", w=wb()[0], prior_strength_attempts=wb()[1],
              tuned_on="fold 1 only (train 2021-22 + 2022-23, test 2023-24); inner split = last 20% of fold-1 training "
                       "games by date; inner L0s fit on the inner-training rows; EN rows excluded from the booster",
              selection="D27 form (D29 / D30): among cells whose inner LL per game is within 2 SE (paired game-block "
                        "bootstrap, 1,000) of the best cell, the smallest max(|log for|, |log against|) of the fold-1 ES "
                        "spread ratios (cell refit on all fold-1 training rows at its rounds, predicting 2023-24); ties "
                        "within 0.02 to the fewer num_leaves x rounds",
              l0s_inner_ll_game=float(base_ll_game.mean()), l0s_fold1_spread=s0, best_ll_cell=bk, n_within_2se=int(len(C)),
              tie_set=T.cell.tolist(),
              lgb=dict(num_leaves=int(sel.num_leaves), min_data_in_leaf=int(sel.min_data_in_leaf),
                       learning_rate=float(sel.learning_rate), n_rounds=int(sel.rounds), early_stopping_rounds=ES_ROUNDS,
                       max_rounds=MAX_ROUNDS, spread_for=float(sel.spread_for), spread_against=float(sel.spread_against)),
              grid_csv=str(GRIDCSV).replace("\\", "/"), elapsed_s=round(time.time() - t0))
    FROZEN5.write_text(json.dumps(fz, indent=1))
    print(D.drop(columns=["secs_inner", "secs_refit"]).to_string(float_format=lambda v: f"{v:.5f}"), flush=True)
    print(now(), "selected", sel.cell, fz["lgb"], flush=True)


# ---------------------------------------------------------------------------------------------------- fits
def outdir(fold):
    return RES if fold == 2 else RES / "fold1"


def fit_fold(fold, threads):
    import lightgbm as lgb
    L = frozen5()
    out = outdir(fold)
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te = frames(fold)
    otr, _, _ = offsets(fold, tr, te)
    l0s = MS.fit_l0s(tr)
    (out / "models" / "L0s.json").write_text(json.dumps(l0s))
    print(now(), f"fold {fold} L0s fit; stratum n {l0s['n']}", flush=True)
    ds = MS.lgb_dataset_c(tr, otr, l0s)
    for arm, seed in (("L3d", SEED1), ("L3ds2", SEED2)):
        t1 = time.time()
        bst = lgb.train(params(L["learning_rate"], L["num_leaves"], L["min_data_in_leaf"], seed, threads), ds,
                        num_boost_round=L["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        print(now(), f"fold {fold} {arm} fit ({time.time() - t1:.0f}s)", flush=True)


def load_fold(fold):
    import lightgbm as lgb
    out = outdir(fold)
    l0s = json.loads((out / "models" / "L0s.json").read_text())
    bs = {a: lgb.Booster(model_file=str(out / "models" / f"{a}.txt")) for a in ("L3d", "L3ds2")}
    return out, l0s, bs


def predict(arm, l0s, bs, r, off):
    if arm == "L0s":
        return MS.l0s_levelled(l0s, r, off)
    return MS.predict_l3c(bs[arm], l0s, r, off)


def insample(fold):
    out, l0s, bs = load_fold(fold)
    tr, te = frames(fold)
    otr, _, _ = offsets(fold, tr, te)
    xg = np.load(M.SA / f"xg_ref_v1_f{fold}.npy")
    grp = tr.grp.to_numpy()
    xg_cls = xg[:, grp].T
    act = xg[tr.cls.to_numpy(), grp]
    P = {a: predict(a, l0s, bs, tr, otr) for a in ARMS}
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
        for a in ("L3d", "L3ds2"):
            v = (P[a][m] * xg_cls[m]).sum(1).mean()
            rec[f"{a}_vs_L0s"] = float(v / base - 1)
            for k in range(3):
                rec[f"{a}_{TIER_NAMES[k]}_pp"] = float((P[a][m][:, CLASS_TIER == k].sum(1).mean()
                                                        - P["L0s"][m][:, CLASS_TIER == k].sum(1).mean()) * 100)
        rec["gated"] = n >= N_MIN
        rec["pass"] = (not rec["gated"]) or abs(rec["L3d_vs_L0s"]) <= TOL
        rows.append(rec)
    ok = all(x["pass"] for x in rows)
    res = dict(fold=fold, rule=f"L3d xG_ref per attempt within +/-{TOL:.1%} of L0s in every stratum with n >= {N_MIN} "
               "(state x period type, and state), training rows", pass_all=bool(ok), rows=rows,
               en_identical=bool(np.array_equal(P["L3d"][np.isin(st, MS.EN_STATES)], P["L0s"][np.isin(st, MS.EN_STATES)])),
               ll_per_attempt={a: float(M.joint_ll(P[a], tr.cls.to_numpy()).mean()) for a in ARMS},
               l3d_eq_l3ds2=bool(np.array_equal(P["L3d"], P["L3ds2"])))
    (out / "insample.json").write_text(json.dumps(res, indent=1))
    print(pd.DataFrame(rows).to_string(), flush=True)
    print(now(), "EN identical", res["en_identical"], "L3d == L3ds2", res["l3d_eq_l3ds2"], "LL/att", res["ll_per_attempt"],
          "PASS" if ok else "FAIL", flush=True)
    return ok


def pred_fold(fold):
    out, l0s, bs = load_fold(fold)
    tr, te = frames(fold)
    _, ote, _ = offsets(fold, tr, te)
    era = recording_era(te.season.to_numpy())
    print(now(), f"fold {fold} test eras {np.unique(era).tolist()}; max |offset| {float(np.abs(ote).max()):.4f}", flush=True)
    te.assign(**{f"off{c}": ote[:, c] for c in range(ote.shape[1])})[KEEP + [f"off{c}" for c in range(ote.shape[1])]] \
        .to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    for a in ARMS:
        P = predict(a, l0s, bs, te, ote).astype(np.float32)
        if P.shape != (len(te), N_CLASS) or not np.allclose(P.sum(1), 1, atol=1e-4):
            raise ValueError(f"{a}: bad probability matrix")
        np.save(out / f"fold{fold}_pred_{label(a)}.npy", P)
    labels = {a: label(a) for a in ARMS}
    (out / "labels_sealed.json").write_text(json.dumps(labels))
    (out / "hashes.json").write_text(json.dumps(sorted(labels.values())))
    print(now(), f"fold {fold}: wrote {len(ARMS)} hash-labelled prediction files", flush=True)


# ---------------------------------------------------------------------------------------------------- D28 guard
def cmd_guard():
    """Fold 1 only. Gate: every SL-R1 bias check read on L3d minus L0s (EN groups reported, D28). Reported alongside:
    the oracle-level (2023-24's own final shares) read of both arms vs actual."""
    D = RES / "fold1"
    r = pd.read_parquet(D / "fold1_rows.parquet")
    lab = json.loads((D / "labels_sealed.json").read_text())
    P = {a: np.load(D / f"fold1_pred_{lab[a]}.npy").astype(np.float64) for a in ("L0s", "L3d")}
    xg = np.load(M.SA / "xg_ref_v1_f1.npy")
    grp = r.grp.to_numpy()
    xc = xg[:, grp].T
    px = {a: (P[a] * xc).sum(1) for a in P}
    rows = []

    def add(kind, cell, m, tol, gated, v):
        rows.append(dict(check=kind, cell=cell, n=int(m.sum()), value=float(v), tol=tol,
                         status=("reported (EN, gates at stage 8, D28)" if cell in EN else
                                 ("UNDERPOWERED" if not gated else ("PASS" if abs(v) <= tol else "FAIL")))))
    allm = np.ones(len(r), bool)
    add("xG rel", "overall", allm, 0.02, True, px["L3d"].mean() / px["L0s"].mean() - 1)
    for g in range(5):
        m = grp == g
        add("xG rel", GROUP_NAMES[g], m, 0.03, m.sum() >= 2000, px["L3d"][m].mean() / px["L0s"][m].mean() - 1)
    mon = pd.to_datetime(r.game_date_local).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = mon == mo
        add("xG rel", mo, m, 0.04, r.game_id[m].nunique() >= 100, px["L3d"][m].mean() / px["L0s"][m].mean() - 1)
    for nm, m in [("overall", allm)] + [(GROUP_NAMES[g], grp == g) for g in range(5)]:
        for k in range(3):
            d = (P["L3d"][m][:, CLASS_TIER == k].sum(1).mean() - P["L0s"][m][:, CLASS_TIER == k].sum(1).mean()) * 100
            add(f"tier {TIER_NAMES[k]} pp", nm, m, 1.5, nm == "overall" or m.sum() >= 2000, d)
    for k in range(N_TYPE):
        d = (P["L3d"][:, CLASS_TYPE == k].sum(1).mean() - P["L0s"][:, CLASS_TYPE == k].sum(1).mean()) * 100
        add(f"type {k} pp", "overall", allm, 1.5, True, d)
    T = pd.DataFrame(rows)
    ok = bool((T.status != "FAIL").all())
    print(T.to_string(float_format=lambda v: f"{v:+.5f}"), flush=True)
    # oracle-level read (reported)
    _, l0s, bs = load_fold(1)
    tr, te = frames(1)
    _, oE, s_train = offsets(1, tr, te)
    L = pd.read_parquet(LEVELS)
    oO = ML.row_offset(te, L[L.construction == "O"], s_train)
    if not np.array_equal(te.game_id.to_numpy(), r.game_id.to_numpy()):
        raise ValueError("fold-1 rows misaligned")
    act = xg[te.cls.to_numpy(), grp]
    At = np.eye(3)[CLASS_TIER[te.cls.to_numpy()]]
    ora = []
    for lev, off in (("E (as graded)", oE), ("O oracle (diagnostic)", oO)):
        for arm in ("L0s", "L3d"):
            Pa = predict(arm, l0s, bs, te, off)
            pred = (Pa * xc).sum(1)
            rec = dict(level=lev, arm=arm, xg_all=float(pred.mean() / act.mean() - 1))
            for g in range(5):
                m = grp == g
                rec[f"xg_{GROUP_NAMES[g]}"] = float(pred[m].mean() / act[m].mean() - 1)
            for k in range(3):
                rec[f"{TIER_NAMES[k]}_pp"] = float((Pa[:, CLASS_TIER == k].sum(1).mean() - At[:, k].mean()) * 100)
            rec.update({f"resp_{k}": v for k, v in spread(pred, act, te).items()})
            ora.append(rec)
    print(pd.DataFrame(ora).to_string(float_format=lambda v: f"{v:+.4f}"), flush=True)
    g = dict(guard_basis="L3d-minus-L0s (D28)", guard_pass=ok, rows=rows,
             max_abs_xg_rel=float(T[T.check == "xG rel"].value.abs().max()), level_read=ora)
    (D / "guard.json").write_text(json.dumps(g, indent=1, default=float))
    T.to_csv(D / "guard.csv", index=False)
    print(now(), "D28 guard (L3d minus L0s):", "PASS" if ok else "FAIL", flush=True)
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "fit2", "insample", "fold1", "guard", "pred2"])
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    if a.cmd == "tune":
        cmd_tune(a)
    elif a.cmd == "fit2":
        fit_fold(2, a.threads)
    elif a.cmd == "insample":
        if not insample(2):
            print(now(), "IN-SAMPLE CHECK FAILED: stop; nothing on fold 2 is read", flush=True)
            sys.exit(3)
    elif a.cmd == "fold1":
        fit_fold(1, a.threads)
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
