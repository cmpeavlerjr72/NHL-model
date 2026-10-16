"""G-R1 trainer (docs/models/goal/experiments.md G-R1).

    train_goal_v1.py select   fold 1 only: (b, w, s) selection for the goalie rating, then the team rating
                              -> results/goal_g_r1/select.json, docs/tests/goal_g_r1_select_2026-10-16.md
    train_goal_v1.py tune     fold-1 training rows only: C2 capacity grid {7, 15} x {200, 800}, lr 0.05, early stopping
                              on the time-ordered inner split (last 20% of fold-1 training games by date)
                              -> docs/models/goal/gr1_frozen_params.json
    train_goal_v1.py fold2|fold1   C0, C1, C2, C2s2 with the selected cells; C2 in-sample stratum check first (L32);
                              hash-labelled predictions for the blind grader

Selection protocol (spec reading, fixed before running; the spec says goalie and team are chosen separately but not how
the two grids are crossed):
  stage A  goalie grid (b, w) x s, with the team rating at the reference cell (b 3000, w 0.7) entering FREELY (refit).
           c_g = goalie coefficient of the free C1 fit on fold-1 training rows for that (b, w).
  stage B  team grid (b, w) x s, with the goalie rating fixed at its stage-A cell (s_g x c_g).
           c_t = team coefficient of the free C1 fit (goalie at its selected cell, free) for that (b, w).
  rule     per stage: among cells whose fold-1 test LL (gated rows, per game) is within 2 paired SE (1,000-resample
           game-block bootstrap) of the best cell, minimise |log R| (D32 decile slope ratio of that rating on gated rows);
           cells within 0.02 of the minimum are ties and go to the larger b (more shrinkage, SB-R2), then the smaller
           |log R|.
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
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402
from nhl_sim.goal import data as D  # noqa: E402
from nhl_sim.goal import models as GM  # noqa: E402

RES = Path("results/goal_g_r1")
SELECT = RES / "select.json"
FROZEN = Path("docs/models/goal/gr1_frozen_params.json")
SALT = "G-R1-2026-10-16"
S_GRID = (0.25, 0.5, 0.75, 1.0, 1.25)
GRID_G = [(b, w) for b in (1000, 3000, 10000, 30000) for w in (0.5, 0.7, 0.85)]
GRID_T = [(b, w) for b in (1000, 3000, 10000) for w in (0.5, 0.7, 0.85)]
REF_T = (3000, 0.7)
ARMS = ("C0", "C1", "C2", "C2s2")
BSEED = 20261016
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(fold):
    """(tr, te, off_tr, off_te, RG, RT): rows with C0 logit offsets; rating tables of the fold."""
    if fold not in _CACHE:
        tr_s, te_s = D.F[fold]
        sel = json.loads((RES / "step1.json").read_text())["selected"]
        rows = pd.read_parquet(RES / "rows_v1.parquet")
        r = rows[rows.season.isin(tr_s + [te_s])].reset_index(drop=True)
        T = np.load(D.OUT / f"cell_table_f{fold}.npy")
        lv = pd.read_parquet(D.OUT / f"level_v1_f{fold}.parquet")
        off = D.c0_logit(r, T, lv[lv.construction == sel])
        RG = pd.read_parquet(D.OUT / f"ratings_goalie_v1_f{fold}.parquet")
        RT = pd.read_parquet(D.OUT / f"ratings_team_v1_f{fold}.parquet")
        m = r.season.isin(tr_s).to_numpy()
        _CACHE[fold] = (r[m].reset_index(drop=True), r[~m].reset_index(drop=True), off[m], off[~m], RG, RT)
    return _CACHE[fold]


def with_ratings(r, RG, RT, gcell, tcell):
    return r.assign(g_r=D.attach_rating(r, RG.rename(columns={D.rkey(*gcell): "r"}), "goalie_id"),
                    t_r=D.attach_rating(r, RT.rename(columns={D.rkey(*tcell): "r"}), "team_id"))


def ll_rows(p, y):
    return y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))


def gated(r):
    return r.sg.isin(D.GATED_SG).to_numpy()


def R_of(p, r, col, n_boot=20):
    g = gated(r)
    x = r[g]
    s = slope_ratio(p[g], x.y.to_numpy(float), x[col].to_numpy(float), np.ones(g.sum()), x.game_id.to_numpy(),
                    n_buckets=10, n_boot=n_boot)
    return s


def ll_game(p, r):
    g = gated(r)
    games = np.sort(r.game_id.unique())
    gp = np.searchsorted(games, r.game_id.to_numpy())
    return np.bincount(gp[g], weights=ll_rows(p, r.y.to_numpy(float))[g], minlength=len(games))


# ------------------------------------------------------------------------------------------------ selection
def _free_c(args):
    stage, gcell, tcell = args
    tr, _, otr, _, RG, RT = frames(1)
    x = with_ratings(tr, RG, RT, gcell, tcell)
    m = GM.fit_free(x, otr)
    return stage, gcell, tcell, m["c_g"], m["c_t"]


def _cell(args):
    stage, gcell, tcell, spec = args
    tr, te, otr, ote, RG, RT = frames(1)
    xtr = with_ratings(tr, RG, RT, gcell, tcell)
    xte = with_ratings(te, RG, RT, gcell, tcell)
    m = GM.fit_c1(xtr, otr, spec)
    p = GM.predict_c1(m, xte, ote)
    col = "g_r" if stage == "A" else "t_r"
    s = R_of(p, xte, col)
    so = R_of(p, xte, "t_r" if stage == "A" else "g_r")
    return dict(stage=stage, g_cell=D.rkey(*gcell), t_cell=D.rkey(*tcell), b=(gcell if stage == "A" else tcell)[0],
                w=(gcell if stage == "A" else tcell)[1], s=spec["s_g"] if stage == "A" else spec["s_t"],
                c=spec["c_g"] if stage == "A" else spec["c_t"], ll_att=float(ll_rows(p, xte.y.to_numpy(float))[gated(xte)].mean()),
                ll_game=ll_game(p, xte).tolist(), R=s["R"], old_q5q1=s["old_q5q1"], R_other=so["R"])


def choose(cells, W):
    llg = np.array([c["ll_game"] for c in cells])
    G = llg.shape[1]
    best = int(np.argmax(llg.sum(1)))
    for i, c in enumerate(cells):
        d = llg[i] - llg[best]
        c["ll_game_vs_best"] = float(d.mean())
        c["se_vs_best"] = float(np.std(W @ d / G)) if i != best else 0.0
        c["in_2se"] = bool(c["ll_game_vs_best"] >= -2 * c["se_vs_best"])
        c["metric"] = float(abs(np.log(c["R"]))) if c["R"] > 0 else float("inf")
    el = [c for c in cells if c["in_2se"]]
    mn = min(c["metric"] for c in el)
    ties = [c for c in el if c["metric"] <= mn + 0.02]
    pick = sorted(ties, key=lambda c: (-c["b"], c["metric"]))[0]
    return pick, best


def cmd_select(a):
    RES.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    _, te, _, _, _, _ = frames(1)
    G = te.game_id.nunique()
    W = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=1000).astype(float)
    with ProcessPoolExecutor(a.procs) as ex:
        cA = {g: cg for _, g, _, cg, _ in ex.map(_free_c, [("A", g, REF_T) for g in GRID_G])}
        print(now(), "stage A free fits", {D.rkey(*k): round(v, 3) for k, v in cA.items()}, flush=True)
        A = list(ex.map(_cell, [("A", g, REF_T, dict(c_g=cA[g], s_g=s)) for g, s in itertools.product(GRID_G, S_GRID)]))
        pa, besta = choose(A, W)
        gsel = (pa["b"], pa["w"])
        print(now(), "stage A pick", D.rkey(*gsel), pa["s"], round(pa["R"], 3), flush=True)
        cB = {t: ct for _, _, t, _, ct in ex.map(_free_c, [("B", gsel, t) for t in GRID_T])}
        print(now(), "stage B free fits", {D.rkey(*k): round(v, 3) for k, v in cB.items()}, flush=True)
        B = list(ex.map(_cell, [("B", gsel, t, dict(c_g=cA[gsel], s_g=pa["s"], c_t=cB[t], s_t=s))
                                for t, s in itertools.product(GRID_T, S_GRID)]))
    pb, bestb = choose(B, W)
    tsel = (pb["b"], pb["w"])
    spec = dict(c_g=cA[gsel], s_g=pa["s"], c_t=cB[tsel], s_t=pb["s"])
    out = dict(goalie_cell=list(gsel), team_cell=list(tsel), spec=spec, ref_team_stage_a=list(REF_T),
               fold1_R_goalie=pb["R_other"], fold1_R_team=pb["R"], n_games=G,
               grid=[{k: v for k, v in c.items() if k != "ll_game"} for c in A + B])
    SELECT.write_text(json.dumps(out, indent=1, default=float))
    cols = ["b", "w", "s", "c", "ll_att", "ll_game_vs_best", "se_vs_best", "in_2se", "R", "old_q5q1", "R_other", "metric"]
    TA = pd.DataFrame(A)[cols]
    TB = pd.DataFrame(B)[cols]
    L = ["# G-R1 step 3: fold-1 (b, w, s) selection (Lane G, 2026-10-16)", "",
         f"Committed BEFORE any fold-2 fit. Generated {now()} ({time.time() - t0:.0f} s) by `scripts/train_goal_v1.py select`. "
         "Fold 1 = train 2021-22 + 2022-23, test 2023-24; level as step 1. Each rating enters C1 as the fixed offset s x c "
         "(c = the free-fit fold-1 coefficient for that (b, w), raw units); the other C1 features are refit.", "",
         "Protocol (spec reading, fixed before the run): stage A = goalie grid with the team rating at the reference cell "
         "(b 3000, w 0.7) entering freely; stage B = team grid with the goalie fixed at its stage-A cell. Per stage: among "
         "cells with fold-1 LL (gated rows, per game) within 2 paired SE (1,000 game-block bootstrap) of the best, minimise "
         "|log R| (D32 decile slope ratio of that rating, gated rows, point estimate); cells within 0.02 of the minimum go to "
         "the larger b, then the smaller |log R|. R_other = the other rating's R in the same fit. LL in nats per SOG; "
         "LL vs best in nats per game.", "",
         "## Stage A: goalie", "", TA.to_markdown(index=False, floatfmt=".4f"), "",
         f"- **Goalie: b {gsel[0]}, w {gsel[1]}, s {pa['s']}** (c {cA[gsel]:.4f}, R {pa['R']:.3f}); best-LL cell "
         f"b {A[besta]['b']} w {A[besta]['w']} s {A[besta]['s']}.", "",
         "## Stage B: team finishing", "", TB.to_markdown(index=False, floatfmt=".4f"), "",
         f"- **Team: b {tsel[0]}, w {tsel[1]}, s {pb['s']}** (c {cB[tsel]:.4f}, R {pb['R']:.3f}); best-LL cell "
         f"b {B[bestb]['b']} w {B[bestb]['w']} s {B[bestb]['s']}.",
         f"- Final fold-1 R at the selected pair: goalie {pb['R_other']:.3f}, team {pb['R']:.3f}. n_games {G}.", ""]
    Path("docs/tests/goal_g_r1_select_2026-10-16.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[-6:]), flush=True)


# ------------------------------------------------------------------------------------------------- booster
def init_logit(r, off, S):
    return off + GM.rating_off(r, S["spec"])


def sel_frames(fold):
    S = json.loads(SELECT.read_text())
    tr, te, otr, ote, RG, RT = frames(fold)
    g, t = tuple(S["goalie_cell"]), tuple(S["team_cell"])
    return with_ratings(tr, RG, RT, g, t), with_ratings(te, RG, RT, g, t), otr, ote, S


def cmd_tune(a):
    import lightgbm as lgb
    tr, _, otr, _, S = sel_frames(1)
    games = tr.groupby("game_id").date.first().sort_values(kind="stable")
    cut = set(games.index[int(0.8 * len(games)):])
    va = tr.game_id.isin(cut).to_numpy()
    lm = GM.lgb_mask(tr)
    init = init_logit(tr, otr, S)
    fit_m, val_m = lm & ~va, lm & va
    res = []
    for nl, md_ in itertools.product((7, 15), (200, 800)):
        dtr = lgb.Dataset(GM.lgb_X(tr[fit_m]), label=tr.y.to_numpy()[fit_m], init_score=init[fit_m],
                          categorical_feature=["sg"], free_raw_data=False)
        dva = lgb.Dataset(GM.lgb_X(tr[val_m]), label=tr.y.to_numpy()[val_m], init_score=init[val_m], reference=dtr,
                          categorical_feature=["sg"], free_raw_data=False)
        bst = lgb.train(GM.lgb_params(nl, md_, 1, a.threads), dtr, num_boost_round=3000, valid_sets=[dva],
                        callbacks=[lgb.early_stopping(50, verbose=False)])
        z = init[val_m] + bst.predict(GM.lgb_X(tr[val_m]), raw_score=True, num_iteration=bst.best_iteration)
        ll = float(ll_rows(D.sigmoid(z), tr.y.to_numpy(float)[val_m]).mean())
        ll0 = float(ll_rows(D.sigmoid(init[val_m]), tr.y.to_numpy(float)[val_m]).mean())
        res.append(dict(num_leaves=nl, min_data_in_leaf=md_, best_iter=int(bst.best_iteration), val_ll=ll, val_ll_init=ll0))
        print(now(), res[-1], flush=True)
    best = max(res, key=lambda d: d["val_ll"])
    FROZEN.write_text(json.dumps(dict(lgb=dict(num_leaves=best["num_leaves"], min_data_in_leaf=best["min_data_in_leaf"],
                                               n_rounds=max(best["best_iter"], 1), learning_rate=0.05),
                                      grid=res, inner_split="last 20% of fold-1 training games by date",
                                      generated=now()), indent=1))
    print(now(), "frozen", best, flush=True)


# ----------------------------------------------------------------------------------------------- fold fits
def cmd_fit(fold, a):
    import lightgbm as lgb
    out = RES / f"fold{fold}"
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te, otr, ote, S = sel_frames(fold)
    P = json.loads(FROZEN.read_text())["lgb"]
    y_tr = tr.y.to_numpy(float)
    preds, info = {}, {}
    # C0
    p0tr = D.sigmoid(otr)
    preds["C0"] = D.sigmoid(ote)
    # C1 (fixed-scale ratings; c from fold 1, not refit)
    m1 = GM.fit_c1(tr, otr, S["spec"])
    (out / "models" / "C1.json").write_text(json.dumps(m1, default=float))
    preds["C1"] = GM.predict_c1(m1, te, ote)
    info["C1"] = dict(coef=m1["coef"], spec=S["spec"])
    # C2 + seed 2
    init_tr, init_te = init_logit(tr, otr, S), init_logit(te, ote, S)
    lm = GM.lgb_mask(tr)
    chk = None
    for arm, seed in (("C2", 1), ("C2s2", 2)):
        ds = lgb.Dataset(GM.lgb_X(tr[lm]), label=tr.y.to_numpy()[lm], init_score=init_tr[lm], categorical_feature=["sg"],
                         free_raw_data=False)
        bst = lgb.train(GM.lgb_params(P["num_leaves"], P["min_data_in_leaf"], seed, a.threads), ds,
                        num_boost_round=P["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        if arm == "C2":
            ptr = GM.predict_c2(bst, tr, init_tr)
            chk = []
            for g in range(D.N_SG):
                mk = (tr.sg == g).to_numpy()
                chk.append(dict(sg=D.SG_NAMES[g], n=int(mk.sum()), c2_goal_pct=100 * ptr[mk].mean(),
                                c0_goal_pct=100 * p0tr[mk].mean(), act_goal_pct=100 * y_tr[mk].mean(),
                                diff_pp=100 * (ptr[mk].mean() - p0tr[mk].mean()), gated=g in D.GATED_SG))
            (out / "c2_stratum_check.json").write_text(json.dumps(chk, indent=1))
            print(now(), "C2 in-sample stratum check (C2 - C0, pp)", [(c["sg"], round(c["diff_pp"], 3)) for c in chk],
                  flush=True)
            bad = [c for c in chk if c["gated"] and abs(c["diff_pp"]) > 0.2]
            if bad:
                raise SystemExit(f"C2 in-sample stratum check FAILED: {bad}; stopping (spec, L32)")
        preds[arm] = GM.predict_c2(bst, te, init_te)
    keep = ["game_id", "season", "game_type", "date", "team_id", "opp_id", "goalie_id", "is_home", "b2b_own", "sg", "lg",
            "tier", "cell", "type6", "sc", "period", "ptype", "rebound", "rush", "y", "g_r", "t_r", "arena", "arena_f"]
    te[keep].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    for arm, p in preds.items():
        p = np.asarray(p, np.float64)
        if p.shape != (len(te),) or not np.isfinite(p).all():
            raise ValueError(f"{arm}: bad probabilities")
        np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p)
    (out / "labels_sealed.json").write_text(json.dumps({k: label(k) for k in ARMS}))
    (out / "fit_info.json").write_text(json.dumps(dict(info=info, stratum_check=chk, lgb=P), indent=1, default=float))
    print(now(), f"fold {fold} fitted; C1 coef", np.round(m1["coef"], 4).tolist(), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["select", "tune", "fold2", "fold1"])
    ap.add_argument("--procs", type=int, default=5)
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"select": cmd_select, "tune": cmd_tune, "fold2": lambda a: cmd_fit(2, a), "fold1": lambda a: cmd_fit(1, a)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
