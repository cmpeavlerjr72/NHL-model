"""G-R3 trainer: as-of goalie response scale (docs/models/goal/experiments.md G-R3; INV-53).

Frozen from G-R2: level M1 K500, cell tables, rating tables and (b, w) cells, goalie c_g / s_g for the reference C1,
team finishing at its fixed scale (s_t x c_t), grading. Only C1-type arms.

    train_goal_v3.py snap      s_t snapshots per fold for the whole grid H {90,180,365} x P {2000,10000}
                               -> data/processed/goal/goalie_scale_v1_f{fold}.parquet
    train_goal_v3.py parity    per genuine-prior training season (fold 1: 2022-23; fold 2: 2022-23, 2023-24): goalie R
                               of C1s (fitted on the fold's training rows) and of G-R2's fixed-scale C1; selection
                               -> results/goal_g_r3/select.json, docs/tests/goal_g_r3_parity_2026-10-16.md
                               (training seasons only: no test-season row, prediction or s_t value is read)
    train_goal_v3.py fold2|fold1   C0, C1 (G-R2 reference), C1s at the selected (H, P); C1s2 = a spec-identical
                               refit (deterministic, so bit-identical; reported) ; hash-labelled blind predictions
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402
from nhl_sim.goal import data as D  # noqa: E402
from nhl_sim.goal import models as GM  # noqa: E402
from nhl_sim.goal import scale as SC  # noqa: E402

RES = Path("results/goal_g_r3")
R1 = Path("results/goal_g_r1")
R2 = Path("results/goal_g_r2")
SELECT_R1 = R1 / "select.json"
SELECT = RES / "select.json"
SALT = "G-R3-2026-10-16"
ARMS = ("C0", "C1", "C1s", "C1s2")
LEVEL = "M1_K500"
BAND_P = (0.9, 1.1)
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def scale_path(fold):
    return D.OUT / f"goalie_scale_v1_f{fold}.parquet"


def frames(fold):
    """All rows of the fold (training seasons + test season), C0 logit offsets, ratings attached, team offset, z."""
    if fold not in _CACHE:
        assert json.loads((R2 / "step1.json").read_text())["selected"] == LEVEL
        tr_s, te_s = D.F[fold]
        S = json.loads(SELECT_R1.read_text())
        rows = pd.read_parquet(R1 / "rows_v1.parquet")
        r = rows[rows.season.isin(tr_s + [te_s])].reset_index(drop=True)
        T = np.load(D.OUT / f"cell_table_f{fold}.npy")
        lv = pd.read_parquet(D.OUT / f"level_v1_f{fold}.parquet")
        off = D.c0_logit(r, T, lv[lv.construction == LEVEL])
        RG = pd.read_parquet(D.OUT / f"ratings_goalie_v1_f{fold}.parquet")
        RT = pd.read_parquet(D.OUT / f"ratings_team_v1_f{fold}.parquet")
        g, t = tuple(S["goalie_cell"]), tuple(S["team_cell"])
        r = r.assign(g_r=D.attach_rating(r, RG.rename(columns={D.rkey(*g): "r"}), "goalie_id"),
                     t_r=D.attach_rating(r, RT.rename(columns={D.rkey(*t): "r"}), "team_id"))
        sd_ref = float(r.g_r[r.season == D.SEASONS[0]].std())
        r["z"] = r.g_r / sd_ref
        _CACHE[fold] = (r, off, S["spec"], sd_ref, tr_s, te_s)
    return _CACHE[fold]


# -------------------------------------------------------------------------------------------------- step 1
def cmd_snap(a):
    for fold in (1, 2):
        r, off, spec, sd_ref, tr_s, te_s = frames(fold)
        o = off + SC.team_off(r, spec)
        parts = []
        for H, P in SC.GRID_ORDER:
            t0 = time.time()
            f = SC.asof_scale(r.date.to_numpy(), r["drop"].to_numpy(), r.y.to_numpy(), o, r.z.to_numpy(), H, P)
            f.insert(0, "cell", SC.skey(H, P))
            f.insert(1, "H", H)
            f.insert(2, "P", P)
            parts.append(f)
            print(now(), f"fold {fold} {SC.skey(H, P)}: {len(f)} dates, {time.time() - t0:.1f} s", flush=True)
        F = pd.concat(parts, ignore_index=True)
        F["sd_ref"] = sd_ref
        F["season"] = F.date.map(dict(zip(pd.to_datetime(r.date), r.season)))
        F.to_parquet(scale_path(fold), index=False)
        print(now(), f"fold {fold} written {scale_path(fold)} sd_ref {sd_ref:.5f}", flush=True)


# -------------------------------------------------------------------------------------------------- step 2
def ll_rows(p, y):
    return y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))


def R_season(p, x, n_boot=200):
    g = x.sg.isin(D.GATED_SG).to_numpy()
    s = slope_ratio(p[g], x.y.to_numpy(float)[g], x.g_r.to_numpy(float)[g], np.ones(g.sum()), x.game_id.to_numpy()[g],
                    n_buckets=10, n_boot=n_boot)
    return s


def goff_of(r, fold, cell):
    F = pd.read_parquet(scale_path(fold))
    sc = F[F.cell == cell]
    return SC.attach_scale(r, sc) * r.z.to_numpy()


def cmd_parity(a):
    RES.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, traj = [], []
    for fold in (1, 2):
        r, off, spec, sd_ref, tr_s, te_s = frames(fold)
        m = r.season.isin(tr_s).to_numpy()
        tr, otr = r[m].reset_index(drop=True), off[m]
        # G-R2 fixed-scale C1, refit on this fold's training rows (as G-R2)
        m1 = GM.fit_c1(tr, otr, spec)
        p1 = GM.predict_c1(m1, tr, otr)
        F = pd.read_parquet(scale_path(fold))
        for s in D.JUDGED[fold]:
            k = (tr.season == s).to_numpy()
            q = R_season(p1[k], tr[k])
            rows.append(dict(fold=fold, season=s, arm="C1 fixed (G-R2)", cell="s_g 0.5 x c_g", R=q["R"], lo=q["ci"][0],
                             hi=q["ci"][1], ll_sog=float(ll_rows(p1[k], tr.y.to_numpy(float)[k])[tr.sg.isin(D.GATED_SG).to_numpy()[k]].mean())))
        for H, P in SC.GRID_ORDER:
            cell = SC.skey(H, P)
            goff = goff_of(tr, fold, cell)
            ms = SC.fit_c1s(tr, otr, spec, goff)
            ps = SC.predict_c1s(ms, tr, otr, spec, goff)
            for s in D.JUDGED[fold]:
                k = (tr.season == s).to_numpy()
                q = R_season(ps[k], tr[k])
                gk = tr.sg.isin(D.GATED_SG).to_numpy()[k]
                rows.append(dict(fold=fold, season=s, arm="C1s", cell=cell, H=H, P=P, R=q["R"], lo=q["ci"][0], hi=q["ci"][1],
                                 ll_sog=float(ll_rows(ps[k], tr.y.to_numpy(float)[k])[gk].mean())))
            # s_t trajectory over training seasons only (test-season values are not read here)
            sc = F[(F.cell == cell) & F.season.isin(tr_s)]
            for s, g in sc.groupby("season"):
                traj.append(dict(fold=fold, cell=cell, season=s, s_first=g.s.iloc[0], s_mid=g.s.iloc[len(g) // 2],
                                 s_last=g.s.iloc[-1], s_min=g.s.min(), s_max=g.s.max(),
                                 s_raw_last=g.s.iloc[-1] / sd_ref, n_eff_last=g.n_eff.iloc[-1]))
            print(now(), f"fold {fold} {cell} done", flush=True)
        # per-training-season free one-parameter slope (in-season, z units) for reference
        o = otr + SC.team_off(tr, spec)
        for s in tr_s:
            k = (tr.season == s).to_numpy()
            f1 = SC._newton(0.0, tr.y.to_numpy(float)[k], o[k], tr.z.to_numpy()[k], np.ones(k.sum()), 0.0)[0]
            traj.append(dict(fold=fold, cell="season-alone MLE", season=s, s_last=f1, s_raw_last=f1 / sd_ref))
    T = pd.DataFrame(rows)
    J = pd.DataFrame(traj)
    T["log_R"] = np.log(T.R)
    cs = T[T.arm == "C1s"].groupby("cell").agg(H=("H", "first"), P=("P", "first"), max_abs_logR=("log_R", lambda v: v.abs().max()),
                                                 all_in=("R", lambda v: bool(((v >= BAND_P[0]) & (v <= BAND_P[1])).all())),
                                                 R_min=("R", "min"), R_max=("R", "max"))
    cs = cs.loc[[SC.skey(H, P) for H, P in SC.GRID_ORDER]]
    passers = [c for c in cs.index if cs.loc[c, "all_in"]]
    if passers:
        sel, how = passers[0], "simplest passer (larger H, then larger P)"
    else:
        sel, how = cs.max_abs_logR.idxmin(), "no passer: smallest max |log R| (listed), proceed"
    H, P = int(cs.loc[sel, "H"]), int(cs.loc[sel, "P"])
    out = dict(selected=sel, H=H, P=P, rule=how, passers=passers, sd_ref={f: frames(f)[3] for f in (1, 2)},
               table=T.to_dict("records"), summary=cs.reset_index().to_dict("records"), generated=now())
    SELECT.write_text(json.dumps(out, indent=1, default=float))
    L = ["# G-R3 step 2: parity analogue and (H, P) selection (Lane G3, 2026-10-16)", "",
         f"Generated {now()} ({time.time() - t0:.0f} s) by `scripts/train_goal_v3.py parity`. Committed BEFORE any fold-2 "
         "prediction. Training seasons only: no test-season row, prediction or s_t value is read in this step.", "",
         "Construction (spec G-R3; code `src/nhl_sim/goal/scale.py`, leakage test `tests/test_goal_asof_scale.py`): the goalie "
         "rating (G-R1 cell b 3000, w 0.5) enters C1s as s_t x z, z = g_r / SD_REF (SD of g_r over the 2021-22 rows of the "
         f"fold: fold 1 {frames(1)[3]:.5f}, fold 2 {frames(2)[3]:.5f}; a unit only). s_t is a one-parameter logistic slope "
         "on all in-scope SOG dated before the game date, weights 0.5^(age/H), offset C0 (M1 K500) + team offset (fixed, "
         "G-R1 cell at s 1.0), shrunk to the previous date's s with a prior of P shots (precision P x per-shot Fisher "
         "information). Start s = 0 before any data (2021-22 burn-in, labelled, never judged). C1s base coefficients "
         "(strength group, score, home, b2b, arena) are refit on the fold's training rows with both rating offsets fixed. "
         "R = D32 decile slope ratio of the goalie rating, gated rows of that season; CI = 200-resample game bootstrap.", "",
         "Reading of the fit (labelled): the C1s base coefficients are fitted on the fold's training rows (in sample, as for "
         "G-R2's C1 in this table); the goalie response itself is as-of, so the goalie R is out of sample for the scale.", "",
         "## Per-season goalie R", "", T.drop(columns=["log_R"]).to_markdown(index=False, floatfmt=".4f"), "",
         "## Per cell (C1s, all three genuine-prior season cells; band [0.9, 1.1])", "",
         cs.to_markdown(floatfmt=".4f"), "",
         f"- **Selected: {sel} (H {H}, P {P})**: {how}. Passers: {passers or 'none'}.", "",
         "## s_t over training seasons (z units; s_raw = s / SD_REF, comparable to the raw-unit fixed scale "
         f"s_g x c_g = {0.5 * frames(1)[2]['c_g']:.4f})", "", J.to_markdown(index=False, floatfmt=".4f"), ""]
    Path("docs/tests/goal_g_r3_parity_2026-10-16.md").write_text("\n".join(L), encoding="utf-8")
    print(cs.to_markdown(floatfmt=".4f"))
    print(now(), "selected", sel, how, flush=True)


# ---------------------------------------------------------------------------------------------- step 3 / 4
def cmd_fit(fold, a):
    S3 = json.loads(SELECT.read_text())
    cell = S3["selected"]
    out = RES / f"fold{fold}"
    (out / "models").mkdir(parents=True, exist_ok=True)
    r, off, spec, sd_ref, tr_s, te_s = frames(fold)
    m = r.season.isin(tr_s).to_numpy()
    tr, te, otr, ote = r[m].reset_index(drop=True), r[~m].reset_index(drop=True), off[m], off[~m]
    preds = {"C0": D.sigmoid(ote)}
    m1 = GM.fit_c1(tr, otr, spec)
    (out / "models" / "C1.json").write_text(json.dumps(m1, default=float))
    preds["C1"] = GM.predict_c1(m1, te, ote)
    gtr, gte = goff_of(tr, fold, cell), goff_of(te, fold, cell)
    ms = SC.fit_c1s(tr, otr, spec, gtr)
    (out / "models" / "C1s.json").write_text(json.dumps(dict(ms, cell=cell, sd_ref=sd_ref), default=float))
    preds["C1s"] = SC.predict_c1s(ms, te, ote, spec, gte)
    ms2 = SC.fit_c1s(tr.sample(frac=1.0, random_state=2).sort_index(), otr, spec, gtr)   # spec-identical refit
    preds["C1s2"] = SC.predict_c1s(ms2, te, ote, spec, gte)
    keep = ["game_id", "season", "game_type", "date", "team_id", "opp_id", "goalie_id", "is_home", "b2b_own", "sg", "lg",
            "tier", "cell", "type6", "sc", "period", "ptype", "rebound", "rush", "y", "g_r", "t_r", "arena", "arena_f"]
    te[keep].to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    for arm, p in preds.items():
        p = np.asarray(p, np.float64)
        if p.shape != (len(te),) or not np.isfinite(p).all():
            raise ValueError(f"{arm}: bad probabilities")
        np.save(out / f"fold{fold}_pred_{label(arm)}.npy", p)
    (out / "labels_sealed.json").write_text(json.dumps({k: label(k) for k in ARMS}))
    (out / "fit_info.json").write_text(json.dumps(dict(cell=cell, sd_ref=sd_ref, C1=m1["coef"], C1s=ms["coef"],
                                                       C1s2=ms2["coef"], spec=spec), indent=1, default=float))
    print(now(), f"fold {fold} fitted ({cell}); C1s coef", np.round(ms["coef"], 4).tolist(), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snap", "parity", "fold2", "fold1"])
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    {"snap": cmd_snap, "parity": cmd_parity, "fold2": lambda a: cmd_fit(2, a), "fold1": lambda a: cmd_fit(1, a)}[a.cmd](a)
    print(now(), "done", a.cmd, flush=True)
