"""SM-R1 trainer (docs/models/miss/experiments.md SM-R1): miss vs on-goal decision, arms S0 / S1 / S2 (+ S2 seed 2).

  Level: the step-1 selection (results/miss_sm_r1/step1.json), entered as a logit offset per level group.
  S1 rating scale: the shooting team's road-only miss rating enters as the FIXED offset s x c (c = fold-1-train-fitted
  coefficient of the rating in an S1 fit with the rating free, raw units; s in {0.25, 0.5, 0.75, 1.0, 1.25}); s is chosen on
  fold 1 by the ES decile-slope R (D32) closest to 1 among s with fold-1 LL within 2 paired SE of the best. Not refit on fold 2.

    train_miss_v1.py select     fold 1 only -> results/miss_sm_r1/select.json, docs/tests/miss_sm_r1_select_2026-10-16.md
    train_miss_v1.py tune       fold 1 only: S2 num_leaves {7, 15} x min_data {200, 800}, early stopping on the time-ordered
                                inner split (last 20% of fold-1 training games) -> docs/models/miss/sm_r1_frozen_params.json
    train_miss_v1.py fold2|fold1   S0, S1, S2, S2s2 with frozen s, c, booster; hash-labelled predictions
"""
import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402
from nhl_sim.miss import data as M  # noqa: E402
from nhl_sim.miss import models as MM  # noqa: E402

RES = Path("results/miss_sm_r1")
FROZEN = Path("docs/models/miss/sm_r1_frozen_params.json")
SELECT = RES / "select.json"
SALT = "SM-R1-2026-10-16"
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
S_GRID = (0.25, 0.5, 0.75, 1.0, 1.25)
LGB_GRID = [(7, 200), (7, 800), (15, 200), (15, 800)]
ARMS = ("S0", "S1", "S2", "S2s2")
COMMON = ["game_id", "season", "game_type", "date", "t", "team", "team_id", "opp_id", "is_home", "st", "grp", "sc", "period",
          "ptype", "y", "is_goal", "event", "cell", "type6", "rebound", "rush", "b2b_own", "b2b_opp", "arena", "arena_f",
          "clock", "off", "own_r", "own_rf_es"]
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def level_name():
    return json.loads((RES / "step1.json").read_text())["selected"]


def frames(fold):
    if fold not in _CACHE:
        tr_s, te_s = F[fold]
        a = M.load_rows(tr_s + [te_s])
        games = pd.read_parquet(M.OUT / "games_v1.parquet")
        rt = pd.read_parquet(M.OUT / "ratings_v1.parquet")
        af = pd.read_parquet(M.OUT / "arena_v1.parquet")
        r = M.assemble(a, games, rt, af)
        tr = r[r.season.isin(tr_s)].reset_index(drop=True)
        te = r[r.season == te_s].reset_index(drop=True)
        L = pd.read_parquet(M.OUT / "level_v1.parquet")
        L = L[L.construction == level_name()]
        s_train = M.share_table(tr)
        otr, ote = M.row_offset(tr, L, s_train), M.row_offset(te, L, s_train)
        m0 = MM.fit_s0(tr, otr)
        tr["off"] = otr
        te["off"] = ote
        _CACHE[fold] = (tr, te, m0, MM.s0_logit(m0, tr, otr), MM.s0_logit(m0, te, ote))
    return _CACHE[fold]


def ll_vec(p, y):
    return y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))


def es_R(te, p, n_boot=1000):
    es = (te.grp == 0).to_numpy()
    x = te[es]
    return slope_ratio(p[es], x.y.to_numpy(float), x.own_rf_es.to_numpy(float), np.ones(es.sum()), x.game_id.to_numpy(),
                       n_buckets=10, n_boot=n_boot)


def coef_fold1():
    f = RES / "coef_fold1.json"
    if f.exists():
        return json.loads(f.read_text())
    tr, te, m0, ltr, lte = frames(1)
    g = (tr.grp <= 2).to_numpy()
    m = MM.fit_s1_free(tr[g].reset_index(drop=True), ltr[g])
    c = dict(rating=m["coef"][MM.I_RATE], arena=m["coef"][MM.I_RATE - 1], home=m["coef"][MM.I_RATE - 4])
    f.write_text(json.dumps(c))
    return c


def cmd_select(a):
    RES.mkdir(parents=True, exist_ok=True)
    tr, te, m0, ltr, lte = frames(1)
    c = coef_fold1()["rating"]
    gt, ge = (tr.grp <= 2).to_numpy(), (te.grp <= 2).to_numpy()
    trg = tr[gt].reset_index(drop=True)
    y = te.y.to_numpy().astype(float)
    games = np.sort(te.game_id.unique())
    gp = np.searchsorted(games, te.game_id.to_numpy())
    G = len(games)
    cells = []
    for s in S_GRID:
        m = MM.fit_s1(trg, ltr[gt], c, s)
        p = MM.predict_s0(m0, te, te.off.to_numpy())
        p[ge] = MM.predict_s1(m, te[ge].reset_index(drop=True), lte[ge])
        ll = ll_vec(p, y)
        R = es_R(te, p, n_boot=1000)
        cells.append(dict(s=s, ll_per_attempt=float(ll[ge].mean()), ll_game=np.bincount(gp[ge], weights=ll[ge], minlength=G),
                          R=R["R"], ci=R["ci"], old=R["old_q5q1"], status=R["status"], under=R["underpowered"], b=R["b"]))
        print(now(), "s", s, f"LL/att {cells[-1]['ll_per_attempt']:.6f} R {R['R']:.3f} CI {R['ci']}", flush=True)
    p0 = MM.predict_s0(m0, te, te.off.to_numpy())
    R0 = es_R(te, p0, n_boot=1000)
    W = np.random.default_rng(20261016).multinomial(G, np.full(G, 1.0 / G), size=1000).astype(float)
    llg = np.array([c_["ll_game"] for c_ in cells])
    best = int(np.argmax(llg.sum(1)))
    for i, c_ in enumerate(cells):
        d = llg[i] - llg[best]
        c_["ll_game_vs_best"] = float(d.mean())
        c_["se_vs_best"] = float(np.std(W @ d / G)) if i != best else 0.0
        c_["in_2se"] = bool(c_["ll_game_vs_best"] >= -2 * c_["se_vs_best"])
        c_["metric"] = float(abs(np.log(c_["R"]))) if c_["R"] > 0 else float("inf")
    elig = [c_ for c_ in cells if c_["in_2se"]]
    pick = min(elig, key=lambda c_: (c_["metric"], c_["s"]))
    corr_arena = float(np.corrcoef(trg.own_rf_es, trg.arena_f)[0, 1])
    out = dict(s=pick["s"], c=c, coef=coef_fold1(), metric=pick["metric"], R=pick["R"], best_ll_s=cells[best]["s"], n_games=G,
               s0_R=R0["R"], s0_R_ci=R0["ci"], corr_rating_arena_train_rows_ES=corr_arena,
               grid=[{k: v for k, v in c_.items() if k != "ll_game"} for c_ in cells])
    SELECT.write_text(json.dumps(out, indent=1))
    T = pd.DataFrame([{k: c_[k] for k in ("s", "ll_per_attempt", "ll_game_vs_best", "se_vs_best", "in_2se", "R", "old", "status",
                                         "under", "metric")} for c_ in cells])
    ci = "; ".join(f"s={c_['s']}: [{c_['ci'][0]:.2f}, {c_['ci'][1]:.2f}]" for c_ in cells)
    L = ["# SM-R1 step 2: fold-1 s-grid selection for the shooting team's road-only miss rating (Lane M, 2026-10-16)", "",
         f"Generated {now()} by `scripts/train_miss_v1.py select`. Committed BEFORE any fold-2 fit. Rule (SM-R1): the rating "
         "enters S1 as the fixed offset s x c (c = the fold-1-train-fitted coefficient of the rating in an S1 fit with the rating "
         "free, raw units; the other S1 features are refit at each s). Among s with fold-1 LL within 2 paired SE (1,000 "
         "game-block bootstrap, vs the best-LL s) of the best, pick the s whose fold-1 ES decile-slope R (D32) is closest to 1, "
         "i.e. minimal |log R|; exact ties go to the smaller s. Level " + level_name() + ". Fold 1 = train 2021-22 + 2022-23, "
         "test 2023-24, " + f"{G} games, {int(ge.sum()):,} gated test attempts. S1 is fit on gated rows (ES / PP / PK); EN rows "
         "are not in this table. R is the point estimate; old = Q5-Q1 endpoint ratio (reported only).", "",
         f"Fold-1 fitted rating coefficient c = {c:.4f} per unit of rating (raw units; arena-factor coefficient "
         f"{coef_fold1()['arena']:.3f}, home {coef_fold1()['home']:.3f}). Corr(rating, arena factor) on ES training rows: "
         f"{corr_arena:+.3f} (road-only construction; the incumbent block ratings were +0.19 / +0.14).", "",
         T.to_markdown(index=False, floatfmt=".4f"), "", "R 95% game-bootstrap CIs: " + ci + ".", "",
         f"- **Selected s = {pick['s']}** (R {pick['R']:.3f}; best-LL s {cells[best]['s']}).",
         f"- S0 (flat reference) fold-1 ES R = {R0['R']:.3f}, CI [{R0['ci'][0]:.2f}, {R0['ci'][1]:.2f}].", f"- n_games {G}."]
    Path("docs/tests/miss_sm_r1_select_2026-10-16.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L), flush=True)


def cmd_tune(a):
    import lightgbm as lgb
    t0 = time.time()
    sel = json.loads(SELECT.read_text())
    tr, te, m0, ltr, lte = frames(1)
    g = (tr.grp <= 2).to_numpy()
    trg = tr[g].reset_index(drop=True)
    gd = trg.groupby("game_id").date.first().sort_values(kind="stable")
    last = set(gd.index[int(len(gd) * 0.8):])
    mi = trg.game_id.isin(last).to_numpy()
    m0i = MM.fit_s0(trg[~mi].reset_index(drop=True), trg.off.to_numpy()[~mi])
    init = MM.s0_logit(m0i, trg, trg.off.to_numpy())
    lres = []
    for nl, md in LGB_GRID:
        t1 = time.time()
        dtr = MM.lgb_dataset(trg[~mi], init[~mi])
        dva = MM.lgb_dataset(trg[mi], init[mi], ref=dtr)
        ev = {}
        bst = lgb.train(MM.lgb_params(nl, md, 1, a.threads), dtr, num_boost_round=3000, valid_sets=[dva], valid_names=["va"],
                        callbacks=[lgb.early_stopping(50, verbose=False), lgb.record_evaluation(ev)])
        lres.append(dict(num_leaves=nl, min_data_in_leaf=md, best_iter=int(bst.best_iteration),
                         inner_logloss=float(min(ev["va"]["binary_logloss"])), secs=round(time.time() - t1)))
        print(now(), lres[-1], flush=True)
    lb = min(lres, key=lambda x: x["inner_logloss"])
    fz = dict(spec="docs/models/miss/experiments.md SM-R1", level=level_name(),
              tuned_on="fold 1 only (train 2021-22 + 2022-23, test 2023-24)", s=sel["s"], c=sel["c"],
              lgb=dict(num_leaves=lb["num_leaves"], min_data_in_leaf=lb["min_data_in_leaf"], learning_rate=0.05,
                       n_rounds=lb["best_iter"], inner_split="last 20% of fold-1 training games by date",
                       early_stopping_rounds=50, init_score="logit of S0 (fit on the inner-train part)", features=MM.LGB_FEATURES,
                       grid=lres), elapsed_s=round(time.time() - t0))
    FROZEN.write_text(json.dumps(fz, indent=1))
    print(now(), "wrote", FROZEN, flush=True)


def fit_arm(fold, arm, threads, fz):
    tr, te, m0, ltr, lte = frames(fold)
    gt, ge = (tr.grp <= 2).to_numpy(), (te.grp <= 2).to_numpy()
    p = MM.predict_s0(m0, te, te.off.to_numpy())
    out, chk = RES if fold == 2 else RES / "fold1", None
    if arm == "S1":
        m = MM.fit_s1(tr[gt].reset_index(drop=True), ltr[gt], fz["c"], fz["s"])
        p[ge] = MM.predict_s1(m, te[ge].reset_index(drop=True), lte[ge])
        (out / "models" / "S1.json").write_text(json.dumps(m, default=float))
    elif arm in ("S2", "S2s2"):
        import lightgbm as lgb
        L = fz["lgb"]
        trg = tr[gt].reset_index(drop=True)
        bst = lgb.train(MM.lgb_params(L["num_leaves"], L["min_data_in_leaf"], 1 if arm == "S2" else 2, threads),
                        MM.lgb_dataset(trg, ltr[gt]), num_boost_round=L["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        ptr = MM.predict_s2(bst, trg, ltr[gt])
        p0tr = 1 / (1 + np.exp(-ltr[gt]))
        chk = [dict(grp=k, n=int((trg.grp == k).sum()), diff_pp=100 * (ptr[(trg.grp == k).to_numpy()].mean()
                                                                       - p0tr[(trg.grp == k).to_numpy()].mean()))
               for k in range(3)]
        p[ge] = MM.predict_s2(bst, te[ge].reset_index(drop=True), lte[ge])
    p = p.astype(np.float64)
    if p.shape != (len(te),) or not np.isfinite(p).all():
        raise ValueError(f"{arm}: bad probabilities")
    np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p.astype(np.float32))
    return chk


def fit_all(fold, threads):
    fz = json.loads(FROZEN.read_text())
    out = RES if fold == 2 else RES / "fold1"
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te, m0, ltr, lte = frames(fold)
    te[COMMON].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    (out / "models" / "S0.json").write_text(json.dumps(m0, default=float))
    chk = fit_arm(fold, "S2", threads, fz)
    (out / "s2_stratum_check.json").write_text(json.dumps(chk, indent=1))
    print(now(), "S2 in-sample stratum check (grp, diff pp)", [(r["grp"], round(r["diff_pp"], 3)) for r in chk], flush=True)
    bad = [r for r in chk if abs(r["diff_pp"]) > 0.2]
    if bad:
        raise SystemExit(f"S2 in-sample stratum check FAILED: {bad}; stopping (spec)")
    for arm in ("S0", "S1", "S2s2"):
        t1 = time.time()
        fit_arm(fold, arm, threads, fz)
        print(now(), f"fold {fold} {arm} done ({round(time.time() - t1)}s)", flush=True)
    (out / "labels_sealed.json").write_text(json.dumps({a_: label(a_) for a_ in ARMS}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["select", "tune", "fold2", "fold1"])
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"select": cmd_select, "tune": cmd_tune, "fold2": lambda a: fit_all(2, a.threads),
     "fold1": lambda a: fit_all(1, a.threads)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
