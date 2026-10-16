"""SL-R1 step 3 trainer: shot location x type arms L0-L3 (docs/models/shot_attribute/experiments.md SL-R1), on
unblocked attempts (step-0 rule (b)).

    train_shot_attribute_v1.py tune    fold 1 only: ratings grid point (w, b) by L1's fold-1 test LL, with the
                                       fold-1 offline quintile-spread ratio for every grid cell (L24); LightGBM
                                       num_leaves x min_data by early stopping on a time-ordered inner split (last 20%
                                       of fold-1 training games by date) -> docs/models/shot_attribute/sl_r1_frozen_params.json
    train_shot_attribute_v1.py fold2   frozen params; L0, L1, L2, L3 (seed 1), L3s2 (seed 2) on 2021-22..2023-24;
                                       hash-labelled 2024-25 predictions -> results/shot_attribute_r1 (graded blind by
                                       grade_shot_attribute.py)
    train_shot_attribute_v1.py fold1   the same on fold 1 (train 2021-22..2022-23, test 2023-24): diagnostic
"""
import argparse
import hashlib
import itertools
import json
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CLASS  # noqa: E402

RES = Path("results/shot_attribute_r1")
FROZEN = Path("docs/models/shot_attribute/sl_r1_frozen_params.json")
SALT = "SL-R1-2026-10-16"
GRID_W = (0.5, 0.7, 0.85, 1.0)
GRID_B = (300, 1000, 3000)
LGB_GRID = [(15, 200), (15, 800), (31, 200), (31, 800)]
SEED1, SEED2 = 1, 2
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
ARMS = ("L0", "L1", "L2", "L3", "L3s2")
KEEP = ["game_id", "season", "game_type", "game_date_local", "t", "team", "team_id", "opp_id", "is_home", "st", "grp",
        "sc", "period", "ptype", "cls", "cell", "type6", "is_goal", "d", "rebound", "rush", "own_r", "opp_r",
        "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena", "arena_f", "clock", "l0"]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(fold, w, b):
    tr, te = F[fold]
    r = M.attach_features(M.load_rows(tr + [te]), fold, w, b)
    return r[r.season.isin(tr)].reset_index(drop=True), r[r.season == te].reset_index(drop=True)


def spread_ratio(r, P, xg, col):
    """Offline quintile spread (ES rows): predicted vs actual mean xG_ref per attempt, Q5 - Q1, team-game quintiles."""
    es = (r.grp == 0).to_numpy()
    x = r[es]
    tg = x.groupby(["game_id", "team"])[col].first()
    q = pd.qcut(tg.rank(method="first"), 5, labels=False)
    qq = x.join(q.rename("q"), on=["game_id", "team"]).q.to_numpy()
    pred = P[es] @ xg[:, 0]
    act = xg[x.cls.to_numpy(), 0]
    pm = np.array([pred[qq == k].mean() for k in range(5)])
    am = np.array([act[qq == k].mean() for k in range(5)])
    return float((pm[4] - pm[0]) / (am[4] - am[0])), pm.tolist(), am.tolist()


def _grid_cell(args):
    w, b = args
    tr, te = frames(1, w, b)
    m = M.fit_mnl(tr, "L1")
    P = M.predict_mnl(m, te)
    ll = float(M.joint_ll(P, te.cls.to_numpy()).mean())
    xg = np.load(M.SA / "xg_ref_v1_f1.npy")
    sf = spread_ratio(te, P, xg, "own_rf_es")
    sa = spread_ratio(te, P, xg, "opp_ra_es")
    return dict(w=w, b=b, ll_per_attempt=ll, n_test=len(te), spread_for=sf[0], spread_against=sa[0],
                q_for_pred=sf[1], q_for_act=sf[2], q_ag_pred=sa[1], q_ag_act=sa[2])


def cmd_tune(a):
    t0 = time.time()
    gfile = RES / "ratings_grid_fold1.json"
    if a.reuse_grid and gfile.exists():
        grid = json.loads(gfile.read_text())
    else:
        with ProcessPoolExecutor(a.procs) as ex:
            grid = list(ex.map(_grid_cell, list(itertools.product(GRID_W, GRID_B))))
        RES.mkdir(parents=True, exist_ok=True)
        gfile.write_text(json.dumps(grid, indent=1))
    for g in grid:
        print(now(), f"w={g['w']} b={g['b']} LL/att {g['ll_per_attempt']:.6f} spread for {g['spread_for']:.3f} "
              f"against {g['spread_against']:.3f}", flush=True)
    # selection (labelled interpretation of the L24 guard): max fold-1 L1 LL among grid cells whose fold-1 offline
    # spread ratios (for and against) both lie in [0.8, 1.2]; if no cell does, max LL over all cells
    inband = [g for g in grid if 0.8 <= g["spread_for"] <= 1.2 and 0.8 <= g["spread_against"] <= 1.2]
    best = max(inband or grid, key=lambda g: g["ll_per_attempt"])
    best_any = max(grid, key=lambda g: g["ll_per_attempt"])
    print(now(), "ratings grid done", f"{time.time() - t0:.0f}s; best in band w={best['w']} b={best['b']}; "
          f"best LL overall w={best_any['w']} b={best_any['b']}", flush=True)
    # LightGBM on fold 1, time-ordered inner split
    import lightgbm as lgb
    tr, _ = frames(1, best["w"], best["b"])
    # inner split: last 20% of fold-1 training games by date (both training seasons pooled, ordered by date)
    gd = tr.groupby("game_id").game_date_local.first().sort_values(kind="stable")
    last = set(gd.index[int(len(gd) * 0.8):])
    inn_tr, inn_va = tr[~tr.game_id.isin(last)], tr[tr.game_id.isin(last)]
    lres = []
    for nl, md in LGB_GRID:
        t1 = time.time()
        dtr = M.lgb_dataset(inn_tr)
        dva = M.lgb_dataset(inn_va, ref=dtr)
        ev = {}
        bst = lgb.train(M.lgb_params(nl, md, SEED1, a.threads), dtr, num_boost_round=3000, valid_sets=[dva],
                        valid_names=["va"], callbacks=[lgb.early_stopping(50, verbose=False), lgb.record_evaluation(ev)])
        lres.append(dict(num_leaves=nl, min_data_in_leaf=md, best_iter=int(bst.best_iteration),
                         inner_logloss=float(min(ev["va"]["multi_logloss"])), secs=round(time.time() - t1)))
        print(now(), lres[-1], flush=True)
    lb = min(lres, key=lambda x: x["inner_logloss"])
    fz = dict(spec="docs/models/shot_attribute/experiments.md SL-R1", tuned_on="fold 1 only (train 2021-22 + 2022-23, test 2023-24)",
              w=best["w"], prior_strength_attempts=best["b"], ratings_grid=grid, ratings_selection="max fold-1 L1 test LL per attempt among grid cells whose fold-1 offline "
              "spread ratios (for and against) lie in [0.8, 1.2] (L24 guard, labelled interpretation)",
              best_ll_any_cell=dict(w=best_any["w"], b=best_any["b"], ll=best_any["ll_per_attempt"]),
              lgb=dict(num_leaves=lb["num_leaves"], min_data_in_leaf=lb["min_data_in_leaf"], learning_rate=0.05,
                       n_rounds=lb["best_iter"], inner_split="last 20% of fold-1 training games by date",
                       early_stopping_rounds=50, grid=lres),
              alpha0_l0=M.ALPHA0, c_reg_mnl=M.C_REG, elapsed_s=round(time.time() - t0))
    FROZEN.write_text(json.dumps(fz, indent=1))
    print(now(), "wrote", FROZEN, flush=True)


def fit_all(fold, out, threads):
    fz = json.loads(FROZEN.read_text())
    tr, te = frames(fold, fz["w"], fz["prior_strength_attempts"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "models").mkdir(exist_ok=True)
    te[KEEP].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    L = fz["lgb"]
    labels = {}
    for arm in ARMS:
        t1 = time.time()
        if arm == "L0":
            m = M.fit_l0(tr)
            (out / "models" / "L0.json").write_text(json.dumps(m))
        elif arm in ("L1", "L2"):
            m = M.fit_mnl(tr, arm)
            (out / "models" / f"{arm}.json").write_text(json.dumps(m))
        else:
            import lightgbm as lgb
            seed = SEED1 if arm == "L3" else SEED2
            m = lgb.train(M.lgb_params(L["num_leaves"], L["min_data_in_leaf"], seed, threads), M.lgb_dataset(tr),
                          num_boost_round=L["n_rounds"])
            m.save_model(str(out / "models" / f"{arm}.txt"))
        P = M.predict_arm(arm if arm != "L3s2" else "L3", m, te).astype(np.float32)
        if P.shape != (len(te), N_CLASS) or not np.allclose(P.sum(1), 1, atol=1e-4):
            raise ValueError(f"{arm}: bad probability matrix")
        labels[arm] = label(arm)
        np.save(out / f"fold{fold}_pred_{labels[arm]}.npy", P)
        print(now(), f"fold {fold} {arm} -> {labels[arm]} ({time.time() - t1:.0f}s); LL/att "
              f"{M.joint_ll(P, te.cls.to_numpy()).mean():.5f}" if a.verbose_ll else f"fold {fold} {arm} done "
              f"({time.time() - t1:.0f}s)", flush=True)
    (out / "labels_sealed.json").write_text(json.dumps(labels))
    if fold == 2:
        (out / "hashes.json").write_text(json.dumps(sorted(labels.values())))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "fold2", "fold1"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--verbose-ll", dest="verbose_ll", action="store_true")
    ap.add_argument("--reuse-grid", dest="reuse_grid", action="store_true")
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    if a.cmd == "tune":
        cmd_tune(a)
    elif a.cmd == "fold2":
        fit_all(2, RES, a.threads)
    else:
        fit_all(1, RES / "fold1", a.threads)
    print(now(), "done", a.cmd, flush=True)
