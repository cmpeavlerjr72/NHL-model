"""EG-R1 part A step 2 (Lane H8a, INV-66): fit P0 / P1 on a fold's training seasons, then grade both arms blind on the
fold's test season (per-team-game LL, the offline bias checks). Fold 1 = D13 guard, fold 2 = selection.

    train_end_game_pull_v1.py fit   --fold 1|2      -> data/processed/end_game/models_v1/fold{f}_{P0,P1}.json
    train_end_game_pull_v1.py grade --fold 1|2      -> results/end_game_pull_v1/grade_fold{f}.json (+ md section)
    train_end_game_pull_v1.py select                -> applies the spec rule to the fold-2 grade (after both grades)
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from nhl_sim.end_game import pull as PL  # noqa: E402

DATA = ROOT / "data" / "processed" / "end_game"
MOD = DATA / "models_v1"
RES = ROOT / "results" / "end_game_pull_v1"
FOLDS = {1: ([20212022, 20222023], 20232024), 2: ([20212022, 20222023, 20232024], 20242025)}
SALT = "eg-r1-a-h8a"


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def load(kind, seasons):
    return pd.concat([pd.read_parquet(DATA / f"pull_{kind}_v1_{s}.parquet") for s in seasons], ignore_index=True)


def cmd_fit(a):
    tr, _ = FOLDS[a.fold]
    rows = load("rows", tr)
    MOD.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    p1 = PL.fit_p1(rows)
    p0 = PL.fit_p0(rows)
    for m in (p0, p1):
        m.update(fold=a.fold, train=tr, fitted=now())
        (MOD / f"fold{a.fold}_{m['arm']}.json").write_text(json.dumps(m))
    w = np.asarray(p1["coef"])
    print(now(), f"fold {a.fold}: P1 {p1['n_iter']} iters, pk {w[-4]:+.3f} pp {w[-3]:+.3f} pulled_before {w[-2]:+.3f} "
          f"home {w[-1]:+.3f}; rows {p1['n_rows']:,}, pulls {p1['n_pulls']:,}; {time.time() - t0:.0f}s", flush=True)


def blind(arm):
    return "arm_" + hashlib.sha256((SALT + arm).encode()).hexdigest()[:6]


def cmd_grade(a):
    tr, te = FOLDS[a.fold]
    rows, paths, ep = load("rows", [te]), load("paths", [te]), load("episodes", [te])
    arms = {nm: json.loads((MOD / f"fold{a.fold}_{nm}.json").read_text()) for nm in ("P0", "P1")}
    RES.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    act = PL.actual_stats(paths, ep)
    out = dict(fold=a.fold, train=tr, test=te, n_rows=int(len(rows)), n_pulls=int(rows.y.sum()), n_team_games=int(len(paths)),
               actual=act, arms={})
    ll = {}
    for nm, m in arms.items():
        ll[nm] = PL.team_game_ll(m, rows)
        sim = PL.simulate_offline(m, paths, reps=a.reps, seed=a.fold)
        b = blind(nm)
        by = {}
        for d in range(3):
            k = rows.dcat.to_numpy() == d
            by[f"dcat{d}"] = float(PL.team_game_ll(m, rows[k]).sum())
        out["arms"][b] = dict(ll_sum=float(ll[nm].sum()), ll_per_team_game=float(ll[nm].mean()), sim=sim,
                              checks=PL.bias_checks(sim, act), ll_by_deficit=by)
        print(now(), b, f"LL/tg {ll[nm].mean():.5f}", json.dumps(sim), flush=True)
    j = ll["P1"].index.union(ll["P0"].index)
    d = (ll["P1"].reindex(j, fill_value=0) - ll["P0"].reindex(j, fill_value=0))
    out["paired"] = dict(first=blind("P1"), second=blind("P0"), mean_diff=float(d.mean()), se=float(d.std(ddof=1) / np.sqrt(len(d))),
                         n_team_games=int(len(d)))
    out["paired"]["z"] = out["paired"]["mean_diff"] / out["paired"]["se"]
    out["noise_floor"] = "0 (P1 is a deterministic logistic; a second-seed refit is identical by construction)"
    out["seconds"] = round(time.time() - t0, 1)
    (RES / f"grade_fold{a.fold}.json").write_text(json.dumps(out, indent=1))
    print(now(), "wrote", RES / f"grade_fold{a.fold}.json", flush=True)


def cmd_select(a):
    g2 = json.loads((RES / "grade_fold2.json").read_text())
    g1 = json.loads((RES / "grade_fold1.json").read_text())
    lab = {blind(n): n for n in ("P0", "P1")}
    p1, p0 = blind("P1"), blind("P0")
    pr = g2["paired"]
    ll_ok = pr["mean_diff"] > 2 * pr["se"]
    c1, c0 = g2["arms"][p1]["checks"]["all"], g2["arms"][p0]["checks"]["all"]
    d13 = {lab[k]: v["checks"]["all"] for k, v in g1["arms"].items()}
    if ll_ok and c1:
        sel = "P1"
    elif c0:
        sel = "P0"
    else:
        sel = None
    res = dict(labels=lab, p1_minus_p0=pr, p1_ll_better_2se=bool(ll_ok), p1_checks=c1, p0_checks=c0, d13_fold1=d13, selected=sel,
               rule="P1 if LL better by > 2 SE and every bias check passes; otherwise P0 if its checks pass")
    (RES / "select.json").write_text(json.dumps(res, indent=1))
    (MOD / "select.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fit", "grade", "select"])
    ap.add_argument("--fold", type=int, default=2)
    ap.add_argument("--reps", type=int, default=200)
    a = ap.parse_args()
    print(now(), "start", a.cmd, a.fold, flush=True)
    {"fit": cmd_fit, "grade": cmd_grade, "select": cmd_select}[a.cmd](a)
