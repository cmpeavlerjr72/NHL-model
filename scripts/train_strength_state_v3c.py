"""SS-R3c (INV-31, D16): the stage-1 incumbent re-levelled with LC-1 (docs/models/strength_state/experiments.md SS-R3c).
Everything is SS-R3 (train_strength_state_v3.py) except the level: the SS-R3 profile p (profile_v3_f<fold>) is kept and
the SS-R2-construction de-seasonalised ratio level is replaced by the LC-1 absolute level (`league_level_lc1`).

  level   build data/processed/strength_state/league_level_v4_f{1,2}.parquet (LC-1, k in {5, 15, 50}; v3 untouched)
  tune    fold 1 only: k on H1'' (w = 1.0, prior strength 1,800 as SS-R3) -> docs/models/strength_state/ss_r3c_frozen_params.json
  fold2   H0''c-H3''c (+ H3''c seed 2), SS-R3 frozen LightGBM params (7 leaves, 200 min-data, 378 rounds);
          hash-labelled predictions to results/strength_state_r3c; models as <arm>_fold2.*; T1 copied (type arm: T1,
          SS-R5 selected no type arm); LC-1 per-training-season parity on fold-2 train (reported)
  fold1   the same arms on fold 1 (diagnostic) + the LC-1 per-training-season parity on fold-1 train
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import PROCESSED, load_games  # noqa: E402
from nhl_sim.league_level_lc1 import lc1_level, per_season_parity  # noqa: E402
from nhl_sim.strength_state import models as M  # noqa: E402
from nhl_sim.strength_state import models_r2 as R  # noqa: E402
from nhl_sim.strength_state.seasonality import game_bins  # noqa: E402
from nhl_sim.strength_state.tables import assert_pregame  # noqa: E402

SS = PROCESSED / "strength_state"
RES = Path("results/strength_state_r3c")
R1 = Path("results/strength_state_r1")
FROZEN = Path("docs/models/strength_state/ss_r3c_frozen_params.json")
FROZEN_R3 = Path("docs/models/strength_state/ss_r3_frozen_params.json")
SALT = "SS-R3c-2026-10-15"
KS = (5, 15, 50)
W, B = 1.0, 1800
SEED1, SEED2 = 1, 2
F1_TRAIN, F1_TEST = [20212022, 20222023], 20232024
F2_TRAIN, F2_TEST = [20212022, 20222023, 20232024], 20242025
KEEP = ["game_id", "season", "game_type", "team", "team_id", "opp_id", "is_home", "t0", "exposure_s", "y", "st",
        "sc", "pdiff", "period", "ptype", "last5", "taken_own", "drawn_opp", "b2b_own", "b2b_opp", "level"]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def build_level():
    long = pd.read_parquet(SS / "team_game_v2.parquet")
    games = load_games(sorted(long.season.unique()), columns=["game_id", "game_type", "game_date_local"])
    gbin = game_bins(long, games)
    for f in (1, 2):
        p = np.array(json.loads((SS / f"profile_v3_f{f}.json").read_text())["p"])
        lv = lc1_level(long, gbin, p, KS)
        assert_pregame(lv)
        lv.to_parquet(SS / f"league_level_v4_f{f}.parquet", index=False)
        print(now(), "fold", f, {int(s): round(float(np.exp(lv[lv.season == s].level_k15).mean()), 4)
                                for s in sorted(lv.season.unique())}, flush=True)


def attach(rows, k, fold):
    """SS-R3 features (models_r2.attach_features, profile fold) with the level replaced by LC-1 + p."""
    r = R.attach_features(rows, W, B, 15, profile_fold=fold).drop(columns=["level"])
    lv = pd.read_parquet(SS / f"league_level_v4_f{fold}.parquet", columns=["game_id", f"level_k{k}", "p"])
    lv["level"] = lv[f"level_k{k}"] + lv["p"]
    r = r.merge(lv[["game_id", "level"]], on="game_id", how="left", validate="many_to_one")
    if r.level.isna().any():
        raise ValueError("missing LC-1 level")
    return r


def frames(train, test, k, fold):
    r = attach(R.load_rows(train + [test]), k, fold)
    return r[r.season.isin(train)].reset_index(drop=True), r[r.season == test].reset_index(drop=True)


def tune():
    out = {"tuned_on": "fold 1 only (train 2021-22 + 2022-23, test 2023-24), k on H1'' (SS-R3 practice)", "grid_H1": []}
    rows = R.load_rows(F1_TRAIN + [F1_TEST])
    best = None
    for k in KS:
        r = attach(rows, k, 1)
        tr, te = r[r.season.isin(F1_TRAIN)], r[r.season == F1_TEST]
        m = R.fit_glm(tr, "H1")
        mu = R.predict_glm(m, te)
        ll = float(M.per_game_ll(te, mu).mean())
        out["grid_H1"].append({"k": k, "fold1_H1_ll_per_game": ll, "pred_over_actual": float(mu.sum() / te.y.sum())})
        print(now(), f"k={k} H1''c fold1 LL/game {ll:.5f} pred/actual {mu.sum() / te.y.sum():.4f}", flush=True)
        if best is None or ll > best[0]:
            best = (ll, k)
    out.update(k=best[1], w=W, prior_strength_min=B, lgb=json.loads(FROZEN_R3.read_text())["lgb"])
    FROZEN.write_text(json.dumps(out, indent=1))
    print(now(), "frozen k", best[1], flush=True)


def fit_all(tr, te, L, outdir, blind):
    (outdir / "models").mkdir(parents=True, exist_ok=True)
    preds, models = {}, {}
    for arm in ("H0", "H1", "H2"):
        m = R.fit_glm(tr, arm)
        (outdir / "models" / f"{arm}_fold2.json").write_text(json.dumps(m))
        preds[arm], models[arm] = R.predict_glm(m, te), m
    for arm, seed in (("H3", SEED1), ("H3s2", SEED2)):
        if not blind and arm == "H3s2":
            continue
        bst = R.fit_lgb(tr, L["num_leaves"], L["min_data_in_leaf"], L["n_rounds"], seed)
        bst.save_model(str(outdir / "models" / f"{arm}_fold2.txt"))
        preds[arm], models[arm] = R.predict_lgb(bst, te), bst
    print(now(), "fits done", flush=True)
    return preds, models


def parity(tr, models):
    res = {}
    for arm in ("H0", "H1", "H2", "H3"):
        mu = R.predict_lgb(models[arm], tr) if arm == "H3" else R.predict_glm(models[arm], tr)
        t = per_season_parity(tr.season.to_numpy(), tr.y.to_numpy(float), mu)
        res[arm] = {int(s): float(v) for s, v in t.pred_over_actual_minus_1.items()}
        print(now(), "parity", arm, {s: round(v, 5) for s, v in res[arm].items()},
              "PASS" if t["pass"].all() else "FAIL", flush=True)
    return res


def fold2():
    fz = json.loads(FROZEN.read_text())
    tr, te = frames(F2_TRAIN, F2_TEST, fz["k"], 2)
    RES.mkdir(parents=True, exist_ok=True)
    te[KEEP].to_parquet(RES / "fold2_rows.parquet", index=False)
    preds, models = fit_all(tr, te, fz["lgb"], RES, True)
    labels = {}
    for arm, mu in preds.items():
        labels[arm] = label(arm)
        np.save(RES / f"fold2_haz_{labels[arm]}.npy", mu)
    (RES / "labels_sealed.json").write_text(json.dumps(labels))
    shutil.copy(R1 / "models" / "T1_fold2.json", RES / "models" / "T1_fold2.json")
    (RES / "parity_fold2_train.json").write_text(json.dumps(parity(tr, models), indent=1))
    print(now(), "fold2 done", flush=True)


def fold1():
    fz = json.loads(FROZEN.read_text())
    d = RES / "fold1"
    d.mkdir(parents=True, exist_ok=True)
    tr, te = frames(F1_TRAIN, F1_TEST, fz["k"], 1)
    te[KEEP].to_parquet(d / "rows.parquet", index=False)
    preds, models = fit_all(tr, te, fz["lgb"], d, False)
    for arm, mu in preds.items():
        np.save(d / f"pred_{arm}.npy", mu)
    (d / "parity_fold1_train.json").write_text(json.dumps(parity(tr, models), indent=1))
    print(now(), "fold1 done", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["level", "tune", "fold2", "fold1"])
    a = ap.parse_args()
    {"level": build_level, "tune": tune, "fold2": fold2, "fold1": fold1}[a.stage]()
