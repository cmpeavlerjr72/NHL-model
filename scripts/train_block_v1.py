"""SB-R1 trainer: arms B0, B1, B2 (+ B2 seed 2) with the selected league block-share level
(docs/models/block/experiments.md SB-R1; selection in results/block_sb_r1/step0.json).

    train_block_v1.py tune    fold 1 only. Ratings grid (w, b): max fold-1 B1 test LL among cells whose fold-1 ES
                              Q5-Q1 spread ratios (shooting-team blocked-against and defending-team blocks-for) both
                              lie in [0.8, 1.2] (explicit L24 rule from SL-R2; the unconstrained LL-best is reported).
                              B2 num_leaves {7, 15} x min_data {200, 800} by early stopping on the time-ordered
                              fold-1 inner split (last 20% of training games), init_score = logit of B0 fit on the
                              inner-train part. -> docs/models/block/sb_r1_frozen_params.json
    train_block_v1.py fold2|fold1   frozen params; B0, B1, B2, B2s2 + labelled references B0n (no level) and B0o
                              (oracle level; never selectable); hash-labelled test predictions -> results/block_sb_r1.
                              B2 in-sample stratum check first (block share per strength group within +/-0.2 pp of
                              B0's on training rows): the run stops if it fails.
"""
import argparse
import hashlib
import itertools
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.block import data as D  # noqa: E402
from nhl_sim.block import models as BM  # noqa: E402

RES = Path("results/block_sb_r1")
FROZEN = Path("docs/models/block/sb_r1_frozen_params.json")
SALT = "SB-R1-2026-10-16"
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
LGB_GRID = [(7, 200), (7, 800), (15, 200), (15, 800)]
SEED1, SEED2 = 1, 2
ARMS = ("B0", "B1", "B2", "B2s2", "B0n", "B0o")
KEEP = ["game_id", "season", "game_type", "date", "t", "team", "team_id", "opp_id", "is_home", "st", "grp", "sc", "period",
        "ptype", "y", "rebound", "rush", "own_r", "opp_r", "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena",
        "arena_f", "clock", "off"]
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def selected():
    return json.loads((RES / "step0.json").read_text())["selected"]


def base_tables():
    if not _CACHE:
        _CACHE["a"] = D.load_attempts()
        _CACHE["games"] = pd.read_parquet(D.OUT / "games_v1.parquet")
        _CACHE["rt"] = pd.read_parquet(D.OUT / "ratings_v1.parquet")
        _CACHE["af"] = pd.read_parquet(D.OUT / "arena_v1.parquet")
        _CACHE["L"] = pd.read_parquet(D.OUT / "level_v1.parquet")
    return _CACHE


def frames(fold, w, b, level=None):
    T = base_tables()
    tr_s, te_s = F[fold]
    a = T["a"][T["a"].season.isin(tr_s + [te_s])]
    r = D.assemble(a, T["games"], T["rt"], T["af"], w, b)
    tr = r[r.season.isin(tr_s)].reset_index(drop=True)
    te = r[r.season == te_s].reset_index(drop=True)
    s_train = D.share_table(tr)
    name = level or selected()
    if name == "none":
        otr, ote = np.zeros(len(tr)), np.zeros(len(te))
    else:
        L = T["L"][T["L"].construction == name]
        otr, ote = D.row_offset(tr, L, s_train), D.row_offset(te, L, s_train)
    return tr, te, otr, ote


def spread_ratio(r, p, col):
    es = (r.grp == 0).to_numpy()
    x = r[es]
    tg = x.groupby(["game_id", "team"])[col].first()
    q = pd.qcut(tg.rank(method="first"), 5, labels=False)
    qq = x.join(q.rename("q"), on=["game_id", "team"]).q.to_numpy()
    pm = np.array([p[es][qq == k].mean() for k in range(5)])
    am = np.array([x.y.to_numpy()[qq == k].mean() for k in range(5)])
    return float((pm[4] - pm[0]) / (am[4] - am[0])), pm.tolist(), am.tolist()


def bern_ll(p, y):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return float((y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def _grid_cell(args):
    w, b = args
    tr, te, otr, ote = frames(1, w, b)
    t0 = time.time()
    m = BM.fit_b1(tr, otr)
    p = BM.predict_b1(m, te, ote)
    g = (te.grp <= 2).to_numpy()
    sf = spread_ratio(te, p, "own_rf_es")
    sa = spread_ratio(te, p, "opp_ra_es")
    return dict(w=w, b=b, ll_per_attempt=bern_ll(p[g], te.y.to_numpy()[g]), n_test=int(g.sum()), spread_for=sf[0],
                spread_against=sa[0], q_for_pred=sf[1], q_for_act=sf[2], q_ag_pred=sa[1], q_ag_act=sa[2],
                coef=m["coef"], fit_s=round(time.time() - t0))


def cmd_tune(a):
    t0 = time.time()
    RES.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(a.procs) as ex:
        grid = list(ex.map(_grid_cell, list(itertools.product(D.GRID_W, D.GRID_B))))
    (RES / "ratings_grid_fold1.json").write_text(json.dumps(grid, indent=1))
    for g in grid:
        print(now(), f"w={g['w']} b={g['b']} LL/att {g['ll_per_attempt']:.6f} spread for {g['spread_for']:.3f} "
              f"against {g['spread_against']:.3f} ({g['fit_s']}s)", flush=True)
    inband = [g for g in grid if 0.8 <= g["spread_for"] <= 1.2 and 0.8 <= g["spread_against"] <= 1.2]
    best_any = max(grid, key=lambda g: g["ll_per_attempt"])
    if not inband:
        print(now(), "NO grid cell inside the L24 band; best-any:",
              {k: best_any[k] for k in ("w", "b", "ll_per_attempt", "spread_for", "spread_against")})
        raise RuntimeError("no grid cell inside the L24 band: the spec has no fallback; stop and report")
    best = max(inband, key=lambda g: g["ll_per_attempt"])
    print(now(), f"selected (in band) w={best['w']} b={best['b']}; LL-best overall w={best_any['w']} b={best_any['b']}",
          flush=True)
    import lightgbm as lgb
    tr, te, otr, ote = frames(1, best["w"], best["b"])
    gd = tr.groupby("game_id").date.first().sort_values(kind="stable")
    last = set(gd.index[int(len(gd) * 0.8):])
    mi = tr.game_id.isin(last).to_numpy()
    m0 = BM.fit_b0(tr[~mi].reset_index(drop=True), otr[~mi])
    init = BM.logit(BM.predict_b0(m0, tr, otr))
    lres = []
    for nl, md in LGB_GRID:
        t1 = time.time()
        dtr = BM.lgb_dataset(tr[~mi], init[~mi])
        dva = BM.lgb_dataset(tr[mi], init[mi], ref=dtr)
        ev = {}
        bst = lgb.train(BM.lgb_params(nl, md, SEED1, a.threads), dtr, num_boost_round=3000, valid_sets=[dva],
                        valid_names=["va"], callbacks=[lgb.early_stopping(50, verbose=False), lgb.record_evaluation(ev)])
        lres.append(dict(num_leaves=nl, min_data_in_leaf=md, best_iter=int(bst.best_iteration),
                         inner_logloss=float(min(ev["va"]["binary_logloss"])), secs=round(time.time() - t1)))
        print(now(), lres[-1], flush=True)
    lb = min(lres, key=lambda x: x["inner_logloss"])
    fz = dict(spec="docs/models/block/experiments.md SB-R1", level=selected(),
              tuned_on="fold 1 only (train 2021-22 + 2022-23, test 2023-24)", w=best["w"], prior_strength_attempts=best["b"],
              ratings_grid=[{k: v for k, v in g.items() if k != "coef"} for g in grid],
              ratings_selection="max fold-1 B1 test LL per attempt (graded rows) among grid cells whose fold-1 ES Q5-Q1 "
              "spread ratios (for and against) both lie in [0.8, 1.2] (explicit L24 rule, as SL-R2)",
              best_ll_any_cell=dict(w=best_any["w"], b=best_any["b"], ll=best_any["ll_per_attempt"],
                                    spread_for=best_any["spread_for"], spread_against=best_any["spread_against"]),
              lgb=dict(num_leaves=lb["num_leaves"], min_data_in_leaf=lb["min_data_in_leaf"], learning_rate=0.05,
                       n_rounds=lb["best_iter"], inner_split="last 20% of fold-1 training games by date",
                       early_stopping_rounds=50, init_score="logit of B0 (fit on the inner-train part)", grid=lres),
              c_reg=BM.C_REG, elapsed_s=round(time.time() - t0))
    FROZEN.write_text(json.dumps(fz, indent=1))
    print(now(), "wrote", FROZEN, flush=True)


def _fit_one(args):
    fold, arm, threads = args
    fz = json.loads(FROZEN.read_text())
    out = RES if fold == 2 else RES / "fold1"
    lvl = {"B0n": "none", "B0o": "O"}.get(arm)
    tr, te, otr, ote = frames(fold, fz["w"], fz["prior_strength_attempts"], lvl)
    t1 = time.time()
    chk = None
    if arm in ("B0", "B0n", "B0o"):
        m = BM.fit_b0(tr, otr)
        (out / "models" / f"{arm}.json").write_text(json.dumps(m))
        p = BM.predict_b0(m, te, ote)
    elif arm == "B1":
        m = BM.fit_b1(tr, otr)
        (out / "models" / "B1.json").write_text(json.dumps(m))
        p = BM.predict_b1(m, te, ote)
    else:
        import lightgbm as lgb
        L = fz["lgb"]
        seed = SEED1 if arm == "B2" else SEED2
        m0 = BM.fit_b0(tr, otr)
        p0tr = BM.predict_b0(m0, tr, otr)
        init = BM.logit(p0tr)
        bst = lgb.train(BM.lgb_params(L["num_leaves"], L["min_data_in_leaf"], seed, threads), BM.lgb_dataset(tr, init),
                        num_boost_round=L["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        ptr = BM.predict_b2(bst, tr, init)
        chk = []
        for g in range(5):
            mk = (tr.grp == g).to_numpy()
            chk.append(dict(grp=g, n=int(mk.sum()), b2_pct=100 * ptr[mk].mean(), b0_pct=100 * p0tr[mk].mean(),
                            diff_pp=100 * (ptr[mk].mean() - p0tr[mk].mean()), gated=g <= 2))
        init_te = BM.logit(BM.predict_b0(m0, te, ote))
        p = BM.predict_b2(bst, te, init_te)
    p = p.astype(np.float64)
    if p.shape != (len(te),) or not np.isfinite(p).all():
        raise ValueError(f"{arm}: bad probabilities")
    np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p.astype(np.float32))
    return arm, round(time.time() - t1), chk


def fit_all(fold, threads, procs):
    fz = json.loads(FROZEN.read_text())
    out = RES if fold == 2 else RES / "fold1"
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te, otr, ote = frames(fold, fz["w"], fz["prior_strength_attempts"])
    te = te.assign(off=ote)
    te[KEEP].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    # B2 stratum check first (L32): stop on failure before any other arm is written
    arm, s, chk = _fit_one((fold, "B2", threads))
    (out / "b2_stratum_check.json").write_text(json.dumps(chk, indent=1))
    print(now(), "B2 in-sample stratum check (grp, diff pp)", [(r["grp"], round(r["diff_pp"], 3)) for r in chk], flush=True)
    bad = [r for r in chk if r["gated"] and abs(r["diff_pp"]) > 0.2]
    if bad:
        raise SystemExit(f"B2 in-sample stratum check FAILED: {bad}; stopping (spec)")
    jobs = [(fold, a_, threads) for a_ in ARMS if a_ != "B2"]
    with ProcessPoolExecutor(procs) as ex:
        for arm, s, _ in ex.map(_fit_one, jobs):
            print(now(), f"fold {fold} {arm} done ({s}s)", flush=True)
    labels = {a_: label(a_) for a_ in ARMS}
    (out / "labels_sealed.json").write_text(json.dumps(labels))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["tune", "fold2", "fold1"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"tune": cmd_tune, "fold2": lambda a: fit_all(2, a.threads, a.procs),
     "fold1": lambda a: fit_all(1, a.threads, a.procs)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
