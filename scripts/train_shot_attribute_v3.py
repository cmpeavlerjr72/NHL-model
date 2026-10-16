"""SL-R3 trainer: arm L3b (LightGBM started from the log of L0m, the levelled stratum baseline) + seed-2 retrain, with
L0m as the comparator (docs/models/shot_attribute/experiments.md SL-R3; D24, L32). Level E (SL-R2 step 0), ratings
cell w = 0.7, b = 1,000 (SL-R2 tuning, kept), same feature list as L3m.

    train_shot_attribute_v3.py tune      fold 1 only: num_leaves {15, 31} x min_data_in_leaf {200, 800} x lr {0.05,
                                         0.02}, early stopping (50 rounds) on the time-ordered fold-1 inner split (last
                                         20% of training games by date). The inner L0 (init baseline) is fit on the
                                         inner-training rows only. -> docs/models/shot_attribute/sl_r3_frozen_params.json
    train_shot_attribute_v3.py fit2      fold-2 fits: L0 (the L0m table), L3b (seed 1), L3bs2 (seed 2). Models only;
                                         nothing is predicted on the test season.
    train_shot_attribute_v3.py insample  the L32 check on the fold-2 TRAINING rows: L3b's (and L3bs2's) mean xG_ref per
                                         attempt by strength group vs L0m's, within +/-0.5%; writes insample.json and
                                         exits non-zero on a failure (then nothing on fold 2 is read).
    train_shot_attribute_v3.py pred2     only after insample passed: hash-labelled 2024-25 predictions for L0m, L3b,
                                         L3bs2 -> results/shot_attribute_r3 (graded blind by grade_shot_attribute.py
                                         --round r3)
    train_shot_attribute_v3.py fold1     the same arms fit and predicted on fold 1 (diagnostic; E is zero there)
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
from nhl_sim.shot_attribute import models_b as MB  # noqa: E402
from nhl_sim.shot_attribute.tables import GROUP_NAMES, N_CLASS, TIER_NAMES, TIER_OF_CELL, N_TYPE  # noqa: E402

RES = Path("results/shot_attribute_r3")
RES2 = Path("results/shot_attribute_r2")
FROZEN = Path("docs/models/shot_attribute/sl_r3_frozen_params.json")
FROZEN2 = Path("docs/models/shot_attribute/sl_r2_frozen_params.json")
LEVELS = M.SA / "mix_level_v2.parquet"
SALT = "SL-R3-2026-10-16"
GRID = list(itertools.product((15, 31), (200, 800), (0.05, 0.02)))
SEED1, SEED2 = 1, 2
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
ARMS = ("L0m", "L3b", "L3bs2")
KEEP = ["game_id", "season", "game_type", "game_date_local", "t", "team", "team_id", "opp_id", "is_home", "st", "grp",
        "sc", "period", "ptype", "cls", "cell", "type6", "is_goal", "d", "rebound", "rush", "own_r", "opp_r",
        "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena", "arena_f", "clock", "l0"]
CLASS_TIER = np.repeat(TIER_OF_CELL, N_TYPE)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def wb():
    fz = json.loads(FROZEN2.read_text())
    if (fz["w"], fz["prior_strength_attempts"]) != (0.7, 1000):
        raise ValueError("SL-R3 keeps the SL-R2 ratings cell w = 0.7, b = 1,000")
    return fz["w"], fz["prior_strength_attempts"]


def frames(fold):
    w, b = wb()
    tr, te = F[fold]
    r = M.attach_features(M.load_rows(tr + [te]), fold, w, b)
    return r[r.season.isin(tr)].reset_index(drop=True), r[r.season == te].reset_index(drop=True)


def offsets(fold, tr, te):
    if json.loads((RES2 / "step0.json").read_text())["selected"] != "E":
        raise ValueError("SL-R3 inherits level E")
    s_train = ML.share_table(tr)
    L = pd.read_parquet(LEVELS)
    L = L[L.construction == f"E_f{fold}"]
    return ML.row_offset(tr, L, s_train), ML.row_offset(te, L, s_train), s_train


def lgb_params(nl, md, lr, seed, threads):
    p = M.lgb_params(nl, md, seed, threads)
    p["learning_rate"] = lr
    return p


def cmd_tune(a):
    import lightgbm as lgb
    t0 = time.time()
    RES.mkdir(parents=True, exist_ok=True)
    tr, te = frames(1)
    otr, _, _ = offsets(1, tr, te)
    print(now(), "fold-1 max |offset| (E is zero on fold 1)", float(np.abs(otr).max()), flush=True)
    gd = tr.groupby("game_id").game_date_local.first().sort_values(kind="stable")
    last = set(gd.index[int(len(gd) * 0.8):])
    mi = tr.game_id.isin(last).to_numpy()
    l0_inner = M.fit_l0(tr[~mi])
    dtr = MB.lgb_dataset_b(tr[~mi], otr[~mi], l0_inner)
    dva = MB.lgb_dataset_b(tr[mi], otr[mi], l0_inner, ref=dtr)
    base_ll = float(-M.joint_ll(np.exp(MB.l3b_init(l0_inner, tr[mi], otr[mi])), tr.cls.to_numpy()[mi]).mean())
    print(now(), f"inner split: {int((~mi).sum())} / {int(mi.sum())} rows; L0m baseline inner logloss {base_ll:.6f}", flush=True)
    res = []
    for nl, md, lr in GRID:
        t1 = time.time()
        ev = {}
        bst = lgb.train(lgb_params(nl, md, lr, SEED1, a.threads), dtr, num_boost_round=5000, valid_sets=[dva],
                        valid_names=["va"], callbacks=[lgb.early_stopping(50, verbose=False), lgb.record_evaluation(ev)])
        res.append(dict(num_leaves=nl, min_data_in_leaf=md, learning_rate=lr, best_iter=int(bst.best_iteration),
                        inner_logloss=float(min(ev["va"]["multi_logloss"])), secs=round(time.time() - t1)))
        print(now(), res[-1], flush=True)
    best = min(res, key=lambda x: x["inner_logloss"])
    fz = dict(spec="docs/models/shot_attribute/experiments.md SL-R3", level="E", w=wb()[0], prior_strength_attempts=wb()[1],
              tuned_on="fold 1 only (train 2021-22 + 2022-23, test 2023-24); inner split = last 20% of fold-1 training games by date",
              init_score="log L0m(row): L0 (Dirichlet ALPHA0 = 10) fit on the inner-training rows (tune) / the fold's training rows (fits) x exp(level-E cell offset), renormalised",
              l0m_baseline_inner_logloss=base_ll,
              lgb=dict(num_leaves=best["num_leaves"], min_data_in_leaf=best["min_data_in_leaf"],
                       learning_rate=best["learning_rate"], n_rounds=best["best_iter"], early_stopping_rounds=50, grid=res),
              alpha0_l0=M.ALPHA0, elapsed_s=round(time.time() - t0))
    FROZEN.write_text(json.dumps(fz, indent=1))
    print(now(), "selected", fz["lgb"], "wrote", FROZEN, flush=True)


def fit_fold(fold, threads):
    import lightgbm as lgb
    fz = json.loads(FROZEN.read_text())
    L = fz["lgb"]
    out = RES if fold == 2 else RES / "fold1"
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te = frames(fold)
    otr, ote, _ = offsets(fold, tr, te)
    l0 = M.fit_l0(tr)
    (out / "models" / "L0.json").write_text(json.dumps(l0))
    ref = RES2 / ("models" if fold == 2 else "fold1/models") / "L0m.json"
    if ref.exists():
        same = np.allclose(np.asarray(json.loads(ref.read_text())["p"]), np.asarray(l0["p"]), rtol=0, atol=1e-12)
        print(now(), f"L0 table equals SL-R2's L0m table ({ref}): {same}", flush=True)
        if not same:
            raise ValueError("L0 differs from SL-R2's L0m")
    ds = MB.lgb_dataset_b(tr, otr, l0)
    for arm, seed in (("L3b", SEED1), ("L3bs2", SEED2)):
        t1 = time.time()
        bst = lgb.train(lgb_params(L["num_leaves"], L["min_data_in_leaf"], L["learning_rate"], seed, threads), ds,
                        num_boost_round=L["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        print(now(), f"fold {fold} {arm} fit ({time.time() - t1:.0f}s)", flush=True)
    return tr, te, otr, ote, l0


def load_fold(fold):
    import lightgbm as lgb
    out = RES if fold == 2 else RES / "fold1"
    l0 = json.loads((out / "models" / "L0.json").read_text())
    bs = {a: lgb.Booster(model_file=str(out / "models" / f"{a}.txt")) for a in ("L3b", "L3bs2")}
    return out, l0, bs


def predict(arm, l0, bs, r, off):
    if arm == "L0m":
        return ML.apply_cell_offset(M.predict_l0(l0, r), off)
    return MB.predict_l3b(bs[arm], l0, r, off)


def insample(fold):
    """L32: per strength group, mean xG_ref per attempt of L3b (and L3bs2) vs L0m on the fold's TRAINING rows."""
    out, l0, bs = load_fold(fold)
    tr, te = frames(fold)
    otr, _, _ = offsets(fold, tr, te)
    xg = np.load(M.SA / f"xg_ref_v1_f{fold}.npy")
    grp = tr.grp.to_numpy()
    xg_cls = xg[:, grp].T
    act = xg[tr.cls.to_numpy(), grp]
    P = {a: predict(a, l0, bs, tr, otr) for a in ARMS}
    rows = []
    for g in range(5):
        m = grp == g
        base = (P["L0m"][m] * xg_cls[m]).sum(1).mean()
        rec = dict(group=GROUP_NAMES[g], n=int(m.sum()), actual=float(act[m].mean()), L0m=float(base),
                   L0m_vs_actual=float(base / act[m].mean() - 1))
        for a in ("L3b", "L3bs2"):
            v = (P[a][m] * xg_cls[m]).sum(1).mean()
            rec[a] = float(v)
            rec[f"{a}_vs_L0m"] = float(v / base - 1)
            for k in range(3):
                rec[f"{a}_{TIER_NAMES[k]}_pp_vs_L0m"] = float((P[a][m][:, CLASS_TIER == k].sum(1).mean()
                                                              - P["L0m"][m][:, CLASS_TIER == k].sum(1).mean()) * 100)
        rec["pass"] = bool(abs(rec["L3b_vs_L0m"]) <= 0.005)
        rows.append(rec)
    ok = all(r_["pass"] for r_ in rows)
    res = dict(fold=fold, rule="L3b xG_ref per attempt by strength group within +/-0.5% of L0m on the fold's training rows",
               pass_all=ok, rows=rows,
               ll_per_attempt={a: float(M.joint_ll(P[a], tr.cls.to_numpy()).mean()) for a in ARMS})
    (out / "insample.json").write_text(json.dumps(res, indent=1))
    print(pd.DataFrame(rows).to_string(), flush=True)
    print(now(), "in-sample LL/att", res["ll_per_attempt"], "PASS" if ok else "FAIL", flush=True)
    return ok


def pred_fold(fold):
    out, l0, bs = load_fold(fold)
    tr, te = frames(fold)
    _, ote, _ = offsets(fold, tr, te)
    era = recording_era(te.season.to_numpy())
    print(now(), f"fold {fold} test eras {np.unique(era).tolist()}; max |offset| {float(np.abs(ote).max()):.4f}", flush=True)
    te.assign(**{f"off{c}": ote[:, c] for c in range(ote.shape[1])})[KEEP + [f"off{c}" for c in range(ote.shape[1])]] \
        .to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    for a in ARMS:
        P = predict(a, l0, bs, te, ote).astype(np.float32)
        if P.shape != (len(te), N_CLASS) or not np.allclose(P.sum(1), 1, atol=1e-4):
            raise ValueError(f"{a}: bad probability matrix")
        np.save(out / f"fold{fold}_pred_{label(a)}.npy", P)
    labels = {a: label(a) for a in ARMS}
    (out / "labels_sealed.json").write_text(json.dumps(labels))
    (out / "hashes.json").write_text(json.dumps(sorted(labels.values())))
    print(now(), f"fold {fold}: wrote {len(ARMS)} hash-labelled prediction files", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "fit2", "insample", "pred2", "fold1"])
    ap.add_argument("--threads", type=int, default=4)
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
    elif a.cmd == "pred2":
        if not json.loads((RES / "insample.json").read_text())["pass_all"]:
            raise SystemExit("in-sample check did not pass; fold 2 is not predicted")
        pred_fold(2)
    else:
        fit_fold(1, a.threads)
        insample(1)
        pred_fold(1)
    print(now(), "done", a.cmd, flush=True)
