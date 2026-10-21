"""G-R4 trainer: score-state terms of the goal model (docs/models/goal/experiments.md G-R4; D48, INV-74).

Frozen from G-R3 / D40: level M1 K500, cell tables, rating tables, team finishing at its fixed scale, the as-of goalie
scale H90 P2000 (AS-1: v2 snapshot where it exists, v1 beyond, identical on every served date, D44), the fold's C1s
non-score coefficients (sg intercepts, home, b2b own / opp, arena factor). Only the score-state terms change.
Code: `src/nhl_sim/goal/score_asof.py`.

    train_goal_v4.py step0     training seasons only: per-season 4-bucket deviation coefficients (offset = the fold's C1s
                               non-score logit) with model and game-cluster SEs and a trend z; per-season C1s served /
                               actual by bucket relative to tied -> results/goal_g_r4/step0.json,
                               docs/tests/goal_g_r4_step0_2026-10-21.md
    train_goal_v4.py snap      C1s-sa as-of deviation snapshots, grid H {90,180,365} x P {2000,10000}, AS-1 floor f 0.5
                               -> data/processed/goal/score_dev_v1_f{fold}.parquet
    train_goal_v4.py parity    judged training seasons only (fold 1: 2022-23; fold 2: 2022-23, 2023-24): C1s-sa served /
                               actual by bucket relative to tied, +/-3%; selection -> results/goal_g_r4/select.json,
                               docs/tests/goal_g_r4_parity_2026-10-21.md (no test-season row or snapshot value is read)
    train_goal_v4.py fold1|fold2   C0, C1s (frozen G-R3 model; reproduction asserted), C1s-sa (selected cell),
                               C1s-sp, C1s-sap fitted on the fold's training rows; hash-labelled blind predictions
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import train_goal_v3 as G3  # noqa: E402
from nhl_sim.goal import data as D  # noqa: E402
from nhl_sim.goal import scale as SC  # noqa: E402
from nhl_sim.goal import score_asof as SA  # noqa: E402

RES = ROOT / "results/goal_g_r4"
SELECT = RES / "select.json"
SALT = "G-R4-2026-10-21"
ARMS = ("C0", "C1s", "C1s-sa", "C1s-sp", "C1s-sap")
GCELL = "H90_P2000"
TOL3 = 0.03
NB = 1000
BSEED = 20261021


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def dev_path(fold):
    return D.OUT / f"score_dev_v1_f{fold}.parquet"


def goalie_scale_v21(fold):
    """Per-date goalie scale of the incumbent cell: v2 (AS-1) where it exists, v1 beyond; asserts v1 == v2 on every
    date after the AS-1 coalescence (D44)."""
    v1 = pd.read_parquet(D.OUT / f"goalie_scale_v1_f{fold}.parquet")
    v2 = pd.read_parquet(D.OUT / f"goalie_scale_v2_f{fold}.parquet")
    v1, v2 = v1[v1.cell == GCELL].set_index("date"), v2[v2.cell == GCELL].set_index("date")
    j = v1[["s"]].join(v2[["s"]], rsuffix="_2", how="inner")
    late = j.index > pd.Timestamp("2022-02-07")
    if not (j.s[late] == j.s_2[late]).all():
        raise ValueError("goalie scale v1 != v2 after the AS-1 coalescence")
    s = v1.s.copy()
    s.loc[v2.index] = v2.s
    return pd.DataFrame({"date": s.index, "s": s.to_numpy()})


_F = {}


def frames4(fold):
    """G-R3 frames + the frozen fold C1s model + offsets:
       fixed_v1 = C0 + team + goalie (v1 scale; the G-R3 C1s reproduction), fixed = the same with the v2/v1 scale,
       ns = C1s non-score logit (on `fixed`)."""
    if fold not in _F:
        r, off, spec, sd_ref, tr_s, te_s = G3.frames(fold)
        mdl = json.loads((G3.RES / f"fold{fold}" / "models" / "C1s.json").read_text())
        assert mdl["cell"] == GCELL
        goff1 = G3.goff_of(r, fold, GCELL)
        goff = SC.attach_scale(r, goalie_scale_v21(fold)) * r.z.to_numpy()
        toff = SC.team_off(r, spec)
        fixed_v1 = off + toff + goff1
        fixed = off + toff + goff
        ns = SA.nonscore_logit(mdl["coef"], r, fixed)
        _F[fold] = dict(r=r, off=off, spec=spec, sd_ref=sd_ref, tr_s=tr_s, te_s=te_s, mdl=mdl, goff1=goff1, goff=goff,
                        fixed_v1=fixed_v1, fixed=fixed, ns=ns, b=SA.bucket(r), X=SA.dev_design(r))
    return _F[fold]


def boot_w(games):
    G = len(games)
    return np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)


def gated(r):
    return r.sg.isin(D.GATED_SG).to_numpy()


def ratio_rows(p, r, tag):
    """served / actual by bucket relative to tied on gated rows, with game-bootstrap SE."""
    g = gated(r)
    x = r[g]
    games, gp = np.unique(x.game_id.to_numpy(), return_inverse=True)
    rat, se = SA.bucket_ratio(np.asarray(p)[g], x.y.to_numpy(float), SA.bucket(x), gp, len(games), boot_w(games))
    out = []
    for b in range(5):
        if b == SA.TIED:
            continue
        out.append(dict(tag, bucket=SA.B_NAMES[b], ratio=float(rat[b]), se=float(se[b]), log_ratio=float(np.log(rat[b])),
                        n_sog=int((SA.bucket(x) == b).sum()), goals=int(x.y.to_numpy()[SA.bucket(x) == b].sum()),
                        within_3pct=bool(abs(rat[b] - 1) <= TOL3)))
    return out


# --------------------------------------------------------------------------------------------------------- step 0
def cluster_se(off, y, X, d, gid):
    p = D.sigmoid(off + X @ d)
    I = (X * (p * (1 - p))[:, None]).T @ X
    Ii = np.linalg.inv(I)
    sc = X * (y - p)[:, None]
    _, inv = np.unique(gid, return_inverse=True)
    S = np.zeros((inv.max() + 1, X.shape[1]))
    np.add.at(S, inv, sc)
    V = Ii @ (S.T @ S) @ Ii
    return np.sqrt(np.diag(Ii)), np.sqrt(np.diag(V))


def trend(c, se):
    w = 1 / se ** 2
    t = np.arange(len(c), dtype=float)
    tb = float(np.polyfit(t, c, 1, w=1 / se)[0])
    tse = float(1 / np.sqrt((w * (t - (w * t).sum() / w.sum()) ** 2).sum()))
    return tb, tse, tb / tse


def cmd_step0(a):
    RES.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    coef_rows, tr_rows, rat_rows = [], [], []
    for fold in (1, 2):
        F = frames4(fold)
        r = F["r"]
        y = r.y.to_numpy(float)
        p_c1s = SC.predict_c1s(F["mdl"], r, F["off"], F["spec"], F["goff1"])
        for s in F["tr_s"]:
            k = (r.season == s).to_numpy()
            d = SA.fit_once(F["ns"][k], y[k], F["X"][k])
            se_m, se_c = cluster_se(F["ns"][k], y[k], F["X"][k], d, r.game_id.to_numpy()[k])
            for j, b in enumerate(SA.DEV_B):
                coef_rows.append(dict(fold=fold, season=s, bucket=SA.B_NAMES[b], coef=float(d[j]), se_model=float(se_m[j]),
                                      se_cluster=float(se_c[j])))
            rat_rows += ratio_rows(p_c1s[k], r[k].reset_index(drop=True), dict(fold=fold, season=s, arm="C1s (in sample)"))
        C = pd.DataFrame([c for c in coef_rows if c["fold"] == fold])
        for b in C.bucket.unique():
            g = C[C.bucket == b].sort_values("season")
            tb, tse, z = trend(g.coef.to_numpy(), g.se_cluster.to_numpy())
            tr_rows.append(dict(fold=fold, bucket=b, n_seasons=len(g), trend_per_season=tb, trend_se=tse, trend_z=z))
        print(now(), f"fold {fold} step 0 done", flush=True)
    C, T, R = pd.DataFrame(coef_rows), pd.DataFrame(tr_rows), pd.DataFrame(rat_rows)
    c1s = {f: np.asarray(frames4(f)["mdl"]["coef"])[SA.SCORE_COLS].tolist() for f in (1, 2)}
    (RES / "step0.json").write_text(json.dumps(dict(coef=C.to_dict("records"), trend=T.to_dict("records"),
                                                    ratio=R.to_dict("records"), c1s_score_coef=c1s, generated=now()),
                                               indent=1, default=float))
    piv = C.pivot_table(index=["fold", "bucket"], columns="season", values=["coef", "se_cluster"])
    L = ["# G-R4 step 0: per-season score-bucket deviations and C1s served / actual by bucket (Lane G4, 2026-10-21)", "",
         f"Generated {now()} ({time.time() - t0:.0f} s) by `scripts/train_goal_v4.py step0`. **Training seasons only** "
         "(fold 1: 2021-22, 2022-23; fold 2: 2021-22..2023-24). Committed before any arm is fit; no test-season row is read.", "",
         "Per-season coefficient: the four bucket log-odds deviations relative to tied (trail 2+ = shooter down 2 or more, "
         "trail 1, lead 1, lead 2+; score BEFORE the shot), unpenalised MLE with the fold's frozen C1s non-score logit as "
         "offset (C0 M1 K500 + sg intercepts + home + b2b + arena + team finishing at its fixed scale + as-of goalie scale), "
         "all in-scope SOG of that season (EAF rows carry no score term). SEs: model and game-cluster (sandwich). Trend = "
         "inverse-variance-weighted slope per season on the cluster SEs (the G-R1 step-0 form).", "",
         "## Per-season coefficients", "", C.to_markdown(index=False, floatfmt=".4f"), "",
         "## Trend across training seasons", "", T.to_markdown(index=False, floatfmt=".4f"), "",
         "For reference, the pooled C1s score dummies (sc -3+, -2, -1, +1, +2, +3+; tied = 0): fold 1 "
         f"{np.round(c1s[1], 4).tolist()}, fold 2 {np.round(c1s[2], 4).tolist()}.", "",
         "## C1s served / actual conversion by bucket, relative to tied (gated rows, in sample on its own training "
         "seasons; game-bootstrap SE, 1,000 resamples)", "", R.to_markdown(index=False, floatfmt=".4f"), ""]
    Path(ROOT / "docs/tests/goal_g_r4_step0_2026-10-21.md").write_text("\n".join(L), encoding="utf-8")
    print(T.to_markdown(index=False, floatfmt=".4f"))
    print(now(), "step0 written", flush=True)


# -------------------------------------------------------------------------------------------------- step 1: snap
def _snap_job(args):
    fold, H, P = args
    F = frames4(fold)
    r = F["r"]
    b21 = (r.season == D.SEASONS[0]).to_numpy()
    iref = SA.info_ref(F["ns"][b21], F["X"][b21])
    t0 = time.time()
    f = SA.asof_dev(r.date.to_numpy(), r["drop"].to_numpy(), F["ns"], r.y.to_numpy(float), F["X"], H, P,
                    floor=(SA.F_FLOOR, iref))
    f.insert(0, "cell", SA.skey(H, P))
    f.insert(1, "H", H)
    f.insert(2, "P", P)
    f["floor_f"] = SA.F_FLOOR
    return f, time.time() - t0, iref


def cmd_snap(a):
    jobs = [(fold, H, P) for fold in (1, 2) for H, P in SA.GRID_ORDER] if not a.cells else \
        [(fold, int(c.split("_")[0][1:]), int(c.split("_")[1][1:])) for fold in (1, 2) for c in a.cells]
    out = {1: [], 2: []}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for (fold, H, P), (f, dt, iref) in zip(jobs, ex.map(_snap_job, jobs)):
            print(now(), f"fold {fold} {SA.skey(H, P)}: {len(f)} dates, {dt:.1f} s, floor binds on "
                  f"{int(f.floor_binds.sum())} dates (last {f.date[f.floor_binds].max() if f.floor_binds.any() else None}); "
                  f"I_ref diag {np.round(np.diag(iref), 5).tolist()}", flush=True)
            out[fold].append(f)
    if a.dry:
        return
    for fold in (1, 2):
        Fr = pd.concat(out[fold], ignore_index=True)
        r = frames4(fold)["r"]
        Fr["season"] = Fr.date.map(dict(zip(pd.to_datetime(r.date), r.season)))
        Fr.to_parquet(dev_path(fold), index=False)
        print(now(), f"fold {fold} written {dev_path(fold)}", flush=True)


# ------------------------------------------------------------------------------------------------ step 2: parity
def cmd_parity(a):
    RES.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, traj = [], []
    for fold in (1, 2):
        F = frames4(fold)
        r = F["r"]
        m = r.season.isin(F["tr_s"]).to_numpy()
        tr = r[m].reset_index(drop=True)
        ns, X = F["ns"][m], F["X"][m]
        p_c1s = SC.predict_c1s(F["mdl"], tr, F["off"][m], F["spec"], F["goff1"][m])
        S = pd.read_parquet(dev_path(fold))
        S = S[S.season.isin(F["tr_s"])]                      # training-season snapshot dates only
        for s in D.JUDGED[fold]:
            k = (tr.season == s).to_numpy()
            rows += ratio_rows(p_c1s[k], tr[k].reset_index(drop=True), dict(fold=fold, season=s, arm="C1s", cell="pooled"))
        for H, P in SA.GRID_ORDER:
            cell = SA.skey(H, P)
            sc = S[S.cell == cell]
            Dv = SA.attach_dev(tr.date.to_numpy(), sc)
            p = D.sigmoid(ns + (X * Dv).sum(1))
            for s in D.JUDGED[fold]:
                k = (tr.season == s).to_numpy()
                rows += ratio_rows(p[k], tr[k].reset_index(drop=True), dict(fold=fold, season=s, arm="C1s-sa", cell=cell, H=H, P=P))
            for s, g in sc.groupby("season"):
                rec = dict(fold=fold, cell=cell, season=s, floor_bind_dates=int(g.floor_binds.sum()))
                for j, b in enumerate(SA.DEV_B):
                    v = g[f"d_{j}"]
                    rec.update({f"{SA.B_NAMES[b]}_first": v.iloc[0], f"{SA.B_NAMES[b]}_last": v.iloc[-1],
                                f"{SA.B_NAMES[b]}_min": v.min(), f"{SA.B_NAMES[b]}_max": v.max()})
                traj.append(rec)
        print(now(), f"fold {fold} parity done", flush=True)
    T = pd.DataFrame(rows)
    J = pd.DataFrame(traj)
    sa = T[T.arm == "C1s-sa"]
    cs = sa.groupby("cell").agg(H=("H", "first"), P=("P", "first"), max_abs_log_ratio=("log_ratio", lambda v: v.abs().max()),
                                all_within=("within_3pct", "all"), n_fail=("within_3pct", lambda v: int((~v).sum())))
    cs = cs.loc[[SA.skey(H, P) for H, P in SA.GRID_ORDER]]
    c1s_ref = T[T.arm == "C1s"]
    passers = [c for c in cs.index if cs.loc[c, "all_within"]]
    if passers:
        sel, how = passers[0], "simplest passer (larger H, then larger P)"
    else:
        sel, how = cs.max_abs_log_ratio.idxmin(), "no passer: smallest max |log ratio| (listed), proceed"
    H, P = int(cs.loc[sel, "H"]), int(cs.loc[sel, "P"])
    SELECT.write_text(json.dumps(dict(selected=sel, H=H, P=P, rule=how, passers=passers, table=T.to_dict("records"),
                                      summary=cs.reset_index().to_dict("records"), generated=now()), indent=1, default=float))
    wide = sa.pivot_table(index=["cell", "fold", "season"], columns="bucket", values="ratio").reindex(
        columns=[SA.B_NAMES[b] for b in SA.DEV_B])
    wref = c1s_ref.pivot_table(index=["fold", "season"], columns="bucket", values="ratio").reindex(
        columns=[SA.B_NAMES[b] for b in SA.DEV_B])
    L = ["# G-R4 step 2: C1s-sa parity analogue and (H, P) selection (Lane G4, 2026-10-21)", "",
         f"Generated {now()} ({time.time() - t0:.0f} s) by `scripts/train_goal_v4.py parity`. Committed BEFORE any fold-2 "
         "prediction. **Judged training seasons only** (fold 1: 2022-23; fold 2: 2022-23, 2023-24); no test-season row, "
         "prediction or snapshot value is read in this step.", "",
         "Construction (spec G-R4; `src/nhl_sim/goal/score_asof.py`, leakage tests `tests/test_goal_score_asof.py`): the four "
         "bucket log-odds deviations relative to tied (trail 2+, trail 1, lead 1, lead 2+; score before the shot) are a "
         "four-parameter as-of logistic fit with the fold's frozen C1s non-score logit as offset, rows weighted 0.5^(age/H), "
         "shrunk to the previous date's values with a prior of P SOG (precision P x per-SOG Fisher information), AS-1 floor "
         "f = 0.5 (I_ref = the fold's 2021-22 rows at d = 0), start 0 (2021-22 burn-in, never judged). Check: served / "
         "actual conversion by bucket relative to tied, gated rows (5v5, PP, PK), within +/-3% on every judged season. SE = "
         "1,000-resample game bootstrap (reported; the band is read on the point estimate).", "",
         "Reading (labelled): the C1s non-score coefficients are fitted on the fold's training rows (in sample, as in G-R3); "
         "the score deviations are as-of, so the bucket ratios are out of sample for the score terms. The pooled C1s rows "
         "are in sample on their own training seasons.", "",
         "## Served / actual by bucket relative to tied, C1s-sa per cell", "", wide.to_markdown(floatfmt=".4f"), "",
         "## The same for the pooled C1s (in sample, reference)", "", wref.to_markdown(floatfmt=".4f"), "",
         "## Long table (with SE, n, goals)", "", T.drop(columns=["log_ratio"]).to_markdown(index=False, floatfmt=".4f"), "",
         "## Per cell (all 4 buckets x 3 judged season-folds; band +/-3%)", "", cs.to_markdown(floatfmt=".4f"), "",
         f"- **Selected: {sel} (H {H}, P {P})**: {how}. Passers: {passers or 'none'}.", "",
         "## Deviation trajectories over training seasons (log-odds)", "", J.to_markdown(index=False, floatfmt=".4f"), ""]
    (ROOT / "docs/tests/goal_g_r4_parity_2026-10-21.md").write_text("\n".join(L), encoding="utf-8")
    print(cs.to_markdown(floatfmt=".4f"))
    print(now(), "selected", sel, how, flush=True)


# ------------------------------------------------------------------------------------------------ steps 3 / 4
def cmd_fit(fold, a):
    S4 = json.loads(SELECT.read_text())
    cell = S4["selected"]
    out = RES / f"fold{fold}"
    (out / "models").mkdir(parents=True, exist_ok=True)
    F = frames4(fold)
    r = F["r"]
    m = r.season.isin(F["tr_s"]).to_numpy()
    tr, te = r[m].reset_index(drop=True), r[~m].reset_index(drop=True)
    sc = pd.read_parquet(dev_path(fold))
    sc = sc[sc.cell == cell]
    Dv = SA.attach_dev(r.date.to_numpy(), sc)
    sa_all = SA.sa_logit(F["ns"], r, Dv)
    preds = {"C0": D.sigmoid(F["off"][~m])}
    p_c1s = SC.predict_c1s(F["mdl"], te, F["off"][~m], F["spec"], F["goff1"][~m])
    ref = np.load(G3.RES / f"fold{fold}" / f"fold{fold}_pred_{G3.label('C1s')}.npy")
    rep = float(np.abs(p_c1s - ref).max())
    if rep > 1e-12:
        raise ValueError(f"C1s does not reproduce G-R3 (max |diff| {rep})")
    preds["C1s"] = p_c1s
    preds["C1s-sa"] = D.sigmoid(sa_all[~m])
    msp = SA.fit_sp(tr, F["fixed"][m])
    preds["C1s-sp"] = SA.predict_sp(msp, te, F["fixed"][~m])
    shares = SA.sap_shares(tr)
    msap = SA.fit_sap(tr, sa_all[m], shares)
    preds["C1s-sap"] = SA.predict_sap(msap, te, sa_all[~m])
    (out / "models" / "C1s-sp.json").write_text(json.dumps(dict(msp, score_table=SA.sp_score_table(msp).tolist()), default=float))
    (out / "models" / "C1s-sap.json").write_text(json.dumps(dict(msap, cell=cell, term_table=SA.sap_term_table(msap).tolist()),
                                                            default=float))
    (out / "models" / "C1s-sa.json").write_text(json.dumps(dict(arm="C1s-sa", cell=cell, c1s_coef=F["mdl"]["coef"],
                                                                snapshot=str(dev_path(fold).relative_to(ROOT))), default=float))
    keep = ["game_id", "season", "game_type", "date", "team_id", "opp_id", "goalie_id", "is_home", "b2b_own", "sg", "lg",
            "tier", "cell", "type6", "sc", "period", "ptype", "rebound", "rush", "y", "g_r", "t_r", "arena", "arena_f"]
    te[keep].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    for arm, p in preds.items():
        p = np.asarray(p, np.float64)
        if p.shape != (len(te),) or not np.isfinite(p).all():
            raise ValueError(f"{arm}: bad probabilities")
        np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p)
    (out / "labels_sealed.json").write_text(json.dumps({k: label(k) for k in ARMS}))
    (out / "fit_info.json").write_text(json.dumps(dict(cell=cell, c1s_reproduction_max_abs_diff=rep, sp=msp["coef"],
                                                       sp_iter=msp["n_iter"], sap=msap["coef"], sap_iter=msap["n_iter"],
                                                       shares=shares.tolist()), indent=1, default=float))
    print(now(), f"fold {fold} fitted ({cell}); C1s reproduction {rep:.1e}; sp iters {msp['n_iter']}, sap iters "
          f"{msap['n_iter']}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["step0", "snap", "parity", "fold2", "fold1"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--cells", nargs="*")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"step0": cmd_step0, "snap": cmd_snap, "parity": cmd_parity, "fold2": lambda a: cmd_fit(2, a),
     "fold1": lambda a: cmd_fit(1, a)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
