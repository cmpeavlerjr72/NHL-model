"""SA-R1 (INV-30) trainer: shot-attempt hazard arms A0-A5 (docs/models/shot_attempt/experiments.md SA-R1).

  tune    fold 1 only (train 2021-22 + 2022-23, test 2023-24):
          (1) k x (w, prior strength) grid on A1 (36 cells): fold-1 test LL per game, plus the fold-1 offline
              quintile-spread ratio (5v5, own ES-for and opponent ES-against rating quintiles) for EVERY cell (L24);
              the pair (and k) maximising fold-1 LL is frozen;
          (2) builds the arena table at the frozen (w, b) (build_shot_attempt_tables.py arena);
          (3) the A3 LightGBM grid (num_leaves {7, 15} x min_data_in_leaf {200, 800}, lr 0.05) with early stopping on
              the time-ordered inner split (last 20% of fold-1 training games by date);
          (4) the A4 latent variance: A2 fitted on fold-1 train, gamma variance maximising the fold-1-train marginal.
          Writes docs/models/shot_attempt/sa_r1_frozen_params.json.
  fold2   frozen params; fits A0, A1, A2, A5, A3 (+ A3 seed 2) on train through 2023-24; A4 = A2 mean + latent;
          writes hash-labelled 2024-25 predictions to results/shot_attempt_r1 (graded blind by grade_shot_attempt.py).
  fold1   diagnostic: the same arms on fold-1 train, fold-1 test predictions for the bias checks.
"""
import argparse
import hashlib
import itertools
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.shot_attempt import models as S  # noqa: E402

RES = Path("results/shot_attempt_r1")
FROZEN = Path("docs/models/shot_attempt/sa_r1_frozen_params.json")
SALT = "SA-R1-2026-10-15"
GRID_K = (15, 50, 150)
GRID_W = (0.5, 0.7, 0.85, 1.0)
GRID_B = (600, 1800, 5400)
GRID_NL, GRID_MD = (7, 15), (200, 800)
SEED1, SEED2 = 1, 2
F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024
F2_TRAIN, F2_TEST = [20212022, 20222023, 20232024], 20242025
KEEP = ["game_id", "season", "game_type", "team", "team_id", "opp_id", "is_home", "t0", "exposure_s", "y", "y_goal",
        "st", "sc", "period", "ptype", "last5", "own_r", "opp_r", "own_rf_es", "opp_ra_es", "b2b_own", "b2b_opp",
        "arena_f", "level"]
ARMS = ("A0", "A1", "A2", "A5", "A4", "A3")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def spread_ratio(te, mu):
    """Fold offline quintile-spread ratio within 5v5: (pred Q5 - Q1 per 60) / (actual Q5 - Q1), team-game quintiles
    of the own ES-for rating and of the opponent ES-against rating."""
    import pandas as pd
    m = te.st.to_numpy() == 0
    d = pd.DataFrame({"g": te.game_id.to_numpy()[m], "t": te.team.to_numpy()[m], "own": te.own_rf_es.to_numpy()[m],
                      "opp": te.opp_ra_es.to_numpy()[m], "mu": mu[m], "y": te.y.to_numpy()[m],
                      "e": te.exposure_s.to_numpy()[m]})
    tg = d.groupby(["g", "t"]).agg(own=("own", "first"), opp=("opp", "first"), mu=("mu", "sum"), y=("y", "sum"),
                                   e=("e", "sum"))
    out = {}
    for c in ("own", "opp"):
        q = pd.qcut(tg[c].rank(method="first"), 5, labels=False)
        a = tg.groupby(q).agg(mu=("mu", "sum"), y=("y", "sum"), e=("e", "sum"))
        p60, a60 = a.mu / a.e * 3600, a.y / a.e * 3600
        out[c] = float((p60.iloc[-1] - p60.iloc[0]) / (a60.iloc[-1] - a60.iloc[0]))
    return out


def frames(train, test, k, fold, w, b, arena=True):
    rows = S.load_rows(train + [test])
    r = S.attach_features(rows, w, b, k, fold, arena=arena)
    return r[r.season.isin(train)].reset_index(drop=True), r[r.season == test].reset_index(drop=True)


def tune():
    t0 = time.time()
    out = {"tuned_on": "fold 1 only: train 2021-22 + 2022-23, test 2023-24 (fold-1 profile)", "grid_A1": [],
           "lgb_grid": []}
    rows = S.load_rows(F1_TRAIN + [F1_TEST])
    best = None
    for k, w, b in itertools.product(GRID_K, GRID_W, GRID_B):
        r = S.attach_features(rows, w, b, k, 1, arena=False)
        tr, te = r[r.season.isin(F1_TRAIN)], r[r.season == F1_TEST]
        m = S.fit_glm(tr, "A1")
        mu = S.predict_glm(m, te)
        ll = float(S.per_game_ll(te, mu).mean())
        sr = spread_ratio(te, mu)
        out["grid_A1"].append({"k": k, "w": w, "b": b, "fold1_A1_ll_per_game": ll, "spread_ratio_own_es": sr["own"],
                               "spread_ratio_opp_es": sr["opp"], "beta_own_r": m["beta"][0], "beta_opp_r": m["beta"][1],
                               "pred_over_actual": float(mu.sum() / te.y.sum())})
        print(now(), f"k={k} w={w} b={b} A1 fold1 LL/game {ll:.5f} spread own {sr['own']:.3f} opp {sr['opp']:.3f}",
              flush=True)
        if best is None or ll > best[0]:
            best = (ll, k, w, b)
    _, k, w, b = best
    out.update(k=k, w=w, prior_strength_min=b)
    FROZEN.write_text(json.dumps(out, indent=1))
    print(now(), f"frozen k={k} w={w} b={b}; building arena table", flush=True)
    subprocess.run([sys.executable, "scripts/build_shot_attempt_tables.py", "arena", "--w", str(w), "--b", str(b)],
                   check=True)
    tr, te = frames(F1_TRAIN, F1_TEST, k, 1, w, b)
    import lightgbm as lgb
    from nhl_sim.strength_state import models as HM
    gd = load_games(F1_TRAIN, columns=["game_id", "game_date_local"]).sort_values(["game_date_local", "game_id"])
    cut = gd.game_id.iloc[int(len(gd) * 0.8):]
    inner_va = tr.game_id.isin(cut).to_numpy()
    bestl = None
    for nl, md in itertools.product(GRID_NL, GRID_MD):
        t1 = time.time()
        bst = lgb.train(HM.lgb_params(nl, md, SEED1), S.lgb_dataset(tr[~inner_va]), num_boost_round=3000,
                        valid_sets=[S.lgb_dataset(tr[inner_va])], callbacks=[lgb.early_stopping(50, verbose=False)])
        it = int(bst.best_iteration)
        full = S.fit_lgb(tr, nl, md, it, SEED1)
        ll = float(S.per_game_ll(te, S.predict_lgb(full, te)).mean())
        out["lgb_grid"].append({"num_leaves": nl, "min_data_in_leaf": md, "best_iter_inner": it,
                                "fold1_A3_ll_per_game": ll})
        print(now(), f"nl={nl} md={md} iters={it} A3 fold1 LL/game {ll:.5f} ({time.time() - t1:.0f}s)", flush=True)
        if bestl is None or ll > bestl[0]:
            bestl = (ll, nl, md, it)
    _, nl, md, it = bestl
    out["lgb"] = {"num_leaves": nl, "min_data_in_leaf": md, "learning_rate": 0.05, "n_rounds": it,
                  "inner_split": "last 20% of fold-1 training games by date"}
    m2 = S.fit_glm(tr, "A2")
    out["latent"] = {**S.fit_latent_v(tr, S.predict_glm(m2, tr)),
                     "fitted_on": "fold-1 train, A2 in-sample mean (A2 coefficients from the Poisson fit)"}
    out["elapsed_s"] = time.time() - t0
    FROZEN.write_text(json.dumps(out, indent=1))
    print(now(), "frozen", json.dumps({x: out[x] for x in ("k", "w", "prior_strength_min", "lgb", "latent")}),
          flush=True)


def fit_all(tr, te, fz, outdir, blind):
    (outdir / "models").mkdir(parents=True, exist_ok=True)
    preds, meta = {}, {}
    for arm in S.ARMS_GLM:
        m = S.fit_glm(tr, arm)
        (outdir / "models" / f"{arm}.json").write_text(json.dumps(m))
        preds[arm] = S.predict_glm(m, te)
        meta[arm] = {"latent_v": 0.0}
        print(now(), arm, "fit", flush=True)
    preds["A4"] = preds["A2"].copy()
    meta["A4"] = {"latent_v": fz["latent"]["latent_v"]}
    L = fz["lgb"]
    for arm, seed in (("A3", SEED1), ("A3s2", SEED2)):
        if not blind and arm == "A3s2":
            continue
        t1 = time.time()
        bst = S.fit_lgb(tr, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], seed)
        bst.save_model(str(outdir / "models" / f"{arm}.txt"))
        preds[arm] = S.predict_lgb(bst, te)
        meta[arm] = {"latent_v": 0.0}
        print(now(), arm, f"fit ({time.time() - t1:.0f}s)", flush=True)
    return preds, meta


def fold2():
    t0 = time.time()
    fz = json.loads(FROZEN.read_text())
    tr, te = frames(F2_TRAIN, F2_TEST, fz["k"], 2, fz["w"], fz["prior_strength_min"])
    RES.mkdir(parents=True, exist_ok=True)
    te[KEEP].to_parquet(RES / "fold2_rows.parquet", index=False)
    preds, meta = fit_all(tr, te, fz, RES, True)
    labels = {}
    for arm, mu in preds.items():
        h = label(arm)
        labels[arm] = h
        np.save(RES / f"fold2_haz_{h}.npy", mu)
        (RES / f"fold2_meta_{h}.json").write_text(json.dumps(meta[arm]))
    (RES / "labels_sealed.json").write_text(json.dumps(labels))
    print(now(), f"fold2 done ({time.time() - t0:.0f}s); rows test {len(te)}", flush=True)


def fold1():
    t0 = time.time()
    fz = json.loads(FROZEN.read_text())
    d = RES / "fold1"
    d.mkdir(parents=True, exist_ok=True)
    tr, te = frames(F1_TRAIN, F1_TEST, fz["k"], 1, fz["w"], fz["prior_strength_min"])
    te[KEEP].to_parquet(d / "rows.parquet", index=False)
    preds, meta = fit_all(tr, te, fz, d, False)
    for arm, mu in preds.items():
        np.save(d / f"pred_{arm}.npy", mu)
    (d / "meta.json").write_text(json.dumps(meta))
    print(now(), f"fold1 done ({time.time() - t0:.0f}s)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "fold2", "fold1"])
    a = ap.parse_args()
    {"tune": tune, "fold2": fold2, "fold1": fold1}[a.stage]()
