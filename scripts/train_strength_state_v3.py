"""SS-R3 (INV-27) trainer: hazard arms H0''-H3'' = SS-R2's arms with the season-phase profile offset and the
de-seasonalised league level (models_r2.attach_features(profile_fold=...)). Stages:
  tune   fold 1 only: k in {15, 50, 150} on H1'' (w = 1.0 and prior strength 1,800 stay frozen at the SS-R2 values),
         then the SS-R1 H3 LightGBM grid re-tuned on fold 1 (early stopping on the time-ordered inner split);
         writes docs/models/strength_state/ss_r3_frozen_params.json.
  fold2  frozen params; fits H0''-H3'' (+ H3'' seed 2) on train through 2023-24, writes hash-labelled 2024-25
         predictions to results/strength_state_r3 (graded blind by scripts/grade_strength_state.py --round SS-R3).
  fold1  diagnostic: fits the SS-R3 arms and the SS-R2 twins (SS-R2 frozen params, no profile) on fold 1 train,
         saves fold-1 test predictions + models to results/strength_state_r3/fold1 for the bias checks.
"""
import argparse
import hashlib
import itertools
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.strength_state import models as M  # noqa: E402
from nhl_sim.strength_state import models_r2 as R  # noqa: E402

RES = Path("results/strength_state_r3")
R1 = Path("results/strength_state_r1")
FROZEN = Path("docs/models/strength_state/ss_r3_frozen_params.json")
FROZEN_R2 = Path("docs/models/strength_state/ss_r2_frozen_params.json")
SALT = "SS-R3-2026-10-15"
GRID_K = (15, 50, 150)
W, B = 1.0, 1800
GRID_NL, GRID_MD = (7, 15), (200, 800)
SEED1, SEED2 = 1, 2
F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024
F2_TRAIN, F2_TEST = [20212022, 20222023, 20232024], 20242025
KEEP = ["game_id", "season", "game_type", "team", "team_id", "opp_id", "is_home", "t0", "exposure_s", "y", "st",
        "sc", "pdiff", "period", "ptype", "last5", "taken_own", "drawn_opp", "b2b_own", "b2b_opp", "level"]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(train, test, k, fold, w=W, b=B, profile=True):
    rows = R.load_rows(train + [test])
    r = R.attach_features(rows, w, b, k, profile_fold=fold if profile else None)
    return r[r.season.isin(train)].reset_index(drop=True), r[r.season == test].reset_index(drop=True)


def tune():
    t0 = time.time()
    out = {"tuned_on": "fold 1 only: train 2021-22 + 2022-23, test 2023-24 (fold-1 profile)", "grid_H1": [],
           "lgb_grid": [], "w": W, "prior_strength_min": B}
    rows = R.load_rows(F1_TRAIN + [F1_TEST])
    best = None
    for k in GRID_K:
        r = R.attach_features(rows, W, B, k, profile_fold=1)
        tr, te = r[r.season.isin(F1_TRAIN)], r[r.season == F1_TEST]
        m = R.fit_glm(tr, "H1")
        ll = float(M.per_game_ll(te, R.predict_glm(m, te)).mean())
        out["grid_H1"].append({"k": k, "fold1_H1_ll_per_game": ll})
        print(now(), f"k={k} H1'' fold1 LL/game {ll:.5f}", flush=True)
        if best is None or ll > best[0]:
            best = (ll, k)
    k = best[1]
    out["k"] = k
    tr, te = frames(F1_TRAIN, F1_TEST, k, 1)
    import lightgbm as lgb
    gd = load_games(F1_TRAIN, columns=["game_id", "game_date_local"]).sort_values(["game_date_local", "game_id"])
    cut = gd.game_id.iloc[int(len(gd) * 0.8):]
    inner_va = tr.game_id.isin(cut)
    bestl = None
    for nl, md in itertools.product(GRID_NL, GRID_MD):
        t1 = time.time()
        bst = lgb.train(M.lgb_params(nl, md, SEED1), R.lgb_dataset(tr[~inner_va]), num_boost_round=3000,
                        valid_sets=[R.lgb_dataset(tr[inner_va])], callbacks=[lgb.early_stopping(50, verbose=False)])
        it = int(bst.best_iteration)
        full = R.fit_lgb(tr, nl, md, it, SEED1)
        ll = float(M.per_game_ll(te, R.predict_lgb(full, te)).mean())
        out["lgb_grid"].append({"num_leaves": nl, "min_data_in_leaf": md, "best_iter_inner": it,
                                "fold1_H3_ll_per_game": ll})
        print(now(), f"nl={nl} md={md} iters={it} H3'' fold1 LL/game {ll:.5f} ({time.time() - t1:.0f}s)", flush=True)
        if bestl is None or ll > bestl[0]:
            bestl = (ll, nl, md, it)
    _, nl, md, it = bestl
    out["lgb"] = {"num_leaves": nl, "min_data_in_leaf": md, "learning_rate": 0.05, "n_rounds": it,
                  "inner_split": "last 20% of fold-1 training games by date"}
    out["elapsed_s"] = time.time() - t0
    FROZEN.write_text(json.dumps(out, indent=1))
    print(now(), "frozen", json.dumps({x: out[x] for x in ("k", "w", "prior_strength_min", "lgb")}), flush=True)


def fit_all(tr, te, L, outdir, prefix, blind):
    (outdir / "models").mkdir(parents=True, exist_ok=True)
    preds = {}
    for arm in ("H0", "H1", "H2"):
        m = R.fit_glm(tr, arm)
        (outdir / "models" / f"{prefix}{arm}_fold.json").write_text(json.dumps(m))
        preds[arm] = R.predict_glm(m, te)
        print(now(), prefix + arm, "fit", flush=True)
    for arm, seed in (("H3", SEED1), ("H3s2", SEED2)):
        if not blind and arm == "H3s2":
            continue
        t1 = time.time()
        bst = R.fit_lgb(tr, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], seed)
        bst.save_model(str(outdir / "models" / f"{prefix}{arm}_fold.txt"))
        preds[arm] = R.predict_lgb(bst, te)
        print(now(), prefix + arm, f"fit ({time.time() - t1:.0f}s)", flush=True)
    return preds


def fold2():
    t0 = time.time()
    fz = json.loads(FROZEN.read_text())
    k, L = fz["k"], fz["lgb"]
    tr, te = frames(F2_TRAIN, F2_TEST, k, 2)
    RES.mkdir(parents=True, exist_ok=True)
    te[KEEP].to_parquet(RES / "fold2_rows.parquet", index=False)
    preds = fit_all(tr, te, L, RES, "", True)
    labels = {}
    for arm, mu in preds.items():
        h = label(arm)
        labels[arm] = h
        np.save(RES / f"fold2_haz_{h}.npy", mu)
    (RES / "labels_sealed.json").write_text(json.dumps(labels))
    for f in ("H0", "H1", "H2", "H3", "H3s2"):  # bias script loads models as <arm>_fold2.*
        for ext in ("json", "txt"):
            src = RES / "models" / f"{f}_fold.{ext}"
            if src.exists():
                src.rename(RES / "models" / f"{f}_fold2.{ext}")
    shutil.copy(R1 / "models" / "T1_fold2.json", RES / "models" / "T1_fold2.json")
    print(now(), f"fold2 done ({time.time() - t0:.0f}s); rows test {len(te)}", flush=True)


def fold1():
    t0 = time.time()
    fz = json.loads(FROZEN.read_text())
    f2 = json.loads(FROZEN_R2.read_text())
    d = RES / "fold1"
    d.mkdir(parents=True, exist_ok=True)
    tr, te = frames(F1_TRAIN, F1_TEST, fz["k"], 1)
    te[KEEP].to_parquet(d / "rows_r3.parquet", index=False)
    for arm, mu in fit_all(tr, te, fz["lgb"], d / "r3", "", False).items():
        np.save(d / f"pred_r3_{arm}.npy", mu)
    tr2, te2 = frames(F1_TRAIN, F1_TEST, f2["k"], 1, w=f2["w"], b=f2["prior_strength_min"], profile=False)
    te2[KEEP].to_parquet(d / "rows_r2.parquet", index=False)
    for arm, mu in fit_all(tr2, te2, f2["lgb"], d / "r2", "", False).items():
        np.save(d / f"pred_r2_{arm}.npy", mu)
    print(now(), f"fold1 done ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "fold2", "fold1"])
    a = ap.parse_args()
    {"tune": tune, "fold2": fold2, "fold1": fold1}[a.stage]()
