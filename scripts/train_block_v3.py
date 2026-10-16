"""SB-R3 trainer, step 1 (docs/models/block/experiments.md SB-R3, D29): response-side arms on the B1 structure.

  B0    level only (as SB-R1)
  B1    as SB-R1 (reference): refit coefficients on own_r / opp_r
  B1p   B1 without the two rating columns; the ratings enter as a fixed offset beta_own * own_r + beta_opp * opp_r, with
        beta = time-forward persistence (slope of realised blocks in games t+1..t+20 on the as-of rating at t, B0 offset,
        the fold's training seasons only; results/block_sb_r3/persistence.json from step 0). Not refit.
  B1m   B1 + own_r x log(1 + own exposure) + opp_r x log(1 + opp exposure) (exposure = the team's games already played
        this season), refit
  B2p   LightGBM on the B1 features minus the ratings + clock + period; init_score = logit(B0) + B1p's rating offset;
        booster parameters frozen from SB-R1 (7 leaves, min_data 200, 310 rounds). B2ps2 = seed-2 retrain (floor).
Level M1_K500, ratings b 1000 / w 0.7 (ratings_v1). B2p in-sample stratum check (vs B0, +/-0.2 pp) runs first.

    train_block_v3.py fold2|fold1  -> results/block_sb_r3[/fold1], hash-labelled predictions, labels_sealed.json
"""
import argparse
import hashlib
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
from nhl_sim.block import response as R  # noqa: E402

RES = Path("results/block_sb_r3")
FROZEN1 = Path("docs/models/block/sb_r1_frozen_params.json")
PERS = RES / "persistence.json"
SALT = "SB-R3-2026-10-16"
F = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
W_, B_ = 0.7, 1000
LEVEL = "M1_K500"
ARMS = ("B0", "B1", "B1p", "B1m", "B2p", "B2ps2")
I_OWN, I_OPP = 19, 20                      # own_r / opp_r columns in design_b1
LGB_P = [c for c in BM.LGB_FEATURES if c not in ("own_r", "opp_r")]
KEEP = ["game_id", "season", "game_type", "date", "t", "team", "team_id", "opp_id", "is_home", "st", "grp", "sc", "period",
        "ptype", "y", "rebound", "rush", "own_r", "opp_r", "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp", "arena",
        "arena_f", "clock", "n_prior", "n_prior_opp", "off"]
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def frames(fold):
    if fold not in _CACHE:
        tr_s, te_s = F[fold]
        a = D.load_attempts(tr_s + [te_s])
        games = pd.read_parquet(D.OUT / "games_v1.parquet")
        r = D.assemble(a, games, pd.read_parquet(D.OUT / "ratings_v1.parquet"), pd.read_parquet(D.OUT / "arena_v1.parquet"),
                       W_, B_)
        ex = R.exposure(games)
        r = r.merge(ex, on=["game_id", "team_id"], how="left", validate="many_to_one")
        r = r.merge(ex.rename(columns={"team_id": "opp_id", "n_prior": "n_prior_opp"}), on=["game_id", "opp_id"],
                    how="left", validate="many_to_one")
        if r[["n_prior", "n_prior_opp"]].isna().any().any():
            raise ValueError("missing exposure")
        tr = r[r.season.isin(tr_s)].reset_index(drop=True)
        te = r[r.season == te_s].reset_index(drop=True)
        L = pd.read_parquet(D.OUT / "level_v1.parquet")
        L = L[L.construction == LEVEL]
        s_train = D.share_table(tr)
        _CACHE[fold] = (tr, te, D.row_offset(tr, L, s_train), D.row_offset(te, L, s_train))
    return _CACHE[fold]


def beta(fold):
    p = json.loads(PERS.read_text())[str(fold)]
    return p["own"]["coef"], p["opp"]["coef"]


def rating_offset(r, fold):
    bo, bp = beta(fold)
    return bo * r.own_r.to_numpy(float) + bp * r.opp_r.to_numpy(float)


def design_b1p(r):
    X = BM.design_b1(r)
    return np.delete(X, [I_OWN, I_OPP], axis=1)


def design_b1m(r):
    X = BM.design_b1(r)
    return np.hstack([X, (r.own_r * np.log1p(r.n_prior)).to_numpy(float)[:, None],
                      (r.opp_r * np.log1p(r.n_prior_opp)).to_numpy(float)[:, None]])


def lgb_ds(r, init, ref=None):
    import lightgbm as lgb
    return lgb.Dataset(r[LGB_P].astype(float), label=r.y.to_numpy(), categorical_feature=["grp"], free_raw_data=False,
                       reference=ref, init_score=init)


def _fit_one(args):
    fold, arm, threads = args
    tr, te, otr, ote = frames(fold)
    out = RES if fold == 2 else RES / "fold1"
    t1 = time.time()
    chk, info = None, {}
    if arm == "B0":
        m = BM.fit_b0(tr, otr)
        p = BM.predict_b0(m, te, ote)
    elif arm == "B1":
        m = BM.fit_b1(tr, otr)
        p = BM.predict_b1(m, te, ote)
        info = dict(coef_own=m["coef"][I_OWN], coef_opp=m["coef"][I_OPP])
    elif arm == "B1p":
        o_tr, o_te = otr + rating_offset(tr, fold), ote + rating_offset(te, fold)
        w, nit = BM.fit_logit_offset(design_b1p(tr), tr.y.to_numpy(), o_tr)
        m = dict(arm="B1p", coef=w.tolist(), beta=beta(fold), n_iter=nit)
        p = BM.sigmoid(design_b1p(te) @ w + o_te)
        info = dict(beta_own=beta(fold)[0], beta_opp=beta(fold)[1], coef_arena=float(w[-1]))
    elif arm == "B1m":
        w, nit = BM.fit_logit_offset(design_b1m(tr), tr.y.to_numpy(), otr)
        m = dict(arm="B1m", coef=w.tolist(), n_iter=nit)
        p = BM.sigmoid(design_b1m(te) @ w + ote)
        info = dict(coef_own=w[I_OWN], coef_opp=w[I_OPP], coef_own_x_logexp=w[-2], coef_opp_x_logexp=w[-1])
    else:
        import lightgbm as lgb
        L = json.loads(FROZEN1.read_text())["lgb"]
        seed = 1 if arm == "B2p" else 2
        m0 = BM.fit_b0(tr, otr)
        p0tr = BM.predict_b0(m0, tr, otr)
        init = BM.logit(p0tr) + rating_offset(tr, fold)
        bst = lgb.train(BM.lgb_params(L["num_leaves"], L["min_data_in_leaf"], seed, threads), lgb_ds(tr, init),
                        num_boost_round=L["n_rounds"])
        bst.save_model(str(out / "models" / f"{arm}.txt"))
        ptr = BM.sigmoid(bst.predict(tr[LGB_P].astype(float), raw_score=True) + init)
        chk = []
        for g in range(5):
            mk = (tr.grp == g).to_numpy()
            chk.append(dict(grp=g, n=int(mk.sum()), diff_pp=100 * (ptr[mk].mean() - p0tr[mk].mean()), gated=g <= 2))
        init_te = BM.logit(BM.predict_b0(m0, te, ote)) + rating_offset(te, fold)
        p = BM.sigmoid(bst.predict(te[LGB_P].astype(float), raw_score=True) + init_te)
        m = None
    if m is not None:
        (out / "models" / f"{arm}.json").write_text(json.dumps(m, default=float))
    p = p.astype(np.float64)
    if p.shape != (len(te),) or not np.isfinite(p).all():
        raise ValueError(f"{arm}: bad probabilities")
    np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p.astype(np.float32))
    return arm, round(time.time() - t1), chk, {k: float(v) for k, v in info.items()}


def fit_all(fold, threads, procs):
    out = RES if fold == 2 else RES / "fold1"
    (out / "models").mkdir(parents=True, exist_ok=True)
    tr, te, otr, ote = frames(fold)
    te.assign(off=ote)[KEEP].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    arm, s, chk, _ = _fit_one((fold, "B2p", threads))
    (out / "b2p_stratum_check.json").write_text(json.dumps(chk, indent=1))
    print(now(), "B2p in-sample stratum check", [(r["grp"], round(r["diff_pp"], 3)) for r in chk], flush=True)
    bad = [r for r in chk if r["gated"] and abs(r["diff_pp"]) > 0.2]
    if bad:
        raise SystemExit(f"B2p in-sample stratum check FAILED: {bad}; stopping (spec)")
    infos = {}
    with ProcessPoolExecutor(procs) as ex:
        for arm, s, _, info in ex.map(_fit_one, [(fold, a_, threads) for a_ in ARMS if a_ != "B2p"]):
            infos[arm] = info
            print(now(), f"fold {fold} {arm} done ({s}s) {info}", flush=True)
    (out / "coef_info.json").write_text(json.dumps(infos, indent=1))
    (out / "labels_sealed.json").write_text(json.dumps({a_: label(a_) for a_ in ARMS}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fold2", "fold1"])
    ap.add_argument("--procs", type=int, default=3)
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    fit_all(2 if a.cmd == "fold2" else 1, a.threads, a.procs)
    print(now(), "done", a.cmd, flush=True)
