"""SA-R3 (INV-32) trainer: thin-state (4v4 / 3v3) attempt hazard arms (docs/models/shot_attempt/experiments.md SA-R3).
Versioned sibling of train_shot_attempt_v2.py (SA-R2 untouched). Everything not listed is A3g as frozen in SA-R2
(docs/models/shot_attempt/sa_r2_frozen_params.json: LC-1 levels, k = 5, w = 0.85, b = 200, 15 leaves, 800 min-data,
459 rounds).

Arms (complexity order A2g-c < A3g < A3g-c < A3g-s):
  A3g     reference refit (reproduction of SA-R2's A3g), seed 1; A3gs2 = the same under seed 2 (noise floor)
  A3g-s   A3g on five LC-1 group levels (ES-5v5, PP-for, PK, 4v4, 3v3; EN keeps the SA-R2 ES level), level "lc1s"
  A3g-c   A3g x exp(cell[st]); cell = log((Y + b_c) / (M + b_c)) for 4v4 and 3v3, Y / M = training actual / training
          (in-sample) A3g prediction, b_c in {50, 200, 800} tuned on fold 1 by LL
  A2g-c   A2g with the same cells (b_c tuned on fold 1 on its own base, labelled)

    train_shot_attempt_v3.py tune    fold 1 only: b_c for A3g-c and A2g-c -> docs/models/shot_attempt/sa_r3_frozen_params.json
    train_shot_attempt_v3.py fold2   frozen; hash-labelled 2024-25 predictions -> results/shot_attempt_r3 (graded blind
                                     by grade_shot_attempt.py --round SA-R3)
    train_shot_attempt_v3.py fold1   diagnostic (fold-1 bias, D13 guard) -> results/shot_attempt_r3/fold1
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.league_level_lc1 import per_season_parity  # noqa: E402
from nhl_sim.shot_attempt import models as S  # noqa: E402

RES = Path("results/shot_attempt_r3")
FROZEN2 = Path("docs/models/shot_attempt/sa_r2_frozen_params.json")
FROZEN = Path("docs/models/shot_attempt/sa_r3_frozen_params.json")
SALT = "SA-R3-2026-10-16"
TV = "v2"
GRID_BC = (50, 200, 800)
SEED1, SEED2 = 1, 2
F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024
F2_TRAIN, F2_TEST = [20212022, 20222023, 20232024], 20242025
KEEP = ["game_id", "season", "game_type", "team", "team_id", "opp_id", "is_home", "t0", "exposure_s", "y", "y_goal",
        "st", "sc", "period", "ptype", "last5", "own_r", "opp_r", "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp",
        "arena_f", "level"]
ARMS = ("A2g-c", "A3g", "A3g-c", "A3g-s", "A3gs2")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(train, test, fold, fz, level):
    rows = S.load_rows(train + [test])
    r = S.attach_features(rows, fz["w"], fz["prior_strength_min"], fz["k"], fold, arena=True, tv=TV, level=level)
    return r[r.season.isin(train)].reset_index(drop=True), r[r.season == test].reset_index(drop=True)


def thin_ratio(r, mu):
    st, y = r.st.to_numpy(), r.y.to_numpy(float)
    return {s_: dict(actual=float(y[st == s_].sum()), pred=float(mu[st == s_].sum()),
                     ratio=float(mu[st == s_].sum() / y[st == s_].sum())) for s_ in S.THIN_STATES}


def tune():
    t0 = time.time()
    fz = json.loads(FROZEN2.read_text())
    L = fz["lgb"]
    tr, te = frames(F1_TRAIN, F1_TEST, 1, fz, "lc1g")
    out = {"inherits": str(FROZEN2), "k": fz["k"], "w": fz["w"], "prior_strength_min": fz["prior_strength_min"],
           "lgb": L, "tuned_on": "fold 1 only: train 2021-22 + 2022-23, test 2023-24", "b_c_grid": list(GRID_BC)}
    bases = {"A3g": S.fit_lgb(tr, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], SEED1),
             "A2g": S.fit_glm(tr, "A2g")}
    for base, m in bases.items():
        arm = f"{base}-c"
        mu_tr = S.predict_arm(base, m, tr)
        mu_te = S.predict_arm(base, m, te)
        ins = thin_ratio(tr, mu_tr)
        rec = {"in_sample_train_pred_over_actual": {str(k): v for k, v in ins.items()},
               "fold1_test_pred_over_actual_base": {str(k): v for k, v in thin_ratio(te, mu_te).items()},
               "ll_base": float(S.per_game_ll(te, mu_te).mean()), "grid": []}
        best = None
        for bc in GRID_BC:
            c = S.thin_cells(tr, mu_tr, bc)
            mu = S.predict_arm(arm, {"base": m, "cell": c}, te)
            ll = float(S.per_game_ll(te, mu).mean())
            rec["grid"].append({"b_c": bc, "cell": c, "fold1_ll_per_game": ll,
                                "fold1_test_pred_over_actual": {str(k): v["ratio"] for k, v in thin_ratio(te, mu).items()}})
            print(now(), f"{arm} b_c={bc} cells 4v4 {c[3]:+.5f} 3v3 {c[4]:+.5f} fold1 LL/game {ll:.6f}", flush=True)
            if best is None or ll > best[0]:
                best = (ll, bc)
        rec["b_c"] = best[1]
        out[arm] = rec
        print(now(), arm, "frozen b_c", best[1], "in-sample ratio", {k: round(v["ratio"], 5) for k, v in ins.items()},
              flush=True)
    out["elapsed_s"] = time.time() - t0
    FROZEN.write_text(json.dumps(out, indent=1))


def fit_all(fold, train, test, outdir, blind):
    fz = json.loads(FROZEN.read_text())
    L = fz["lgb"]
    tr, te = frames(train, test, fold, fz, "lc1g")
    trs, tes = frames(train, test, fold, fz, "lc1s")
    assert (tr.y.to_numpy() == trs.y.to_numpy()).all() and (te.exposure_s.to_numpy() == tes.exposure_s.to_numpy()).all()
    (outdir / "models").mkdir(parents=True, exist_ok=True)
    preds, models, fits = {}, {}, {}
    for arm, seed in (("A3g", SEED1), ("A3gs2", SEED2)):
        t1 = time.time()
        b = S.fit_lgb(tr, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], seed)
        b.save_model(str(outdir / "models" / f"{arm}.txt"))
        models[arm], fits[arm] = b, tr
        preds[arm] = S.predict_arm("A3g", b, te)
        print(now(), arm, f"fit ({time.time() - t1:.0f}s)", flush=True)
    m2 = S.fit_glm(tr, "A2g")
    (outdir / "models" / "A2g.json").write_text(json.dumps(m2))
    models["A2g"] = m2
    for base in ("A3g", "A2g"):
        arm = f"{base}-c"
        c = S.thin_cells(tr, S.predict_arm(base, models[base], tr), fz[arm]["b_c"])
        (outdir / "models" / f"{arm}.json").write_text(json.dumps(
            {"base_model": f"{base}.txt" if base == "A3g" else f"{base}.json", "b_c": fz[arm]["b_c"], "cell": c}))
        models[arm], fits[arm] = {"base": models[base], "cell": c}, tr
        preds[arm] = S.predict_arm(arm, models[arm], te)
        print(now(), arm, "cells", np.round(c, 5).tolist(), flush=True)
    t1 = time.time()
    b = S.fit_lgb(trs, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], SEED1)
    b.save_model(str(outdir / "models" / "A3g-s.txt"))
    models["A3g-s"], fits["A3g-s"] = b, trs
    preds["A3g-s"] = S.predict_arm("A3g-s", b, tes)
    print(now(), "A3g-s", f"fit ({time.time() - t1:.0f}s)", flush=True)
    # LC-1 per-training-season parity (in-sample), every arm (reported)
    par = {}
    for arm in ARMS:
        mu = S.predict_arm(arm if arm != "A3gs2" else "A3g", models[arm], fits[arm])
        t = per_season_parity(fits[arm].season.to_numpy(), fits[arm].y.to_numpy(float), mu)
        par[arm] = {int(s_): float(v) for s_, v in t.pred_over_actual_minus_1.items()}
        print(now(), "parity", arm, {k: round(v, 5) for k, v in par[arm].items()}, flush=True)
    (outdir / f"parity_fold{fold}_train.json").write_text(json.dumps(par, indent=1))
    return te, tes, preds


def fold2():
    t0 = time.time()
    RES.mkdir(parents=True, exist_ok=True)
    te, tes, preds = fit_all(2, F2_TRAIN, F2_TEST, RES, True)
    te[KEEP].to_parquet(RES / "fold2_rows.parquet", index=False)
    tes[["level"]].to_parquet(RES / "fold2_level_lc1s.parquet", index=False)
    # reproduction of SA-R2's A3g
    r2 = Path("results/shot_attempt_r2")
    lab2 = json.loads((r2 / "labels_sealed.json").read_text())
    old = np.load(r2 / f"fold2_haz_{lab2['A3g']}.npy")
    rep = dict(max_abs_diff=float(np.abs(old - preds["A3g"]).max()), bit_identical=bool((old == preds["A3g"]).all()))
    (RES / "reproduction_A3g.json").write_text(json.dumps(rep))
    print(now(), "A3g reproduction vs SA-R2", rep, flush=True)
    labels = {}
    for arm, mu in preds.items():
        h = label(arm)
        labels[arm] = h
        np.save(RES / f"fold2_haz_{h}.npy", mu)
        (RES / f"fold2_meta_{h}.json").write_text(json.dumps({"latent_v": 0.0}))
    (RES / "labels_sealed.json").write_text(json.dumps(labels))
    print(now(), f"fold2 done ({time.time() - t0:.0f}s); rows test {len(te)}", flush=True)


def fold1():
    t0 = time.time()
    d = RES / "fold1"
    d.mkdir(parents=True, exist_ok=True)
    te, _, preds = fit_all(1, F1_TRAIN, F1_TEST, d, False)
    te[KEEP].to_parquet(d / "rows.parquet", index=False)
    for arm, mu in preds.items():
        np.save(d / f"pred_{arm}.npy", mu)
    print(now(), f"fold1 done ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "fold2", "fold1"])
    a = ap.parse_args()
    {"tune": tune, "fold2": fold2, "fold1": fold1}[a.stage]()
