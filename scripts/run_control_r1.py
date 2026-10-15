"""Control R1 (INV-6) runner. Stages:
  tune   fold 1 only: grid lambda x w on A0, kappa on A1, lambda3 / phi fit on fold-1 train; writes the frozen params.
  fold2  loads frozen params, runs A0-A4 on 2024-25, writes hashed-label prediction files for grade_control.py.
  sim    samples N seeds per game for one arm on fold 2 into results/<tag>/ (schema docs/ops/sim_output_schema.md).
"""
import argparse
import hashlib
import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.control import engine as E  # noqa: E402

RES = Path("results/control_r1")
FROZEN = Path("docs/models/control/r1_frozen_params.json")
SALT = "R1-2026-10-15"
ARMS = ["A0", "A1", "A2", "A3", "A4"]
DESIGN = {"A0": "base", "A1": "gk", "A2": "gk", "A3": "gk", "A4": "gkrest"}
GRID_PEN_REST = [1e-3, 1, 10, 100]
GRID_LAM, GRID_W, GRID_KAPPA = [1, 3, 10, 30], [0.5, 0.7, 0.9], [250, 500, 1000, 2000]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def season_games(d, s):
    return d.g[d.g.season == s].reset_index(drop=True)


def a0_score(d, lam, w, s):
    ch = E.Chain(d, "base", lam, w)
    p = ch.asof(s)
    gs = season_games(d, s)
    reg = E.reg_pmf("A0", p.lam_h.values, p.lam_a.values, {})
    F, _ = E.final_pmf(reg, gs.q_ot.values, gs.p_home_tie.values)
    return float(E.logscore(F, gs.hg.values, gs.ag.values).mean())


def tune():
    t0 = time.time()
    d = E.build_data()
    out = {"tuned_on": "fold 1 (test 2023-24) only; dispersion fits on fold-1 train (2022-23 as-of)", "grid_lambda_w": []}
    best = None
    for lam, w in itertools.product(GRID_LAM, GRID_W):
        t1 = time.time()
        sc = a0_score(d, lam, w, 20232024)
        out["grid_lambda_w"].append({"lambda": lam, "w": w, "fold1_A0_logscore": sc})
        print(now(), f"lam={lam} w={w} A0 fold1 logscore {sc:.5f} ({time.time()-t1:.1f}s)", flush=True)
        if best is None or sc > best[0]:
            best = (sc, lam, w)
    _, lam, w = best
    out["lambda"], out["w"] = lam, w
    gs = season_games(d, 20232024)
    best_k = None
    out["grid_kappa"] = []
    for kappa in GRID_KAPPA:
        ch = E.Chain(d, "gk", lam, w, kappa)
        p = ch.asof(20232024)
        reg = E.reg_pmf("A1", p.lam_h.values, p.lam_a.values, {})
        F, _ = E.final_pmf(reg, gs.q_ot.values, gs.p_home_tie.values)
        sc = float(E.logscore(F, gs.hg.values, gs.ag.values).mean())
        out["grid_kappa"].append({"kappa": kappa, "fold1_A1_logscore": sc})
        print(now(), f"kappa={kappa} A1 fold1 logscore {sc:.5f}", flush=True)
        if best_k is None or sc > best_k[0]:
            best_k = (sc, kappa)
    kappa = best_k[1]
    out["kappa"] = kappa
    # A4 stability (found at the first fold-2 run: spec-literal near-unpenalised rest terms gave lambda=2e4 on game 4 of
    # 2024-25). Ridge on the rest terms only is chosen HERE on fold 1; literal value reported alongside.
    out['grid_pen_rest'] = []
    best_r = None
    for pr in GRID_PEN_REST:
        p = E.Chain(d, 'gkrest', lam, w, kappa, pr).asof(20232024)
        reg = E.reg_pmf('A3', p.lam_h.values, p.lam_a.values, {'phi': 1e-4})
        F, _ = E.final_pmf(reg, gs.q_ot.values, gs.p_home_tie.values)
        sc = float(np.nanmean(E.logscore(F, gs.hg.values, gs.ag.values)))
        mx = float(max(p.lam_h.max(), p.lam_a.max()))
        out['grid_pen_rest'].append({'pen_rest': pr, 'fold1_A4_logscore_phi0': sc, 'max_lambda': mx})
        print(now(), f'pen_rest={pr} A4 fold1 logscore {sc:.5f} max lambda {mx:.2f}', flush=True)
        if np.isfinite(sc) and mx < 12 and (best_r is None or sc > best_r[0]):
            best_r = (sc, pr)
    out['pen_rest'] = best_r[1]
    tr = season_games(d, 20222023)
    for key, design in (("gk", "gk"), ("gkrest", "gkrest")):
        p = E.Chain(d, design, lam, w, kappa, out['pen_rest'] if design == 'gkrest' else 1e-3).asof(20222023)
        rates = (p.lam_h.values, p.lam_a.values)
        if key == "gk":
            out["lambda3"] = E.fit_lambda3(rates, tr.reg_h.values, tr.reg_a.values)
            out["phi_A3"] = E.fit_phi(rates, tr.reg_h.values, tr.reg_a.values)
        else:
            out["phi_A4"] = E.fit_phi(rates, tr.reg_h.values, tr.reg_a.values)
    FROZEN.parent.mkdir(parents=True, exist_ok=True)
    FROZEN.write_text(json.dumps(out, indent=1))
    print(now(), "frozen:", {k: v for k, v in out.items() if not k.startswith("grid")}, f"({time.time()-t0:.0f}s)")


def fold2():
    fz = json.loads(FROZEN.read_text())
    lam, w, kappa = fz["lambda"], fz["w"], fz["kappa"]
    s = 20242025
    d = E.build_data()
    gs = season_games(d, s)
    RES.mkdir(parents=True, exist_ok=True)
    rates = {}
    for design in ("base", "gk", "gkrest"):
        rates[design] = E.Chain(d, design, lam, w, kappa, fz['pen_rest'] if design == 'gkrest' else 1e-3).asof(s)
    labels = {}
    for arm in ARMS:
        p = rates[DESIGN[arm]]
        par = {"lambda3": fz["lambda3"], "phi": fz["phi_A3"] if arm == "A3" else fz.get("phi_A4")}
        reg = E.reg_pmf(arm, p.lam_h.values, p.lam_a.values, par)
        F, pw = E.final_pmf(reg, gs.q_ot.values, gs.p_home_tie.values)
        lab = label(arm)
        labels[arm] = lab
        np.savez_compressed(RES / f"fold2_{lab}.npz", final=F.astype(np.float32), pwin=pw, lam_h=p.lam_h.values,
                            lam_a=p.lam_a.values, net_h=p.net_h.values, net_a=p.net_a.values,
                            reg_tie=reg[:, np.arange(E.NR), np.arange(E.NR)].sum(1),
                            uses_goalie=np.array(arm != "A0"))
        print(now(), "wrote", lab, flush=True)
    gs.assign(z_h=(gs.lg_sv - gs.a_sv / gs.a_sa.clip(lower=1)) * 100).to_parquet(RES / "fold2_games.parquet")
    (RES / "labels_sealed.json").write_text(json.dumps(labels))


def sim(arm, n_seeds=1000):
    fz = json.loads(FROZEN.read_text())
    lam, w, kappa = fz["lambda"], fz["w"], fz["kappa"]
    s = 20242025
    d = E.build_data()
    gs = season_games(d, s)
    p = E.Chain(d, DESIGN[arm], lam, w, kappa, fz['pen_rest'] if DESIGN[arm] == 'gkrest' else 1e-3).asof(s)
    par = {"lambda3": fz["lambda3"], "phi": fz["phi_A3"] if arm == "A3" else fz.get("phi_A4")}
    tag = f"control_r1_{arm}_fold2"
    parts = []
    for off in range(1):
        h, a, es, hw = E.sample_final(arm, p.lam_h.values, p.lam_a.values, gs.q_ot.values, gs.p_home_tie.values, par,
                                      n_seeds, seed=20261015 + off)
        G = len(gs)
        parts.append(pd.DataFrame({"game_id": np.repeat(gs.game_id.values, n_seeds), "seed": np.tile(np.arange(n_seeds, dtype="int32"), G),
                                   "home_goals": h.ravel().astype("int16"), "away_goals": a.ravel().astype("int16"),
                                   "end_state": es.ravel(), "home_win": hw.ravel()}))
    out = Path("results") / tag
    out.mkdir(parents=True, exist_ok=True)
    pd.concat(parts).to_parquet(out / "games.parquet")
    (out / "run_meta.json").write_text(json.dumps({"engine_tag": tag, "arm": arm, "fold": 2, "season": s, "n_seeds": n_seeds,
                                                  "sealed_touched": False, "oracle_goalie": arm != "A0",
                                                  "frozen_params": str(FROZEN)}))
    print(now(), "wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["tune", "fold2", "sim"])
    ap.add_argument("--arm")
    ap.add_argument("--seeds", type=int, default=1000)
    a = ap.parse_args()
    {"tune": tune, "fold2": fold2, "sim": lambda: sim(a.arm, a.seeds)}[a.stage]()
