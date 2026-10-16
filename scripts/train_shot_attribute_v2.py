"""SL-R2 trainer: arms L0m, L1m, L3m (+ L3m seed 2) with the as-of league location-mix level selected in step 0
(docs/models/shot_attribute/experiments.md SL-R2; level from results/shot_attribute_r2/step0.json).

    train_shot_attribute_v2.py tune    fold 1 only. Ratings grid (w, b) for L1m: the fold-1 LL maximum among grid cells
                                       whose fold-1 ES spread ratios (for and against) both lie in [0.8, 1.2] (L24
                                       guard, explicit in SL-R2); the unconstrained LL-best cell is reported alongside.
                                       LightGBM num_leaves x min_data by early stopping on the time-ordered fold-1 inner
                                       split (last 20% of training games by date), with the level as init_score.
                                       -> docs/models/shot_attribute/sl_r2_frozen_params.json
    train_shot_attribute_v2.py fold2   frozen params; L0m, L1m, L3m (seed 1), L3ms2 (seed 2), plus the labelled
                                       references L0 (SL-R1, no level) and L0o (oracle level; diagnostic, never
                                       selectable); hash-labelled 2024-25 predictions -> results/shot_attribute_r2
    train_shot_attribute_v2.py fold1   the same on fold 1 (diagnostic)
    train_shot_attribute_v2.py check   offset MNL with a zero offset vs SL-R1's sklearn L1 (fold-1 cell w0.7 b1000)
"""
import argparse
import hashlib
import itertools
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.shot_attribute import mix_level as ML  # noqa: E402
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute import models_m as MM  # noqa: E402
from nhl_sim.shot_attribute.tables import N_CLASS  # noqa: E402

RES = Path("results/shot_attribute_r2")
FROZEN = Path("docs/models/shot_attribute/sl_r2_frozen_params.json")
LEVELS = M.SA / "mix_level_v2.parquet"
SALT = "SL-R2-2026-10-16"
GRID_W = (0.5, 0.7, 0.85, 1.0)
GRID_B = (300, 1000, 3000)
LGB_GRID = [(15, 200), (15, 800), (31, 200), (31, 800)]
SEED1, SEED2 = 1, 2
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
ARMS = ("L0m", "L1m", "L3m", "L3ms2", "L0", "L0o")
KEEP = ["game_id", "season", "game_type", "game_date_local", "t", "team", "team_id", "opp_id", "is_home", "st", "grp",
        "sc", "period", "ptype", "cls", "cell", "type6", "is_goal", "d", "rebound", "rush", "own_r", "opp_r",
        "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena", "arena_f", "clock", "l0"]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def level_name(fold):
    sel = json.loads((RES / "step0.json").read_text())["selected"]
    return f"E_f{fold}" if sel == "E" else sel


def level_df(name):
    L = pd.read_parquet(LEVELS)
    return L[L.construction == name]


def frames(fold, w, b):
    tr, te = F[fold]
    r = M.attach_features(M.load_rows(tr + [te]), fold, w, b)
    return r[r.season.isin(tr)].reset_index(drop=True), r[r.season == te].reset_index(drop=True)


def offsets(fold, tr, te, name=None):
    s_train = ML.share_table(tr)
    L = level_df(name or level_name(fold))
    return ML.row_offset(tr, L, s_train), ML.row_offset(te, L, s_train), s_train


def spread_ratio(r, P, xg, col):
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
    otr, ote, _ = offsets(1, tr, te)
    t0 = time.time()
    m = MM.fit_l1m(tr, otr)
    P = MM.predict_l1m(m, te, ote)
    ll = float(M.joint_ll(P, te.cls.to_numpy()).mean())
    xg = np.load(M.SA / "xg_ref_v1_f1.npy")
    sf = spread_ratio(te, P, xg, "own_rf_es")
    sa = spread_ratio(te, P, xg, "opp_ra_es")
    return dict(w=w, b=b, ll_per_attempt=ll, n_test=len(te), spread_for=sf[0], spread_against=sa[0],
                q_for_pred=sf[1], q_for_act=sf[2], q_ag_pred=sa[1], q_ag_act=sa[2], n_iter=m["n_iter"],
                fit_s=round(time.time() - t0))


def cmd_check(a):
    tr, te = frames(1, 0.7, 1000)
    otr, ote, _ = offsets(1, tr, te)
    print(now(), "max |offset| fold 1 train / test", float(np.abs(otr).max()), float(np.abs(ote).max()), flush=True)
    t0 = time.time()
    m = MM.fit_l1m(tr, np.zeros_like(otr))
    P = MM.predict_l1m(m, te, np.zeros_like(ote))
    t1 = time.time()
    m1 = M.fit_mnl(tr, "L1")
    P1 = M.predict_mnl(m1, te)
    print(now(), f"offset-MNL {t1 - t0:.0f}s iters {m['n_iter']}; sklearn {time.time() - t1:.0f}s", flush=True)
    print("LL/att offset-MNL", M.joint_ll(P, te.cls.to_numpy()).mean(), "sklearn", M.joint_ll(P1, te.cls.to_numpy()).mean(),
          "max |dP|", float(np.abs(P - P1).max()), flush=True)


def cmd_tune(a):
    t0 = time.time()
    RES.mkdir(parents=True, exist_ok=True)
    gfile = RES / "ratings_grid_fold1.json"
    if a.reuse_grid and gfile.exists():
        grid = json.loads(gfile.read_text())
    else:
        with ProcessPoolExecutor(a.procs) as ex:
            grid = list(ex.map(_grid_cell, list(itertools.product(GRID_W, GRID_B))))
        gfile.write_text(json.dumps(grid, indent=1))
    for g in grid:
        print(now(), f"w={g['w']} b={g['b']} LL/att {g['ll_per_attempt']:.6f} spread for {g['spread_for']:.3f} "
              f"against {g['spread_against']:.3f} ({g['fit_s']}s)", flush=True)
    inband = [g for g in grid if 0.8 <= g["spread_for"] <= 1.2 and 0.8 <= g["spread_against"] <= 1.2]
    if not inband:
        raise RuntimeError("no grid cell inside the L24 band: the spec has no fallback; stop and report")
    best = max(inband, key=lambda g: g["ll_per_attempt"])
    best_any = max(grid, key=lambda g: g["ll_per_attempt"])
    print(now(), "ratings grid done", f"{time.time() - t0:.0f}s; selected (in band) w={best['w']} b={best['b']}; "
          f"LL-best overall w={best_any['w']} b={best_any['b']}", flush=True)
    import lightgbm as lgb
    tr, te = frames(1, best["w"], best["b"])
    otr, _, _ = offsets(1, tr, te)
    gd = tr.groupby("game_id").game_date_local.first().sort_values(kind="stable")
    last = set(gd.index[int(len(gd) * 0.8):])
    mi = tr.game_id.isin(last).to_numpy()
    lres = []
    for nl, md in LGB_GRID:
        t1 = time.time()
        base = MM.class_base(tr.cls.to_numpy()[~mi])
        dtr = MM.lgb_dataset_m(tr[~mi], otr[~mi], base)
        dva = MM.lgb_dataset_m(tr[mi], otr[mi], base, ref=dtr)
        ev = {}
        bst = lgb.train(M.lgb_params(nl, md, SEED1, a.threads), dtr, num_boost_round=3000, valid_sets=[dva],
                        valid_names=["va"], callbacks=[lgb.early_stopping(50, verbose=False), lgb.record_evaluation(ev)])
        lres.append(dict(num_leaves=nl, min_data_in_leaf=md, best_iter=int(bst.best_iteration),
                         inner_logloss=float(min(ev["va"]["multi_logloss"])), secs=round(time.time() - t1)))
        print(now(), lres[-1], flush=True)
    lb = min(lres, key=lambda x: x["inner_logloss"])
    fz = dict(spec="docs/models/shot_attribute/experiments.md SL-R2", level=json.loads((RES / "step0.json").read_text())["selected"],
              tuned_on="fold 1 only (train 2021-22 + 2022-23, test 2023-24)", w=best["w"], prior_strength_attempts=best["b"],
              ratings_grid=grid, ratings_selection="max fold-1 L1m test LL per attempt among grid cells whose fold-1 ES "
              "spread ratios (for and against) both lie in [0.8, 1.2] (SL-R2 explicit L24 rule)",
              best_ll_any_cell=dict(w=best_any["w"], b=best_any["b"], ll=best_any["ll_per_attempt"],
                                    spread_for=best_any["spread_for"], spread_against=best_any["spread_against"]),
              lgb=dict(num_leaves=lb["num_leaves"], min_data_in_leaf=lb["min_data_in_leaf"], learning_rate=0.05,
                       n_rounds=lb["best_iter"], inner_split="last 20% of fold-1 training games by date",
                       early_stopping_rounds=50, init_score="log training class frequency + level offset on each class's cell", grid=lres),
              alpha0_l0=M.ALPHA0, c_reg_mnl=M.C_REG, elapsed_s=round(time.time() - t0))
    FROZEN.write_text(json.dumps(fz, indent=1))
    print(now(), "wrote", FROZEN, flush=True)


def _fit_one(args):
    fold, arm, threads = args
    fz = json.loads(FROZEN.read_text())
    out = RES if fold == 2 else RES / "fold1"
    tr, te = frames(fold, fz["w"], fz["prior_strength_attempts"])
    if arm == "L0o":
        otr, ote, _ = offsets(fold, tr, te, "O")
    else:
        otr, ote, _ = offsets(fold, tr, te)
    t1 = time.time()
    if arm in ("L0m", "L0", "L0o"):
        m = M.fit_l0(tr)
        (out / "models" / f"{arm}.json").write_text(json.dumps(m))
    elif arm == "L1m":
        m = MM.fit_l1m(tr, otr)
        (out / "models" / "L1m.json").write_text(json.dumps(m))
    else:
        import lightgbm as lgb
        L = fz["lgb"]
        seed = SEED1 if arm == "L3m" else SEED2
        base = MM.class_base(tr.cls.to_numpy())
        bst = lgb.train(M.lgb_params(L["num_leaves"], L["min_data_in_leaf"], seed, threads),
                        MM.lgb_dataset_m(tr, otr, base), num_boost_round=L["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        (out / "models" / f"{arm}.base.json").write_text(json.dumps(base.tolist()))
        m = (bst, base)
    P = MM.predict_arm_m(arm, m, te, ote).astype(np.float32)
    if P.shape != (len(te), N_CLASS) or not np.allclose(P.sum(1), 1, atol=1e-4):
        raise ValueError(f"{arm}: bad probability matrix")
    np.save(out / f"fold{fold}_pred_{label(arm)}.npy", P)
    return arm, round(time.time() - t1)


def fit_all(fold, threads, procs):
    fz = json.loads(FROZEN.read_text())
    out = RES if fold == 2 else RES / "fold1"
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te = frames(fold, fz["w"], fz["prior_strength_attempts"])
    _, ote, _ = offsets(fold, tr, te)
    te = te.assign(**{f"off{c}": ote[:, c] for c in range(ote.shape[1])})
    te[KEEP + [f"off{c}" for c in range(ote.shape[1])]].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    jobs = [(fold, a, threads) for a in ARMS]
    with ProcessPoolExecutor(procs) as ex:
        for arm, s in ex.map(_fit_one, jobs):
            print(now(), f"fold {fold} {arm} done ({s}s)", flush=True)
    labels = {a: label(a) for a in ARMS}
    (out / "labels_sealed.json").write_text(json.dumps(labels))
    if fold == 2:
        (out / "hashes.json").write_text(json.dumps(sorted(labels.values())))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "fold2", "fold1", "check"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--reuse-grid", dest="reuse_grid", action="store_true")
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"tune": cmd_tune, "check": cmd_check, "fold2": lambda a: fit_all(2, a.threads, a.procs),
     "fold1": lambda a: fit_all(1, a.threads, a.procs)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
