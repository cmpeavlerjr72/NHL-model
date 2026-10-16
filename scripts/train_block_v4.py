"""SB-R4 trainer (docs/models/block/experiments.md SB-R4, D32): arena-free block ratings at a fixed, spread-tuned scale.

  Rr / Ra  as-of block ratings (b 1000, w 0.7): road games only / all games with counts adjusted by the as-of arena factor
           (data_v4.py, ratings_r4_{Rr,Ra}.parquet).
  B1r / B1a  B0 + score + home + rest + arena factor (all fitted) + the two ratings (own_r = shooting team's blocked-against,
           opp_r = defending team's blocks-for) entering as a FIXED offset s x c, c = the fold-1-train-fitted B1 coefficient of
           that rating (raw units), s chosen on fold 1 from {0.25, 0.5, 0.75, 1.0, 1.25}. Not refit on fold 2.
  B2x      LightGBM (SB-R1 frozen booster), init_score = logit of the better construction's B1 (by the fold-1 s-rule criterion),
           no rating features in the trees. B2xs2 = seed-2 retrain (noise floor).

    train_block_v4.py select       fold 1 only -> results/block_sb_r4/select.json, docs/tests/block_sb_r4_select_2026-10-16.md
    train_block_v4.py fold2|fold1  B0, B1r, B1a, B2x, B2xs2 with the selected scales; hash-labelled predictions
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
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402

RES = Path("results/block_sb_r4")
FROZEN1 = Path("docs/models/block/sb_r1_frozen_params.json")
SELECT = RES / "select.json"
SALT = "SB-R4-2026-10-16"
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
LEVEL = "M1_K500"
S_GRID = (0.25, 0.5, 0.75, 1.0, 1.25)
CONS = ("Rr", "Ra")
ARMS = ("B0", "B1r", "B1a", "B2x", "B2xs2")
I_OWN, I_OPP = 19, 20
LGB_P = [c for c in BM.LGB_FEATURES if c not in ("own_r", "opp_r")]
COMMON = ["game_id", "season", "game_type", "date", "t", "team", "team_id", "opp_id", "is_home", "st", "grp", "sc", "period",
          "ptype", "y", "rebound", "rush", "b2b_own", "b2b_opp", "arena", "arena_f", "clock", "off"]
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(fold, cons):
    key = (fold, cons)
    if key not in _CACHE:
        tr_s, te_s = F[fold]
        a = D.load_attempts(tr_s + [te_s])
        games = pd.read_parquet(D.OUT / "games_v1.parquet")
        rt = pd.read_parquet(D.OUT / f"ratings_r4_{cons}.parquet")
        af = pd.read_parquet(D.OUT / "arena_v1.parquet")
        r = D.assemble(a, games, rt, af, 0.7, 1000)
        tr = r[r.season.isin(tr_s)].reset_index(drop=True)
        te = r[r.season == te_s].reset_index(drop=True)
        L = pd.read_parquet(D.OUT / "level_v1.parquet")
        L = L[L.construction == LEVEL]
        s_train = D.share_table(tr)
        _CACHE[key] = (tr, te, D.row_offset(tr, L, s_train), D.row_offset(te, L, s_train))
    return _CACHE[key]


def coef_fold1(cons):
    """The fold-1-train-fitted B1 coefficients (raw units) of the two ratings."""
    f = RES / f"coef_fold1_{cons}.json"
    if f.exists():
        return json.loads(f.read_text())
    tr, _, otr, _ = frames(1, cons)
    m = BM.fit_b1(tr, otr)
    c = dict(own=m["coef"][I_OWN], opp=m["coef"][I_OPP])
    f.write_text(json.dumps(c))
    return c


def rating_off(r, c, s):
    return s * (c["own"] * r.own_r.to_numpy(float) + c["opp"] * r.opp_r.to_numpy(float))


def design_nr(r):
    return np.delete(BM.design_b1(r), [I_OWN, I_OPP], axis=1)


def fit_fixed(tr, otr, c, s):
    w, nit = BM.fit_logit_offset(design_nr(tr), tr.y.to_numpy(), otr + rating_off(tr, c, s))
    return dict(arm="B1fixed", coef=w.tolist(), s=s, c=c, n_iter=nit)


def predict_fixed(m, r, off):
    return BM.sigmoid(design_nr(r) @ np.asarray(m["coef"]) + off + rating_off(r, m["c"], m["s"]))


def es_R(te, p, n_boot=1000):
    es = (te.grp == 0).to_numpy()
    x = te[es]
    out = {}
    for nm, col in (("for", "own_rf_es"), ("against", "opp_ra_es")):
        r = slope_ratio(p[es], x.y.to_numpy(float), x[col].to_numpy(float), np.ones(es.sum()), x.game_id.to_numpy(),
                        n_buckets=10, n_boot=n_boot)
        out[nm] = dict(R=r["R"], ci=r["ci"], old=r["old_q5q1"], status=r["status"], under=r["underpowered"])
    return out


def _grid_cell(args):
    cons, s = args
    tr, te, otr, ote = frames(1, cons)
    c = coef_fold1(cons)
    m = fit_fixed(tr, otr, c, s)
    p = predict_fixed(m, te, ote)
    g = (te.grp <= 2).to_numpy()
    y = te.y.to_numpy().astype(float)
    ll = y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))
    games = np.sort(te.game_id.unique())
    gp = np.searchsorted(games, te.game_id.to_numpy())
    llg = np.bincount(gp[g], weights=ll[g], minlength=len(games))
    R = es_R(te, p, n_boot=200)
    return dict(cons=cons, s=s, ll_per_attempt=float(ll[g].mean()), ll_game=llg.tolist(), R_for=R["for"]["R"],
                R_against=R["against"]["R"], ci_for=R["for"]["ci"], ci_against=R["against"]["ci"],
                old_for=R["for"]["old"], old_against=R["against"]["old"], coef_own=c["own"], coef_opp=c["opp"])


def cmd_select(a):
    RES.mkdir(parents=True, exist_ok=True)
    for cn in CONS:
        coef_fold1(cn)
    with ProcessPoolExecutor(a.procs) as ex:
        grid = list(ex.map(_grid_cell, list(itertools.product(CONS, S_GRID))))
    G = len(grid[0]["ll_game"])
    W = np.random.default_rng(20261016).multinomial(G, np.full(G, 1.0 / G), size=1000).astype(float)
    sel = {}
    for cn in CONS:
        cells = [c for c in grid if c["cons"] == cn]
        llg = np.array([c["ll_game"] for c in cells])
        best = int(np.argmax(llg.sum(1)))
        for i, c in enumerate(cells):
            d = llg[i] - llg[best]
            c["ll_game_vs_best"] = float(d.mean())
            c["se_vs_best"] = float(np.std(W @ d / G)) if i != best else 0.0
            c["in_2se"] = bool(c["ll_game_vs_best"] >= -2 * c["se_vs_best"])
            c["metric"] = float(max(abs(np.log(c["R_for"])), abs(np.log(c["R_against"]))))
        elig = [c for c in cells if c["in_2se"]]
        pick = min(elig, key=lambda c: (c["metric"], c["s"]))
        sel[cn] = dict(s=pick["s"], metric=pick["metric"], R_for=pick["R_for"], R_against=pick["R_against"],
                       best_ll_s=cells[best]["s"])
    base = min(CONS, key=lambda cn: (sel[cn]["metric"], CONS.index(cn)))
    out = dict(selected=sel, b2x_base=base, n_games=G,
               coef={cn: json.loads((RES / f"coef_fold1_{cn}.json").read_text()) for cn in CONS},
               grid=[{k: v for k, v in c.items() if k != "ll_game"} for c in grid])
    SELECT.write_text(json.dumps(out, indent=1))
    T = pd.DataFrame([{k: c[k] for k in ("cons", "s", "ll_per_attempt", "ll_game_vs_best", "se_vs_best", "in_2se", "R_for",
                                         "R_against", "old_for", "old_against", "metric")} for c in grid])
    L = ["# SB-R4 step 1: fold-1 s-grid selection (Lane B4, 2026-10-16)", "",
         "Committed BEFORE any fold-2 fit. Rule (SB-R4): the rating enters as the fixed offset s x c (c = fold-1-train-fitted B1 "
         "coefficient of that rating, raw units; the other B1 features are refit). Per construction, among s with fold-1 LL "
         "within 2 paired SE (1,000 game-block bootstrap, vs the best-LL s) of the best, pick the s whose fold-1 ES decile-slope "
         "R (for and against, D32) is closest to 1, i.e. minimal max(|log R_for|, |log R_against|); exact ties go to the smaller s. "
         "B2x's base is the construction with the smaller selected metric (tie: Rr). Level M1_K500; fold 1 = train 2021-22 + "
         "2022-23, test 2023-24. R is the point estimate (CIs are in select.json); old = Q5-Q1 endpoint ratio "
         "(reported only).", "",
         "Fold-1 fitted coefficients c (own / opp): " + "; ".join(
             f"{cn} {out['coef'][cn]['own']:.4f} / {out['coef'][cn]['opp']:.4f}" for cn in CONS) + ".", "",
         T.to_markdown(index=False, floatfmt=".4f"), ""]
    for cn in CONS:
        L.append(f"- **{cn}: selected s = {sel[cn]['s']}** (R for {sel[cn]['R_for']:.3f}, against {sel[cn]['R_against']:.3f}; "
                 f"best-LL s {sel[cn]['best_ll_s']}).")
    L += [f"- **B2x base = {base}** (smaller selected metric).", f"- n_games {G}."]
    Path("docs/tests/block_sb_r4_select_2026-10-16.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L), flush=True)


def _fit_one(args):
    fold, arm, threads = args
    S = json.loads(SELECT.read_text())
    out = RES if fold == 2 else RES / "fold1"
    t1 = time.time()
    chk, info = None, {}
    cons = {"B1r": "Rr", "B1a": "Ra", "B0": "Rr"}.get(arm, S["b2x_base"])
    tr, te, otr, ote = frames(fold, cons)
    if arm == "B0":
        m = BM.fit_b0(tr, otr)
        p = BM.predict_b0(m, te, ote)
    elif arm in ("B1r", "B1a"):
        m = fit_fixed(tr, otr, S["coef"][cons], S["selected"][cons]["s"])
        p = predict_fixed(m, te, ote)
        info = dict(s=m["s"], coef_own=S["coef"][cons]["own"], coef_opp=S["coef"][cons]["opp"], coef_arena=m["coef"][-1],
                    coef_home=m["coef"][-4])
    else:
        import lightgbm as lgb
        L = json.loads(FROZEN1.read_text())["lgb"]
        seed = 1 if arm == "B2x" else 2
        m1 = fit_fixed(tr, otr, S["coef"][cons], S["selected"][cons]["s"])
        init = BM.logit(predict_fixed(m1, tr, otr))
        m0 = BM.fit_b0(tr, otr)
        p0tr = BM.predict_b0(m0, tr, otr)
        ds = lgb.Dataset(tr[LGB_P].astype(float), label=tr.y.to_numpy(), categorical_feature=["grp"], free_raw_data=False,
                         init_score=init)
        bst = lgb.train(BM.lgb_params(L["num_leaves"], L["min_data_in_leaf"], seed, threads), ds,
                        num_boost_round=L["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        ptr = BM.sigmoid(bst.predict(tr[LGB_P].astype(float), raw_score=True) + init)
        chk = []
        for g in range(5):
            mk = (tr.grp == g).to_numpy()
            chk.append(dict(grp=g, n=int(mk.sum()), diff_pp=100 * (ptr[mk].mean() - p0tr[mk].mean()), gated=g <= 2))
        init_te = BM.logit(predict_fixed(m1, te, ote))
        p = BM.sigmoid(bst.predict(te[LGB_P].astype(float), raw_score=True) + init_te)
        m = None
        info = dict(base=cons)
    if m is not None:
        (out / "models" / f"{arm}.json").write_text(json.dumps(m, default=float))
    p = p.astype(np.float64)
    if p.shape != (len(te),) or not np.isfinite(p).all():
        raise ValueError(f"{arm}: bad probabilities")
    np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p.astype(np.float32))
    return arm, round(time.time() - t1), chk, {k: (v if isinstance(v, str) else float(v)) for k, v in info.items()}


def fit_all(fold, threads, procs):
    out = RES if fold == 2 else RES / "fold1"
    (out / "models").mkdir(parents=True, exist_ok=True)
    rows = None
    for cn in CONS:
        tr, te, otr, ote = frames(fold, cn)
        if rows is None:
            rows = te.assign(off=ote)[COMMON].copy()
        else:
            assert (rows.game_id.to_numpy() == te.game_id.to_numpy()).all() and (rows.t.to_numpy() == te.t.to_numpy()).all()
        for col in ("own_r", "opp_r", "own_rf_es", "opp_ra_es"):
            rows[f"{col}_{cn}"] = te[col].to_numpy()
    rows.to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    arm, s, chk, _ = _fit_one((fold, "B2x", threads))
    (out / "b2x_stratum_check.json").write_text(json.dumps(chk, indent=1))
    print(now(), "B2x in-sample stratum check", [(r["grp"], round(r["diff_pp"], 3)) for r in chk], flush=True)
    bad = [r for r in chk if r["gated"] and abs(r["diff_pp"]) > 0.2]
    if bad:
        raise SystemExit(f"B2x in-sample stratum check FAILED: {bad}; stopping (spec)")
    infos = {}
    with ProcessPoolExecutor(procs) as ex:
        for arm, s, _, info in ex.map(_fit_one, [(fold, a_, threads) for a_ in ARMS if a_ != "B2x"]):
            infos[arm] = info
            print(now(), f"fold {fold} {arm} done ({s}s) {info}", flush=True)
    (out / "coef_info.json").write_text(json.dumps(infos, indent=1))
    (out / "labels_sealed.json").write_text(json.dumps({a_: label(a_) for a_ in ARMS}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["select", "fold2", "fold1"])
    ap.add_argument("--procs", type=int, default=5)
    ap.add_argument("--threads", type=int, default=1)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"select": cmd_select, "fold2": lambda a: fit_all(2, a.threads, a.procs),
     "fold1": lambda a: fit_all(1, a.threads, a.procs)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
