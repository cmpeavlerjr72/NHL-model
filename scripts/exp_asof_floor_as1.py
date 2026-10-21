"""AS-1: prior-precision floor for the as-of response scale (docs/models/asof_scale/experiments.md AS-1; INV-62, D42, L38).

Instances (incumbent cells): goalie H90 P2000 (`src/nhl_sim/goal/scale.py`, G-R3 frames from train_goal_v3.py) and
stage-4 Qa H45 P10000 (`src/nhl_sim/shot_attribute/scale.py`, SL-R7 frames from train_shot_attribute_v7.py).

Rows: fold 1 = the incumbent snapshot's rows (2021-22 .. 2023-24); fold 2 = TRAINING seasons only (2021-22 .. 2023-24):
no 2024-25 row enters any computation here ("no fold-2 row is touched"). The estimator is causal, so the training-date
snapshot is the same object as the incumbent's training-date rows (checked: f = None reproduces them bit-for-bit).

    exp_asof_floor_as1.py run       f = None identity (every grid cell), I_ref, f grid on the incumbent cells, selection
                                    -> results/asof_floor_as1/as1.json, docs/tests/asof_floor_as1_2026-10-21.md
    exp_asof_floor_as1.py write     the selected f, every grid cell -> goalie_scale_v2_f{fold}, sq_scale_v2_f{fold}
                                    (versioned siblings; v1 untouched) + the SL-R7 burn-in in-sample re-statement
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import train_goal_v3 as G3  # noqa: E402
import train_shot_attribute_v7 as V7  # noqa: E402
from nhl_sim.goal import scale as GS  # noqa: E402
from nhl_sim.shot_attribute import scale as QS  # noqa: E402

RES = ROOT / "results/asof_floor_as1"
DOC = ROOT / "docs/tests/asof_floor_as1_2026-10-21.md"
F_GRID = (0.05, 0.10, 0.25, 0.50)
BURN = 20212022
JUDGED = {1: [20222023], 2: [20222023, 20232024]}
INC = {"goalie": (90, 2000), "stage4": (45, 10000)}
TEST = {1: 20232024, 2: 20242025}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


# ------------------------------------------------------------------------------------------------ instance inputs
def goalie_inputs(fold):
    r, off, spec, sd_ref, tr_s, te_s = G3.frames(fold)
    o = off + GS.team_off(r, spec)
    keep = (r.season != TEST[2]).to_numpy()            # never a 2024-25 row
    r, o = r[keep].reset_index(drop=True), np.asarray(o)[keep]
    b = (r.season == BURN).to_numpy()
    iref = GS.info_ref(r.y.to_numpy()[b], o[b], r.z.to_numpy()[b])
    season = dict(zip(pd.to_datetime(r.date).to_numpy("datetime64[D]"), r.season))
    return dict(r=r, o=o, iref=iref, sd=(sd_ref,), season=season)


def goalie_snap(I, H, P, floor=None):
    r = I["r"]
    return GS.asof_scale(r.date.to_numpy(), r["drop"].to_numpy(), r.y.to_numpy(), I["o"], r.z.to_numpy(), H, P,
                         floor=floor)


def stage4_inputs(fold):
    D = V7.fold_data(fold)
    msk, rr, A, C, zf, za, y = V7.offset_inputs(D, D["r"], D["off"])
    keep = (rr.season != TEST[2]).to_numpy()
    rr = rr[keep]
    A, C, zf, za, y = A[keep], C[keep], zf[keep], za[keep], y[keep]
    b = (rr.season == BURN).to_numpy()
    iref = QS.info_ref(A[b], C[b], zf[b], za[b])
    mom = QS.daily_moments(rr.game_date_local.to_numpy(), rr["drop"].to_numpy(), A, C, y, zf, za)
    season = dict(zip(pd.to_datetime(rr.game_date_local).to_numpy("datetime64[D]"), rr.season))
    return dict(mom=mom, iref=iref, sd=D["sd"], season=season, n=len(rr))


def stage4_snap(I, H, P, floor=None):
    return QS.asof_from_moments(I["mom"], H, P, floor=floor)


def svals(inst, f):
    return f[["s"]].to_numpy() if inst == "goalie" else f[["s_for", "s_against"]].to_numpy()


def add_season(f, season):
    f = f.copy()
    f["season"] = [season[d] for d in pd.to_datetime(f.date).to_numpy("datetime64[D]")]
    return f


def v1_path(inst, fold):
    return (G3.scale_path(fold) if inst == "goalie" else V7.snap_path(fold))


def v2_path(inst, fold):
    p = v1_path(inst, fold)
    return p.with_name(p.name.replace("_v1_", "_v2_"))


# ------------------------------------------------------------------------------------------------ run
def cmd_run(a):
    RES.mkdir(parents=True, exist_ok=True)
    out = dict(identity={}, iref={}, grid=[], clock=[])
    for inst, (inputs, snap, grid) in {"goalie": (goalie_inputs, goalie_snap, GS.GRID_ORDER),
                                       "stage4": (stage4_inputs, stage4_snap, QS.GRID_ORDER)}.items():
        for fold in (1, 2):
            t0 = time.time()
            I = inputs(fold)
            out["clock"].append(dict(step=f"{inst} f{fold} inputs", secs=round(time.time() - t0, 1)))
            iref = np.atleast_2d(I["iref"])
            out["iref"][f"{inst}_f{fold}"] = dict(I_ref=iref.tolist(), lambda_min=float(np.linalg.eigvalsh(iref)[0]),
                                                  sd_ref=list(I["sd"]))
            # ---- f = None reproduces the incumbent snapshot bit-for-bit (every grid cell, every date computed)
            V1 = pd.read_parquet(v1_path(inst, fold))
            ident = {}
            base = {}
            t1 = time.time()
            for H, P in grid:
                cell = GS.skey(H, P)
                f0 = snap(I, H, P)
                base[(H, P)] = f0
                v = V1[V1.cell == cell].reset_index(drop=True)
                v = v[pd.to_datetime(v.date).isin(pd.to_datetime(f0.date))].reset_index(drop=True)
                assert len(v) == len(f0), (inst, fold, cell, len(v), len(f0))
                eq = bool(np.array_equal(svals(inst, f0), svals(inst, v))
                          and np.array_equal(pd.to_datetime(f0.date).to_numpy(), pd.to_datetime(v.date).to_numpy())
                          and np.array_equal(f0.n_eff.to_numpy(), v.n_eff.to_numpy()))
                ident[cell] = dict(bit_identical=eq, n_dates=len(f0),
                                   max_abs=float(np.abs(svals(inst, f0) - svals(inst, v)).max()))
            out["identity"][f"{inst}_f{fold}"] = ident
            out["clock"].append(dict(step=f"{inst} f{fold} f=None grid", secs=round(time.time() - t1, 1)))
            print(now(), inst, fold, "identity", all(x["bit_identical"] for x in ident.values()), flush=True)
            # ---- f grid on the incumbent cell
            H, P = INC[inst]
            f0 = add_season(base[(H, P)], I["season"])
            sd = np.asarray(I["sd"], float)
            for f in F_GRID:
                t2 = time.time()
                ff = add_season(snap(I, H, P, floor=(f, iref if inst == "stage4" else float(iref[0, 0]))), I["season"])
                raw0, raw1 = svals(inst, f0) / sd, svals(inst, ff) / sd
                bm = (ff.season == BURN).to_numpy()
                jm = ff.season.isin(JUDGED[fold]).to_numpy()
                tm = (ff.season == TEST[1]).to_numpy() if fold == 1 else np.zeros(len(ff), bool)
                d = np.abs(svals(inst, ff) - svals(inst, f0)).max(1)
                rec = dict(instance=inst, fold=fold, cell=GS.skey(H, P), f=f,
                           burn_max_raw=np.abs(raw1[bm]).max(0).tolist(),
                           burn_max_raw_unfloored=np.abs(raw0[bm]).max(0).tolist(),
                           judged_max_raw=np.abs(raw1[jm]).max(0).tolist(),
                           judged_max_raw_unfloored=np.abs(raw0[jm]).max(0).tolist(),
                           judged_bit_identical=bool(np.array_equal(svals(inst, ff)[jm], svals(inst, f0)[jm])),
                           judged_max_abs_delta=float(d[jm].max()),
                           judged_dates_differing=int((d[jm] > 0).sum()),
                           judged_first_last_diff=[str(x) for x in pd.to_datetime(ff.date[jm & (d > 0)]).agg(["min", "max"])]
                           if (jm & (d > 0)).any() else None,
                           fold1_test_bit_identical=bool(np.array_equal(svals(inst, ff)[tm], svals(inst, f0)[tm])) if fold == 1 else None,
                           floor_bind_dates=int(ff.floor_binds.sum()),
                           floor_bind_judged=int(ff.floor_binds[jm].sum()),
                           floor_last_bind=str(pd.to_datetime(ff.date[ff.floor_binds]).max()) if ff.floor_binds.any() else None,
                           burn_last_diff=str(pd.to_datetime(ff.date[d > 0]).max()) if (d > 0).any() else None)
                rec["ratio_ok"] = bool(all(b <= 3 * j for b, j in zip(rec["burn_max_raw"], rec["judged_max_raw"])))
                out["grid"].append(rec)
                print(now(), inst, fold, f, f"{time.time() - t2:.1f}s", {k: rec[k] for k in
                      ("burn_max_raw", "judged_max_raw", "judged_bit_identical", "judged_max_abs_delta",
                       "floor_bind_dates", "floor_bind_judged", "ratio_ok")}, flush=True)
            out["clock"].append(dict(step=f"{inst} f{fold} f grid", secs=round(time.time() - t1, 1)))
    G = pd.DataFrame(out["grid"])
    sel = None
    for f in F_GRID:
        g = G[G.f == f]
        if g.ratio_ok.all() and g.judged_bit_identical.all():
            sel = f
            break
    out["selected_f"] = sel
    (RES / "as1.json").write_text(json.dumps(out, indent=1, default=str))
    print(now(), "selected f", sel, flush=True)


# ------------------------------------------------------------------------------------------------ write
def cmd_write(a):
    o = json.loads((RES / "as1.json").read_text())
    f = o["selected_f"]
    assert f is not None, "no f selected"
    for inst, (inputs, snap, grid) in {"goalie": (goalie_inputs, goalie_snap, GS.GRID_ORDER),
                                       "stage4": (stage4_inputs, stage4_snap, QS.GRID_ORDER)}.items():
        for fold in (1, 2):
            t0 = time.time()
            I = inputs(fold)
            iref = np.atleast_2d(I["iref"])
            fl = (f, iref if inst == "stage4" else float(iref[0, 0]))
            parts = []
            for H, P in grid:
                x = snap(I, H, P, floor=fl)
                x.insert(0, "cell", GS.skey(H, P))
                x.insert(1, "H", H)
                x.insert(2, "P", P)
                parts.append(x)
            Fr = add_season(pd.concat(parts, ignore_index=True), I["season"])
            if inst == "goalie":
                Fr["sd_ref"] = I["sd"][0]
            else:
                Fr["sd_for"], Fr["sd_against"] = I["sd"]
            Fr["floor_f"] = f
            Fr["rows_scope"] = "2021-22..2023-24 (no 2024-25 row; AS-1)"
            out = v2_path(inst, fold)
            assert not out.exists() or a.force, f"{out} exists"
            assert "_v2_" in out.name
            Fr.to_parquet(out, index=False)
            print(now(), inst, fold, "written", out, f"{time.time() - t0:.0f}s", flush=True)
    insample_restated(f)


def insample_restated(f):
    """AS-1 step 5: the SL-R7 in-sample stratum check (fold-2 training rows) under the floored stage-4 snapshot."""
    MS, V6 = V7.MS, V7.V6
    D = V7.fold_data(2)
    r, off, ntr = D["r"], D["off"], D["ntr"]
    tr, otr = r.iloc[:ntr].reset_index(drop=True), off[:ntr]
    assert (tr.season != TEST[2]).all()
    cell = QS.skey(*INC["stage4"])
    P = {"L0s": MS.l0s_levelled(D["l0s"], tr, otr)}
    for tag, path in (("v1", v1_path("stage4", 2)), ("v2", v2_path("stage4", 2))):
        F = pd.read_parquet(path)
        sf, sa = V7.cell_scale(F, cell, tr.game_date_local.to_numpy())
        P[tag] = V7.predict_as(D, tr, otr, sf, sa)
    xg = D["xg"]
    grp = tr.grp.to_numpy()
    xg_cls = xg[:, grp].T
    st, pt = tr.st.to_numpy(), tr.ptype.to_numpy()
    dd = pd.to_datetime(tr.game_date_local)
    cells = [(MS.STATE_NAMES[k], st == k) for k in range(7)]
    cells += [(f"{MS.STATE_NAMES[k]} {'OT' if q else 'reg'}", (st == k) & (pt == q)) for k in range(7) for q in (0, 1)]
    scopes = [("all training rows", np.ones(len(tr), bool)),
              ("2021-22 through 10-25", ((tr.season == BURN) & (dd <= "2021-10-25")).to_numpy()),
              ("2021-22 after 10-25", ((tr.season == BURN) & (dd > "2021-10-25")).to_numpy()),
              ("judged 2022-23 onward", (tr.season != BURN).to_numpy())]
    rows = []
    for scope, sm in scopes:
        for nm, m0 in cells:
            m = m0 & sm
            n = int(m.sum())
            if n == 0:
                continue
            base = (P["L0s"][m] * xg_cls[m]).sum(1).mean()
            rec = dict(scope=scope, stratum=nm, n=n)
            for tag in ("v1", "v2"):
                rec[f"L1xas_{tag}_vs_L0s"] = float((P[tag][m] * xg_cls[m]).sum(1).mean() / base - 1)
            rec["within_0.5pct_n2000"] = (n < V6.N_MIN) or abs(rec["L1xas_v2_vs_L0s"]) <= V6.TOL
            rows.append(rec)
    j = ~(tr.season == BURN).to_numpy()
    res = dict(f=f, cell=cell, rows=rows, judged_predictions_identical=bool(np.array_equal(P["v1"][j], P["v2"][j])),
               ll_per_attempt={k: float(V7.M.joint_ll(v, tr.cls.to_numpy()).mean()) for k, v in P.items()})
    (RES / "insample_restated.json").write_text(json.dumps(res, indent=1))
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows).to_string(), flush=True)
    print(now(), "judged identical", res["judged_predictions_identical"], res["ll_per_attempt"], flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "write"])
    ap.add_argument("--force", action="store_true", help="rewrite an existing v2 sibling (this lane's own file)")
    a = ap.parse_args()
    {"run": cmd_run, "write": cmd_write}[a.cmd](a)
