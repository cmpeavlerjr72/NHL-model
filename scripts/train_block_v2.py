"""SB-R2 trainer (docs/models/block/experiments.md SB-R2, D27): B0 / B1 / B2 with calibrated-spread rating shrinkage.

    train_block_v2.py select   fold 1 only. 12-cell grid b {1000,3000,10000,30000} x w {0.5,0.7,0.85}: B1 fold-1 test LL
                               per game, ES spread ratios. Rule: among cells with fold-1 LL within 2 paired SE (1,000
                               game-block bootstrap) of the best cell, minimise max(|log for|, |log against|); ties within
                               0.02 go to the larger b. -> results/block_sb_r2/select.json, docs/tests/block_sb_r2_select_2026-10-16.md
    train_block_v2.py fold2|fold1   B0, B1, B2, B2s2 + refs B0n, B0o with the selected cell; booster hyperparameters as frozen
                               in SB-R1 (docs/models/block/sb_r1_frozen_params.json). Level M1_K500 (SB-R1 step 0).
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

RES = Path("results/block_sb_r2")
FROZEN1 = Path("docs/models/block/sb_r1_frozen_params.json")
SELECT = RES / "select.json"
SALT = "SB-R2-2026-10-16"
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
GRID_W, GRID_B = (0.5, 0.7, 0.85), (1000, 3000, 10000, 30000)
LEVEL = "M1_K500"
ARMS = ("B0", "B1", "B2", "B2s2", "B0n", "B0o")
KEEP = ["game_id", "season", "game_type", "date", "t", "team", "team_id", "opp_id", "is_home", "st", "grp", "sc", "period",
        "ptype", "y", "rebound", "rush", "own_r", "opp_r", "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena",
        "arena_f", "clock", "off"]
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def base_tables():
    if not _CACHE:
        _CACHE["a"] = D.load_attempts()
        _CACHE["games"] = pd.read_parquet(D.OUT / "games_v1.parquet")
        _CACHE["rt"] = pd.read_parquet(D.OUT / "ratings_v2.parquet")
        _CACHE["af"] = pd.read_parquet(D.OUT / "arena_v1.parquet")
        _CACHE["L"] = pd.read_parquet(D.OUT / "level_v1.parquet")
    return _CACHE


def frames(fold, w, b, level=LEVEL):
    T = base_tables()
    tr_s, te_s = F[fold]
    a = T["a"][T["a"].season.isin(tr_s + [te_s])]
    r = D.assemble(a, T["games"], T["rt"], T["af"], w, b)
    tr = r[r.season.isin(tr_s)].reset_index(drop=True)
    te = r[r.season == te_s].reset_index(drop=True)
    s_train = D.share_table(tr)
    if level == "none":
        return tr, te, np.zeros(len(tr)), np.zeros(len(te))
    L = T["L"][T["L"].construction == level]
    return tr, te, D.row_offset(tr, L, s_train), D.row_offset(te, L, s_train)


def spread_ratio(r, p, col):
    es = (r.grp == 0).to_numpy()
    x = r[es]
    tg = x.groupby(["game_id", "team"])[col].first()
    q = pd.qcut(tg.rank(method="first"), 5, labels=False)
    qq = x.join(q.rename("q"), on=["game_id", "team"]).q.to_numpy()
    pm = np.array([p[es][qq == k].mean() for k in range(5)])
    am = np.array([x.y.to_numpy()[qq == k].mean() for k in range(5)])
    return float((pm[4] - pm[0]) / (am[4] - am[0])), pm.tolist(), am.tolist()


def _grid_cell(args):
    b, w = args
    tr, te, otr, ote = frames(1, w, b)
    t0 = time.time()
    m = BM.fit_b1(tr, otr)
    p = BM.predict_b1(m, te, ote)
    g = (te.grp <= 2).to_numpy()
    y = te.y.to_numpy().astype(float)
    ll = y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))
    games = np.sort(te.game_id.unique())
    gp = np.searchsorted(games, te.game_id.to_numpy())
    llg = np.bincount(gp[g], weights=ll[g], minlength=len(games))
    sf, sa = spread_ratio(te, p, "own_rf_es"), spread_ratio(te, p, "opp_ra_es")
    return dict(w=w, b=b, ll_per_attempt=float(ll[g].mean()), ll_game=llg.tolist(), spread_for=sf[0], spread_against=sa[0],
                q_for_pred=sf[1], q_for_act=sf[2], q_ag_pred=sa[1], q_ag_act=sa[2], fit_s=round(time.time() - t0))


def cmd_select(a):
    RES.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(a.procs) as ex:
        grid = list(ex.map(_grid_cell, list(itertools.product(GRID_B, GRID_W))))
    G = len(grid[0]["ll_game"])
    W = np.random.default_rng(20261016).multinomial(G, np.full(G, 1.0 / G), size=1000).astype(float)
    llg = np.array([c["ll_game"] for c in grid])
    best = int(np.argmax(llg.sum(1)))
    for i, c in enumerate(grid):
        d = llg[i] - llg[best]
        c["ll_game_vs_best"] = float(d.mean())
        c["se_vs_best"] = float(np.std(W @ d / G)) if i != best else 0.0
        c["in_2se"] = bool(c["ll_game_vs_best"] >= -2 * c["se_vs_best"])
        c["max_abs_log_ratio"] = float(max(abs(np.log(c["spread_for"])), abs(np.log(c["spread_against"]))))
    elig = [c for c in grid if c["in_2se"]]
    m = min(c["max_abs_log_ratio"] for c in elig)
    near = [c for c in elig if c["max_abs_log_ratio"] <= m + 0.02]
    sel = sorted(near, key=lambda c: (-c["b"], c["max_abs_log_ratio"]))[0]
    out = dict(selected=dict(w=sel["w"], b=sel["b"]), best_ll_cell=dict(w=grid[best]["w"], b=grid[best]["b"]),
               min_metric=m, n_games=G, grid=[{k: v for k, v in c.items() if k != "ll_game"} for c in grid])
    SELECT.write_text(json.dumps(out, indent=1))
    T = pd.DataFrame([{k: c[k] for k in ("b", "w", "ll_per_attempt", "ll_game_vs_best", "se_vs_best", "in_2se",
                                         "spread_for", "spread_against", "max_abs_log_ratio")} for c in grid])
    L = ["# SB-R2 step 1: fold-1 rating-shrinkage selection (Lane B2, 2026-10-16)", "",
         "Committed BEFORE any fold-2 fit. Rule (SB-R2, D27): cells with fold-1 B1 LL within 2 paired SE (1,000 game-block "
         "bootstrap, vs the best-LL cell) of the best; among them minimise max(|log for-ratio|, |log against-ratio|) of the fold-1 "
         "ES Q5-Q1 spread ratios; ties within 0.02 go to the larger b. Level M1_K500; booster frozen from SB-R1.", "",
         T.to_markdown(index=False, floatfmt=".4f"), "",
         f"- Best-LL cell: b {grid[best]['b']}, w {grid[best]['w']} (n_games {G}).",
         f"- Min max|log ratio| among in-2SE cells: {m:.4f}; cells within 0.02: "
         f"{[(c['b'], c['w'], round(c['max_abs_log_ratio'], 4)) for c in near]}.",
         f"- **Selected: b {sel['b']}, w {sel['w']}** (spread for {sel['spread_for']:.3f}, against {sel['spread_against']:.3f}).", ""]
    Path("docs/tests/block_sb_r2_select_2026-10-16.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)


def _fit_one(args):
    fold, arm, threads = args
    sel = json.loads(SELECT.read_text())["selected"]
    fz = json.loads(FROZEN1.read_text())
    out = RES if fold == 2 else RES / "fold1"
    lvl = {"B0n": "none", "B0o": "O"}.get(arm, LEVEL)
    tr, te, otr, ote = frames(fold, sel["w"], sel["b"], lvl)
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
        seed = 1 if arm == "B2" else 2
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
            chk.append(dict(grp=g, n=int(mk.sum()), diff_pp=100 * (ptr[mk].mean() - p0tr[mk].mean()), gated=g <= 2))
        p = BM.predict_b2(bst, te, BM.logit(BM.predict_b0(m0, te, ote)))
    p = p.astype(np.float64)
    if p.shape != (len(te),) or not np.isfinite(p).all():
        raise ValueError(f"{arm}: bad probabilities")
    np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p.astype(np.float32))
    return arm, round(time.time() - t1), chk


def fit_all(fold, threads, procs):
    sel = json.loads(SELECT.read_text())["selected"]
    out = RES if fold == 2 else RES / "fold1"
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te, otr, ote = frames(fold, sel["w"], sel["b"])
    te.assign(off=ote)[KEEP].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    arm, s, chk = _fit_one((fold, "B2", threads))
    (out / "b2_stratum_check.json").write_text(json.dumps(chk, indent=1))
    print(now(), "B2 in-sample stratum check", [(r["grp"], round(r["diff_pp"], 3)) for r in chk], flush=True)
    bad = [r for r in chk if r["gated"] and abs(r["diff_pp"]) > 0.2]
    if bad:
        raise SystemExit(f"B2 in-sample stratum check FAILED: {bad}; stopping (spec)")
    with ProcessPoolExecutor(procs) as ex:
        for arm, s, _ in ex.map(_fit_one, [(fold, a_, threads) for a_ in ARMS if a_ != "B2"]):
            print(now(), f"fold {fold} {arm} done ({s}s)", flush=True)
    (out / "labels_sealed.json").write_text(json.dumps({a_: label(a_) for a_ in ARMS}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["select", "fold2", "fold1"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"select": cmd_select, "fold2": lambda a: fit_all(2, a.threads, a.procs),
     "fold1": lambda a: fit_all(1, a.threads, a.procs)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
