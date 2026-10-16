"""SL-R4 trainer: L0s (state-stratified baseline, the comparator) and L3c (L3b started from L0s; EN rows on L0s only,
excluded from the booster) + a seed-2 retrain (docs/models/shot_attribute/experiments.md SL-R4; D26, L33). Level E,
ratings cell w = 0.7, b = 1,000, the SL-R3 features and frozen booster params (15 leaves, 800 min-data, lr 0.02,
31 rounds; no re-tune, as written).

    train_shot_attribute_v4.py fit2      fold-2 fits: L0s, L3c (seed 1), L3cs2 (seed 2). Nothing on the test season.
    train_shot_attribute_v4.py insample  fold-2 TRAINING rows: L3c's mean xG_ref per attempt vs L0s's in every stratum
                                         (state x period type, and state) with n >= 2,000, within +/-0.5%;
                                         writes insample.json, exits 3 on a failure.
    train_shot_attribute_v4.py fold1     fold-1 fits + the same in-sample table (diagnostic) + hash-labelled 2023-24
                                         predictions (the D13 guard is graded blind by grade_shot_attribute.py
                                         --round r4 --fold 1)
    train_shot_attribute_v4.py pred2     only after insample passed AND the fold-1 D13 guard passed: hash-labelled
                                         2024-25 predictions for L0s, L3c, L3cs2 -> results/shot_attribute_r4
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
from nhl_sim.shot_attribute import mix_level as ML  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute import models_s as MS  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CLASS, TIER_NAMES, TIER_OF_CELL, N_TYPE  # noqa: E402

RES = Path("results/shot_attribute_r4")
RES2 = Path("results/shot_attribute_r2")
FROZEN3 = Path("docs/models/shot_attribute/sl_r3_frozen_params.json")
LEVELS = M.SA / "mix_level_v2.parquet"
SALT = "SL-R4-2026-10-16"
SEED1, SEED2 = 1, 2
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
ARMS = ("L0s", "L3c", "L3cs2")
N_MIN = 2000
TOL = 0.005
KEEP = ["game_id", "season", "game_type", "game_date_local", "t", "team", "team_id", "opp_id", "is_home", "st", "grp",
        "sc", "period", "ptype", "cls", "cell", "type6", "is_goal", "d", "rebound", "rush", "own_r", "opp_r",
        "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena", "arena_f", "clock", "l0"]
CLASS_TIER = np.repeat(TIER_OF_CELL, N_TYPE)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frozen():
    fz = json.loads(FROZEN3.read_text())
    if (fz["w"], fz["prior_strength_attempts"]) != (0.7, 1000):
        raise ValueError("SL-R4 keeps the ratings cell w = 0.7, b = 1,000")
    return fz


def frames(fold):
    fz = frozen()
    tr, te = F[fold]
    r = M.attach_features(M.load_rows(tr + [te]), fold, fz["w"], fz["prior_strength_attempts"])
    return r[r.season.isin(tr)].reset_index(drop=True), r[r.season == te].reset_index(drop=True)


def offsets(fold, tr, te):
    if json.loads((RES2 / "step0.json").read_text())["selected"] != "E":
        raise ValueError("SL-R4 inherits level E")
    s_train = ML.share_table(tr)
    L = pd.read_parquet(LEVELS)
    L = L[L.construction == f"E_f{fold}"]
    return ML.row_offset(tr, L, s_train), ML.row_offset(te, L, s_train), s_train


def lgb_params(seed, threads):
    L = frozen()["lgb"]
    p = M.lgb_params(L["num_leaves"], L["min_data_in_leaf"], seed, threads)
    p["learning_rate"] = L["learning_rate"]
    return p, L["n_rounds"]


def outdir(fold):
    return RES if fold == 2 else RES / "fold1"


def fit_fold(fold, threads):
    import lightgbm as lgb
    out = outdir(fold)
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te = frames(fold)
    otr, _, _ = offsets(fold, tr, te)
    l0s = MS.fit_l0s(tr)
    (out / "models" / "L0s.json").write_text(json.dumps(l0s))
    print(now(), f"fold {fold} L0s fit; stratum n {l0s['n']}", flush=True)
    ds = MS.lgb_dataset_c(tr, otr, l0s)
    print(now(), f"booster rows {int(MS.booster_rows(tr).sum())} of {len(tr)} (EN rows excluded)", flush=True)
    for arm, seed in (("L3c", SEED1), ("L3cs2", SEED2)):
        t1 = time.time()
        p, n = lgb_params(seed, threads)
        bst = lgb.train(p, ds, num_boost_round=n)
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        print(now(), f"fold {fold} {arm} fit ({time.time() - t1:.0f}s)", flush=True)


def load_fold(fold):
    import lightgbm as lgb
    out = outdir(fold)
    l0s = json.loads((out / "models" / "L0s.json").read_text())
    bs = {a: lgb.Booster(model_file=str(out / "models" / f"{a}.txt")) for a in ("L3c", "L3cs2")}
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
        for a in ("L3c", "L3cs2"):
            v = (P[a][m] * xg_cls[m]).sum(1).mean()
            rec[f"{a}_vs_L0s"] = float(v / base - 1)
            for k in range(3):
                rec[f"{a}_{TIER_NAMES[k]}_pp"] = float((P[a][m][:, CLASS_TIER == k].sum(1).mean()
                                                        - P["L0s"][m][:, CLASS_TIER == k].sum(1).mean()) * 100)
        rec["gated"] = n >= N_MIN
        rec["pass"] = (not rec["gated"]) or abs(rec["L3c_vs_L0s"]) <= TOL
        rows.append(rec)
    ok = all(x["pass"] for x in rows)
    res = dict(fold=fold, rule=f"L3c xG_ref per attempt within +/-{TOL:.1%} of L0s in every stratum with n >= {N_MIN} "
               "(state x period type, and state), training rows", pass_all=bool(ok), rows=rows,
               en_identical=bool(np.array_equal(P["L3c"][np.isin(st, MS.EN_STATES)], P["L0s"][np.isin(st, MS.EN_STATES)])),
               ll_per_attempt={a: float(M.joint_ll(P[a], tr.cls.to_numpy()).mean()) for a in ARMS},
               l3c_eq_l3cs2=bool(np.array_equal(P["L3c"], P["L3cs2"])))
    (out / "insample.json").write_text(json.dumps(res, indent=1))
    print(pd.DataFrame(rows).to_string(), flush=True)
    print(now(), "EN identical", res["en_identical"], "L3c == L3cs2", res["l3c_eq_l3cs2"], "LL/att", res["ll_per_attempt"],
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fit2", "insample", "fold1", "pred2"])
    ap.add_argument("--threads", type=int, default=8)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    if a.cmd == "fit2":
        fit_fold(2, a.threads)
    elif a.cmd == "insample":
        if not insample(2):
            print(now(), "IN-SAMPLE CHECK FAILED: stop; nothing on fold 2 is read", flush=True)
            sys.exit(3)
    elif a.cmd == "fold1":
        fit_fold(1, a.threads)
        insample(1)
        pred_fold(1)
    else:
        if not json.loads((RES / "insample.json").read_text())["pass_all"]:
            raise SystemExit("in-sample check did not pass; fold 2 is not predicted")
        g1 = RES / "grade_fold1.json"
        if not g1.exists() or not json.loads(g1.read_text()).get("d13_guard_pass"):
            raise SystemExit("fold-1 D13 guard has not passed; fold 2 is not predicted")
        pred_fold(2)
    print(now(), "done", a.cmd, flush=True)
