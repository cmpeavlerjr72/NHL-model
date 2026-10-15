"""SS-R1 (INV-22) trainer. Stages:
  tune   fold 1 only (train 2021-22 + 2022-23, test 2023-24): ratings grid (w x prior strength) on H1, then the
         H3 LightGBM grid with early stopping on a time-ordered inner split; writes the frozen params.
  fold2  frozen params; fits H0-H3 (+ H3 under a second seed) and T0-T1 on train through 2023-24; writes
         hash-labelled 2024-25 predictions for scripts/grade_strength_state.py.

    train_strength_state_v1.py tune|fold2
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
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.strength_state import models as M  # noqa: E402

RES = Path("results/strength_state_r1")
FROZEN = Path("docs/models/strength_state/ss_r1_frozen_params.json")
SALT = "SS-R1-2026-10-15"
GRID_W, GRID_B = (0.3, 0.5, 0.7), (200, 600, 1800)
GRID_NL, GRID_MD = (7, 15), (200, 800)
SEED1, SEED2 = 1, 2
F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024
F2_TRAIN, F2_TEST = [20212022, 20222023, 20232024], 20242025


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(train, test, w, b):
    rows = M.load_rows(train + [test])
    r = M.attach_features(rows, w, b, last_train_season=max(train))
    return r[r.season.isin(train)].reset_index(drop=True), r[r.season == test].reset_index(drop=True)


def tune():
    t0 = time.time()
    out = {"tuned_on": "fold 1 only: train 2021-22 + 2022-23, test 2023-24", "ratings_grid_H1": [], "lgb_grid": []}
    best = None
    for w, b in itertools.product(GRID_W, GRID_B):
        tr, te = frames(F1_TRAIN, F1_TEST, w, b)
        m = M.fit_glm(tr, "H1")
        ll = float(M.per_game_ll(te, M.predict_glm(m, te)).mean())
        out["ratings_grid_H1"].append({"w": w, "prior_strength_min": b, "fold1_H1_ll_per_game": ll})
        print(now(), f"w={w} b={b} H1 fold1 LL/game {ll:.5f}", flush=True)
        if best is None or ll > best[0]:
            best = (ll, w, b)
    _, w, b = best
    out["w"], out["prior_strength_min"] = w, b
    tr, te = frames(F1_TRAIN, F1_TEST, w, b)
    import lightgbm as lgb
    gd = load_games(F1_TRAIN, columns=["game_id", "game_date_local"]).sort_values(["game_date_local", "game_id"])
    cut = gd.game_id.iloc[int(len(gd) * 0.8):]
    inner_va = tr.game_id.isin(cut)
    bestl = None
    for nl, md in itertools.product(GRID_NL, GRID_MD):
        t1 = time.time()
        dtr = M.lgb_dataset(tr[~inner_va])
        dva = M.lgb_dataset(tr[inner_va])
        bst = lgb.train(M.lgb_params(nl, md, SEED1), dtr, num_boost_round=3000, valid_sets=[dva],
                        callbacks=[lgb.early_stopping(50, verbose=False)])
        it = int(bst.best_iteration)
        full = M.fit_lgb(tr, nl, md, it, SEED1)
        ll = float(M.per_game_ll(te, M.predict_lgb(full, te)).mean())
        out["lgb_grid"].append({"num_leaves": nl, "min_data_in_leaf": md, "best_iter_inner": it,
                                "fold1_H3_ll_per_game": ll})
        print(now(), f"nl={nl} md={md} iters={it} H3 fold1 LL/game {ll:.5f} ({time.time() - t1:.0f}s)", flush=True)
        if bestl is None or ll > bestl[0]:
            bestl = (ll, nl, md, it)
    _, nl, md, it = bestl
    out["lgb"] = {"num_leaves": nl, "min_data_in_leaf": md, "learning_rate": 0.05, "n_rounds": it,
                  "inner_split": "last 20% of fold-1 training games by date"}
    out["elapsed_s"] = time.time() - t0
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    FROZEN.write_text(json.dumps(out, indent=1))
    print(now(), "frozen", json.dumps({k: out[k] for k in ("w", "prior_strength_min", "lgb")}), flush=True)


def fold2():
    t0 = time.time()
    fz = json.loads(FROZEN.read_text())
    w, b, L = fz["w"], fz["prior_strength_min"], fz["lgb"]
    tr, te = frames(F2_TRAIN, F2_TEST, w, b)
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "models").mkdir(exist_ok=True)
    keep = ["game_id", "season", "game_type", "team", "team_id", "opp_id", "is_home", "t0", "exposure_s", "y", "st",
            "sc", "pdiff", "period", "ptype", "last5", "taken_own", "drawn_opp", "b2b_own", "b2b_opp"]
    te[keep].to_parquet(RES / "fold2_rows.parquet", index=False)
    preds, labels = {}, {}
    for arm in ("H0", "H1", "H2"):
        m = M.fit_glm(tr, arm)
        (RES / "models" / f"{arm}_fold2.json").write_text(json.dumps(m))
        preds[arm] = M.predict_glm(m, te)
        print(now(), arm, "fit", flush=True)
    for arm, seed in (("H3", SEED1), ("H3s2", SEED2)):
        t1 = time.time()
        bst = M.fit_lgb(tr, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], seed)
        bst.save_model(str(RES / "models" / f"{arm}_fold2.txt"))
        preds[arm] = M.predict_lgb(bst, te)
        print(now(), arm, f"fit ({time.time() - t1:.0f}s)", flush=True)
    for arm, mu in preds.items():
        h = label(arm)
        labels[arm] = h
        np.save(RES / f"fold2_haz_{h}.npy", mu)
    # type arms
    ttr = M.type_frame(F2_TRAIN, max(F2_TRAIN))
    tte = M.type_frame([F2_TEST], max(F2_TRAIN))
    tte.to_parquet(RES / "fold2_types.parquet", index=False)
    m0, m1 = M.fit_t0(ttr), M.fit_t1(ttr)
    (RES / "models" / "T0_fold2.json").write_text(json.dumps(m0))
    (RES / "models" / "T1_fold2.json").write_text(json.dumps(m1))
    for arm, p in (("T0", M.predict_t0(m0, tte)), ("T1", M.predict_t1(m1, tte))):
        h = label(arm)
        labels[arm] = h
        np.save(RES / f"fold2_type_{h}.npy", p)
    (RES / "labels_sealed.json").write_text(json.dumps(labels))
    print(now(), f"fold2 done ({time.time() - t0:.0f}s); rows test {len(te)}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "fold2"])
    a = ap.parse_args()
    {"tune": tune, "fold2": fold2}[a.stage]()
