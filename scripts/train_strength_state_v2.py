"""SS-R2 (INV-26) trainer: hazard arms H0'-H3' with the SS-R2 changes (models_r2.py). Stages:
  tune   fold 1 only (train 2021-22 + 2022-23, test 2023-24): league-level strength k x ratings grid (w x prior
         strength) on H1', then the SS-R1 H3' LightGBM grid with early stopping on a time-ordered inner split;
         writes docs/models/strength_state/ss_r2_frozen_params.json.
  fold2  frozen params; fits H0'-H3' (+ H3' under a second seed) on train through 2023-24; writes hash-labelled
         2024-25 predictions for scripts/grade_strength_state.py --round r2. T1 carries over from SS-R1 unchanged
         (not re-raced); it is copied for the closed loop.

    train_strength_state_v2.py tune|fold2
Arm keys in files are H0..H3 / H3s2 (the SS-R2 primed arms H0'..H3').
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

RES = Path("results/strength_state_r2")
R1 = Path("results/strength_state_r1")
FROZEN = Path("docs/models/strength_state/ss_r2_frozen_params.json")
SALT = "SS-R2-2026-10-15"
GRID_K = (50, 150, 450)
GRID_W, GRID_B = (0.7, 0.85, 1.0), (1800, 5400)
GRID_NL, GRID_MD = (7, 15), (200, 800)
SEED1, SEED2 = 1, 2
F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024
F2_TRAIN, F2_TEST = [20212022, 20222023, 20232024], 20242025


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(train, test, w, b, k):
    rows = R.load_rows(train + [test])
    r = R.attach_features(rows, w, b, k)
    return r[r.season.isin(train)].reset_index(drop=True), r[r.season == test].reset_index(drop=True)


def tune():
    t0 = time.time()
    out = {"tuned_on": "fold 1 only: train 2021-22 + 2022-23, test 2023-24", "grid_H1": [], "lgb_grid": []}
    best = None
    rows = R.load_rows(F1_TRAIN + [F1_TEST])
    for k, w, b in itertools.product(GRID_K, GRID_W, GRID_B):
        r = R.attach_features(rows, w, b, k)
        tr, te = r[r.season.isin(F1_TRAIN)], r[r.season == F1_TEST]
        m = R.fit_glm(tr, "H1")
        ll = float(M.per_game_ll(te, R.predict_glm(m, te)).mean())
        out["grid_H1"].append({"k": k, "w": w, "prior_strength_min": b, "fold1_H1_ll_per_game": ll})
        print(now(), f"k={k} w={w} b={b} H1' fold1 LL/game {ll:.5f}", flush=True)
        if best is None or ll > best[0]:
            best = (ll, k, w, b)
    _, k, w, b = best
    out["k"], out["w"], out["prior_strength_min"] = k, w, b
    tr, te = frames(F1_TRAIN, F1_TEST, w, b, k)
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
        print(now(), f"nl={nl} md={md} iters={it} H3' fold1 LL/game {ll:.5f} ({time.time() - t1:.0f}s)", flush=True)
        if bestl is None or ll > bestl[0]:
            bestl = (ll, nl, md, it)
    _, nl, md, it = bestl
    out["lgb"] = {"num_leaves": nl, "min_data_in_leaf": md, "learning_rate": 0.05, "n_rounds": it,
                  "inner_split": "last 20% of fold-1 training games by date"}
    out["elapsed_s"] = time.time() - t0
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    FROZEN.write_text(json.dumps(out, indent=1))
    print(now(), "frozen", json.dumps({x: out[x] for x in ("k", "w", "prior_strength_min", "lgb")}), flush=True)


def fold2():
    t0 = time.time()
    fz = json.loads(FROZEN.read_text())
    k, w, b, L = fz["k"], fz["w"], fz["prior_strength_min"], fz["lgb"]
    tr, te = frames(F2_TRAIN, F2_TEST, w, b, k)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "models").mkdir(exist_ok=True)
    keep = ["game_id", "season", "game_type", "team", "team_id", "opp_id", "is_home", "t0", "exposure_s", "y", "st",
            "sc", "pdiff", "period", "ptype", "last5", "taken_own", "drawn_opp", "b2b_own", "b2b_opp", "level"]
    te[keep].to_parquet(RES / "fold2_rows.parquet", index=False)
    preds, labels = {}, {}
    for arm in ("H0", "H1", "H2"):
        m = R.fit_glm(tr, arm)
        (RES / "models" / f"{arm}_fold2.json").write_text(json.dumps(m))
        preds[arm] = R.predict_glm(m, te)
        print(now(), arm + "'", "fit", flush=True)
    for arm, seed in (("H3", SEED1), ("H3s2", SEED2)):
        t1 = time.time()
        bst = R.fit_lgb(tr, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], seed)
        bst.save_model(str(RES / "models" / f"{arm}_fold2.txt"))
        preds[arm] = R.predict_lgb(bst, te)
        print(now(), arm + "'", f"fit ({time.time() - t1:.0f}s)", flush=True)
    for arm, mu in preds.items():
        h = label(arm)
        labels[arm] = h
        np.save(RES / f"fold2_haz_{h}.npy", mu)
    (RES / "labels_sealed.json").write_text(json.dumps(labels))
    shutil.copy(R1 / "models" / "T1_fold2.json", RES / "models" / "T1_fold2.json")
    print(now(), f"fold2 done ({time.time() - t0:.0f}s); rows test {len(te)}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "fold2"])
    a = ap.parse_args()
    {"tune": tune, "fold2": fold2}[a.stage]()
