"""SL-R7 trainer: L1x-ot0 with the as-of response scale on Qa (docs/models/shot_attribute/experiments.md SL-R7;
D40, INV-59, INV-53; src/nhl_sim/shot_attribute/scale.py).

Frozen from SL-R6 / D38 (read, never refit): L0s (M1 K500, D35), Qa ratings (w 0.7, b 1,000), the quality direction,
the fold's L1x-ot0 home / score / rest terms W (results/shot_attribute_r6_d38[/fold1]/models/L1x.json), EN served L0s.
L1x-as = L0s + W + (s_for,t zf + s_against,t za) c, with the per-date pair from the snapshot of the selected (H, P) cell.

    train_shot_attribute_v7.py snap      per fold, the as-of snapshots for H {45, 90, 180, 365} x P {2000, 10000}
                                         -> data/processed/shot_attribute/sq_scale_v1_f{fold}.parquet
                                         + an exact-evaluation spot check and a series-order check (snap_check.json)
    train_shot_attribute_v7.py parity    step 0 + parity analogue (training seasons only) and the (H, P) selection
                                         -> results/shot_attribute_r7/select.json,
                                            docs/tests/shot_attribute_sl_r7_parity_2026-10-21.md
    train_shot_attribute_v7.py insample  fold-2 TRAINING rows: L1x-as within +/-0.5% xG_ref of L0s in every stratum with
                                         n >= 2,000 (SL-R4 check, inherited); exits 3 on a failure
    train_shot_attribute_v7.py fold1     hash-labelled 2023-24 predictions (L0s, L1x ref, L1x-as, L1x-as2)
    train_shot_attribute_v7.py guard     D28 guard on fold 1 (every SL-R1 bias check on L1x-as MINUS L0s); exits 4
    train_shot_attribute_v7.py pred2     only after insample AND guard passed: hash-labelled 2024-25 predictions
                                         -> results/shot_attribute_r7 (graded blind: grade_shot_attribute.py --round r7)
L1x-as2 is the spec-identical rerun: the selected cell's snapshot recomputed from a within-day shuffled row order.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import train_shot_attribute_v6 as V6  # noqa: E402  (frozen SL-R6 frames / offsets / xG_ref / resp)
from nhl_sim.shot_attribute import models as M  # noqa: E402
from nhl_sim.shot_attribute import models_s as MS  # noqa: E402
from nhl_sim.shot_attribute import models_x as MX  # noqa: E402
from nhl_sim.shot_attribute import scale as SC  # noqa: E402
from nhl_sim.shot_attribute.tables import GROUP_NAMES, N_CLASS, N_TYPE, TIER_NAMES  # noqa: E402

RES = Path("results/shot_attribute_r7")
R6 = Path("results/shot_attribute_r6_d38")
SELECT = RES / "select.json"
PARITY_DOC = Path("docs/tests/shot_attribute_sl_r7_parity_2026-10-21.md")
SALT = "SL-R7-2026-10-21"
ARMS = ("L0s", "L1x", "L1xas", "L1xas2")
JUDGED = {1: [20222023], 2: [20222023, 20232024]}
BAND_P = (0.9, 1.1)
OC, PC = "own_Qa", "opp_Qa"
FIRST = 20212022
CLASS_TIER = V6.CLASS_TIER
CLASS_TYPE = V6.CLASS_TYPE
EN = V6.EN
_CACHE = {}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def label(arm):
    return hashlib.sha1(f"{SALT}|{arm}".encode()).hexdigest()[:8]


def snap_path(fold):
    return M.SA / f"sq_scale_v1_f{fold}.parquet"


def r6dir(fold):
    return R6 / "models" if fold == 2 else R6 / "fold1" / "models"


def frozen_models(fold):
    l0s = json.loads((r6dir(fold) / "L0s.json").read_text())
    m = json.loads((r6dir(fold) / "L1x.json").read_text())
    assert m.get("ot0") is True and m["construction"] == "Qa", "SL-R6 L1x-ot0 (Qa) expected"
    return l0s, m


def fold_data(fold):
    """Training + test rows of the fold, level offsets, xG_ref, frozen models, puck drops, units."""
    if fold not in _CACHE:
        tr, te = V6.frames(fold)
        otr, ote, _ = V6.offsets(fold, tr, te)
        xg = V6.xgref(fold)
        l0s, m = frozen_models(fold)
        l0s_re = MS.fit_l0s(tr)
        if not np.allclose(np.asarray(l0s_re["p"]), np.asarray(l0s["p"]), rtol=0, atol=1e-12):
            raise ValueError("stored SL-R6 L0s differs from a refit on the fold's training rows")
        q = pd.read_parquet(M.SA / f"sq_ratings_v2_f{fold}.parquet", columns=["game_id", "puck_drop"]) \
            .drop_duplicates("game_id").set_index("game_id").puck_drop
        r = pd.concat([tr, te], ignore_index=True)
        off = np.vstack([otr, ote])
        r["drop"] = q.reindex(r.game_id.to_numpy()).to_numpy()
        if r["drop"].isna().any():
            raise ValueError("rows without a puck drop")
        ins = MS.booster_rows(r) & (r.season == FIRST).to_numpy()
        sd = (float(r.loc[ins, OC].std()), float(r.loc[ins, PC].std()))
        _CACHE[fold] = dict(r=r, off=off, ntr=len(tr), xg=xg, l0s=l0s, m=m, sd=sd, tr_s=V6.F[fold][0], te_s=V6.F[fold][1])
    return _CACHE[fold]


def offset_inputs(D, r, off):
    """Non-EN rows: A = log L0s levelled + frozen W terms (ot0), C, zf, za, y; plus the mask."""
    msk = MS.booster_rows(r)
    rr = r[msk]
    B, C, own, opp, X, y = MX.inputs(rr, D["l0s"], off[msk], D["xg"], OC, PC)
    Xc = X - np.asarray(D["m"]["xbar"])
    MX.zero_ot_score(Xc, rr)
    A = B + Xc @ np.asarray(D["m"]["W"])
    return msk, rr, A, C, own / D["sd"][0], opp / D["sd"][1], y


def predict_as(D, r, off, sf, sa):
    """L1x-as: non-EN rows softmax(A + (sf zf + sa za) c); EN rows L0s levelled. sf / sa per row."""
    P = MS.l0s_levelled(D["l0s"], r, off)
    msk, rr, A, C, zf, za, _ = offset_inputs(D, r, off)
    t = sf[msk] * zf + sa[msk] * za
    P[msk] = MX._softmax(A + t[:, None] * C)
    return P


def predict_ref(D, r, off):
    return MX.predict_l1x(D["m"], D["l0s"], r, off, D["xg"], OC, PC)


def snapshots(fold):
    F = pd.read_parquet(snap_path(fold))
    return F


def cell_scale(F, cell, dates):
    return SC.attach_scale(dates, F[F.cell == cell])


# ---------------------------------------------------------------------------------------------------- step 1
def cmd_snap():
    RES.mkdir(parents=True, exist_ok=True)
    checks = {}
    for fold in (1, 2):
        t0 = time.time()
        D = fold_data(fold)
        r, off = D["r"], D["off"]
        msk, rr, A, C, zf, za, y = offset_inputs(D, r, off)
        dates, drops = rr.game_date_local.to_numpy(), rr["drop"].to_numpy()
        print(now(), f"fold {fold}: {len(rr):,} in-scope rows, sd {D['sd']}, inputs {time.time() - t0:.0f} s", flush=True)
        t1 = time.time()
        mom = SC.daily_moments(dates, drops, A, C, y, zf, za)
        print(now(), f"fold {fold}: daily moments ({len(mom['days'])} dates) {time.time() - t1:.1f} s", flush=True)
        parts = []
        for H, P in SC.GRID_ORDER:
            t2 = time.time()
            f = SC.asof_from_moments(mom, H, P)
            f.insert(0, "cell", SC.skey(H, P))
            f.insert(1, "H", H)
            f.insert(2, "P", P)
            parts.append(f)
            print(now(), f"fold {fold} {SC.skey(H, P)}: {time.time() - t2:.1f} s", flush=True)
        Fr = pd.concat(parts, ignore_index=True)
        Fr["sd_for"], Fr["sd_against"] = D["sd"]
        smap = dict(zip(pd.to_datetime(rr.game_date_local).to_numpy("datetime64[D]"), rr.season))
        Fr["season"] = pd.to_datetime(Fr.date).to_numpy("datetime64[D]")
        Fr["season"] = [smap[d] for d in Fr.season.to_numpy()]
        Fr.to_parquet(snap_path(fold), index=False)
        print(now(), f"fold {fold} written {snap_path(fold)}", flush=True)
        # ---- checks: (a) series order 10 vs 14 on two cells; (b) exact Newton step at sampled dates from the series'
        # previous-date pair; (c) max |t| on the rows (vs the series' radius)
        ck = dict(order=SC.ORDER, t_safe=float(mom["t_safe"]))
        ck["direct_evaluations"] = {c: dict(n=int(g.n_exact.sum()), dates=int((g.n_exact > 0).sum()),
                                            last_date=str(g.date[g.n_exact > 0].max()) if (g.n_exact > 0).any() else None)
                                    for c, g in Fr.groupby("cell")}
        t3 = time.time()
        mom10 = SC.daily_moments(dates, drops, A, C, y, zf, za, order=14)
        ck["order14_vs_20_max_abs"] = {}
        for H, P in ((45, 2000), (365, 10000)):
            a = SC.asof_from_moments(mom10, H, P)
            b = Fr[Fr.cell == SC.skey(H, P)]
            ck["order14_vs_20_max_abs"][SC.skey(H, P)] = float(np.abs(a[["s_for", "s_against"]].to_numpy()
                                                                       - b[["s_for", "s_against"]].to_numpy()).max())
        dsort = np.sort(pd.to_datetime(pd.Series(dates)).to_numpy("datetime64[D]"))
        days = mom["days"]
        pick = np.unique(np.linspace(5, len(days) - 1, 8).astype(int))
        ex = []
        dn = pd.to_datetime(pd.Series(dates)).to_numpy("datetime64[D]")
        for H, P in ((45, 2000), (90, 2000), (365, 10000)):
            sc = Fr[Fr.cell == SC.skey(H, P)].reset_index(drop=True)
            for k in pick:
                day = days[k]
                bm = dn < day
                w = 0.5 ** ((day.astype(np.int64) - dn[bm].astype(np.int64)) / H)
                An, Cn, yn = A[bm], C[bm], y[bm]
                zn = np.column_stack([zf[bm], za[bm]])
                cyn = Cn[np.arange(len(yn)), yn]

                def stats(sv, An=An, Cn=Cn, zn=zn, cyn=cyn, w=w):
                    t = zn @ sv
                    p = MX._softmax(An + t[:, None] * Cn)
                    E = (p * Cn).sum(1)
                    V = (p * Cn * Cn).sum(1) - E * E
                    return zn.T @ (w * (cyn - E)), (zn * (w * V)[:, None]).T @ zn, float(w.sum())
                s_prev = sc.loc[k - 1, ["s_for", "s_against"]].to_numpy(float)
                s_ex, _ = SC._newton2(s_prev, stats, P)
                s_se = sc.loc[k, ["s_for", "s_against"]].to_numpy(float)
                ex.append(dict(cell=SC.skey(H, P), date=str(day), n_before=int(bm.sum()),
                               max_abs_diff=float(np.abs(s_ex - s_se).max())))
        ck["exact_step"] = ex
        ck["exact_step_max_abs"] = float(max(e["max_abs_diff"] for e in ex))
        sfz = np.abs(Fr.s_for).max()
        saz = np.abs(Fr.s_against).max()
        ck["max_abs_t_bound"] = float(sfz * np.abs(zf).max() + saz * np.abs(za).max())
        tq = np.abs(zf) * sfz + np.abs(za) * saz
        ck["t_bound_p999"] = float(np.quantile(tq, 0.999))
        ck["c_range"] = float(C.max() - C.min())
        ck["secs"] = round(time.time() - t3)
        ck["elapsed_s"] = round(time.time() - t0)
        ck["n_rows"] = int(len(rr))
        ck["n_dates"] = int(len(days))
        checks[fold] = ck
        print(now(), f"fold {fold} checks", {k: v for k, v in ck.items() if k != "exact_step"}, flush=True)
        del dsort
    (RES / "snap_check.json").write_text(json.dumps(checks, indent=1, default=str))


# ---------------------------------------------------------------------------------------------------- step 0 + 2
def season_R(P, r, xg, n_boot=200):
    grp = r.grp.to_numpy()
    pred = (P * xg[:, grp].T).sum(1)
    act = xg[r.cls.to_numpy(), grp]
    return V6.resp(pred, act, r, OC, PC, n_boot=n_boot)


def cmd_parity():
    t0 = time.time()
    rows, traj, mle = [], [], []
    sd_info = {}
    for fold in (1, 2):
        D = fold_data(fold)
        r, off, ntr = D["r"], D["off"], D["ntr"]
        tr, otr = r.iloc[:ntr].reset_index(drop=True), off[:ntr]
        assert set(tr.season.unique()) == set(D["tr_s"])
        xg = D["xg"]
        F = snapshots(fold)
        Ft = F[F.season.isin(D["tr_s"])]               # training dates only
        sd_info[fold] = D["sd"]
        Pref = predict_ref(D, tr, otr)
        msk, rr, A, C, zf, za, y = offset_inputs(D, tr, otr)
        for s in JUDGED[fold]:
            k = (tr.season == s).to_numpy()
            q = season_R(Pref[k], tr[k], xg)
            rows.append(dict(fold=fold, season=s, arm="L1x-ot0 fixed (SL-R6)", cell="Qa x0.75",
                             R_for=q["for"]["R"], for_ci=q["for"]["ci"], R_against=q["against"]["R"],
                             against_ci=q["against"]["ci"]))
            # post-hoc diagnostic: season-own MLE pair as a fixed scale (in sample; used for no choice)
            km = (rr.season == s).to_numpy()
            s_m = SC.fit_once(A[km], C[km], y[km], zf[km], za[km])
            sf_row = np.full(len(tr), s_m[0])
            sa_row = np.full(len(tr), s_m[1])
            Pm = predict_as(D, tr[k].reset_index(drop=True), otr[k], sf_row[k], sa_row[k])
            q = season_R(Pm, tr[k].reset_index(drop=True), xg)
            rows.append(dict(fold=fold, season=s, arm="season-own MLE (post-hoc diagnostic)", cell="-",
                             R_for=q["for"]["R"], for_ci=q["for"]["ci"], R_against=q["against"]["R"],
                             against_ci=q["against"]["ci"]))
        for s in D["tr_s"]:
            km = (rr.season == s).to_numpy()
            s_m = SC.fit_once(A[km], C[km], y[km], zf[km], za[km])
            mle.append(dict(fold=fold, season=s, s_for_z=s_m[0], s_against_z=s_m[1],
                            s_for_raw=s_m[0] / D["sd"][0], s_against_raw=s_m[1] / D["sd"][1]))
        for H, P in SC.GRID_ORDER:
            cell = SC.skey(H, P)
            sf, sa = cell_scale(Ft, cell, tr.game_date_local.to_numpy())
            Pa = predict_as(D, tr, otr, sf, sa)
            for s in JUDGED[fold]:
                k = (tr.season == s).to_numpy()
                q = season_R(Pa[k], tr[k].reset_index(drop=True), xg)
                rows.append(dict(fold=fold, season=s, arm="L1x-as", cell=cell, H=H, P=P,
                                 R_for=q["for"]["R"], for_ci=q["for"]["ci"], R_against=q["against"]["R"],
                                 against_ci=q["against"]["ci"]))
            sc = Ft[Ft.cell == cell]
            for s, g in sc.groupby("season"):
                traj.append(dict(fold=fold, cell=cell, season=s,
                                 **{f"{d}_{w}": v for d, col, u in (("for", "s_for", D["sd"][0]), ("against", "s_against", D["sd"][1]))
                                    for w, v in (("first", g[col].iloc[0] / u), ("mid", g[col].iloc[len(g) // 2] / u),
                                                 ("last", g[col].iloc[-1] / u), ("min", g[col].min() / u),
                                                 ("max", g[col].max() / u))},
                                 n_eff_last=g.n_eff.iloc[-1]))
            print(now(), f"fold {fold} {cell} done", flush=True)
    T = pd.DataFrame(rows)
    T["max_abs_logR"] = np.maximum(np.abs(np.log(T.R_for)), np.abs(np.log(T.R_against)))
    T["both_in"] = T.R_for.between(*BAND_P) & T.R_against.between(*BAND_P)
    A_ = T[T.arm == "L1x-as"]
    cs = A_.groupby("cell").agg(H=("H", "first"), P=("P", "first"), max_abs_logR=("max_abs_logR", "max"),
                                all_in=("both_in", "all"), R_for_min=("R_for", "min"), R_for_max=("R_for", "max"),
                                R_against_min=("R_against", "min"), R_against_max=("R_against", "max"))
    cs = cs.loc[[SC.skey(H, P) for H, P in SC.GRID_ORDER]]
    passers = [c for c in cs.index if cs.loc[c, "all_in"]]
    if passers:
        sel, how = passers[0], "simplest passer (larger H, then larger P)"
    else:
        sel, how = cs.max_abs_logR.idxmin(), "no passer: smallest max |log R| over both directions and all judged seasons (listed), proceed"
    H, P = int(cs.loc[sel, "H"]), int(cs.loc[sel, "P"])
    J = pd.DataFrame(traj)
    Mx = pd.DataFrame(mle)
    s0 = json.loads(V6.STEP0.read_text())
    qa = [f for f in s0["flatness"] if f["construction"] == "Qa"]
    fz = json.loads(V6.FROZEN.read_text())
    out = dict(selected=sel, H=H, P=P, rule=how, passers=passers, sd=sd_info, table=T.to_dict("records"),
               summary=cs.reset_index().to_dict("records"), trajectory=J.to_dict("records"), season_mle=Mx.to_dict("records"),
               generated=now(), elapsed_s=round(time.time() - t0))
    SELECT.write_text(json.dumps(out, indent=1, default=float))
    ck = json.loads((RES / "snap_check.json").read_text())

    def fmt_ci(v):
        return f"{v[0]:.2f}-{v[1]:.2f}"
    Tshow = T.assign(for_ci=T.for_ci.map(fmt_ci), against_ci=T.against_ci.map(fmt_ci))
    Tshow = Tshow[["fold", "season", "arm", "cell", "R_for", "for_ci", "R_against", "against_ci", "max_abs_logR", "both_in"]]
    L = ["# SL-R7 step 0 and parity analogue, (H, P) selection (Lane A7, 2026-10-21)", "",
         f"Generated {now()} ({time.time() - t0:.0f} s) by `scripts/train_shot_attribute_v7.py parity`. Committed BEFORE any "
         "fold-2 prediction. Training seasons only (fold 1: 2021-22, 2022-23; fold 2: 2021-22 to 2023-24): no test-season "
         "row, prediction or s_t value is read or printed here.", "",
         "## Construction (spec SL-R7; code `src/nhl_sim/shot_attribute/scale.py`, test `tests/test_shot_attribute_asof_scale.py`)", "",
         "- L1x-as (non-EN rows): logit = log L0s levelled (M1 K500) + the fold's FROZEN SL-R6 L1x-ot0 home / score / rest "
         "terms (score terms zero on OT rows) + (s_for,t zf + s_against,t za) x c, c the frozen quality direction. EN rows: "
         "L0s levelled. Nothing is refit.",
         f"- zf = own Qa / SD, za = opponent Qa / SD, SD over the fold's 2021-22 in-scope rows (unit only): fold 1 "
         f"{sd_info[1][0]:.5f} / {sd_info[1][1]:.5f}, fold 2 {sd_info[2][0]:.5f} / {sd_info[2][1]:.5f}.",
         "- (s_for,t, s_against,t): two-parameter MNL slope fit on every non-EN unblocked attempt dated before the game "
         "date (OT rows included, score terms zero), weights 0.5^(age/H), offset fixed; shrunk to the previous date's "
         "pair with prior precision P x the per-attempt Fisher information matrix; Newton from the previous pair; "
         "start (0, 0), 2021-22 burn-in (never judged); created_at = previous date's last drop + 6 h, asserted "
         "< puck_drop. A coordinate with no information (all-zero season-opening ratings) carries forward.",
         f"- Numerical method (labelled): window sums by exact decay recursion, each row's score / information through "
         f"its cumulant series in t (order {SC.ORDER}). Checks (`results/shot_attribute_r7/snap_check.json`): exact "
         f"direct-evaluation Newton step at 8 sampled dates x 3 cells per fold, max |diff| fold 1 "
         f"{ck['1']['exact_step_max_abs']:.1e}, fold 2 {ck['2']['exact_step_max_abs']:.1e}; series order 14 vs "
         f"{SC.ORDER}: max |diff| {max(ck[f]['order14_vs_20_max_abs'][c] for f in ('1', '2') for c in ck[f]['order14_vs_20_max_abs']):.1e}.",
         "- Parity R: D32 decile slope ratio on ES rows of that training season, deciles of the row's own as-of Qa (for) / "
         "the opponent's (against); CI = 200-resample game bootstrap. The W terms are fitted on the fold's training rows "
         "(in sample, as in G-R3's table); the response scale is as-of, so R is out of sample for the scale.", "",
         "## Step 0: the trend the as-of scale must track", "",
         "SL-R6 step 0 per-season Qa coefficients (season alone, own unlevelled L0s, free W; raw rating units; "
         "`sl_r6_step0.json`):", "",
         "| rating | 2021-22 | 2022-23 | 2023-24 | p (flat) | trend z |", "|---|---|---|---|---|---|"]
    for f in qa:
        L.append(f"| {f['rating']} | " + " | ".join(f"{b:.3f} ({s:.3f})" for b, s in zip(f["per_season"], f["se"]))
                 + f" | {f['p_het']:.3f} | {f['trend_z']:+.2f} |")
    L += ["", f"SL-R6 fixed scale (Qa x0.75, frozen): s_f {fz['s_f']:.4f}, s_a {fz['s_a']:.4f} (raw units).", "",
          "Season-alone MLE of the pair under the SL-R7 offset (frozen W of the fold, levelled L0s; P = 0; raw units = z units / SD):", "",
          Mx.to_markdown(index=False, floatfmt=".4f"), "",
          "As-of s_t over training dates, per cell and season (raw units; first / mid / last game date of the season, "
          "min / max; n_eff = summed window weight on the last date):", "",
          J.to_markdown(index=False, floatfmt=".4f"), "",
          "## Parity analogue (genuine-prior training seasons; band [0.9, 1.1] on both R)", "",
          Tshow.to_markdown(index=False, floatfmt=".4f"), "",
          "Per cell (L1x-as, all three genuine-prior season cells, both directions):", "",
          cs.to_markdown(floatfmt=".4f"), "",
          f"- **Selected: {sel} (H {H}, P {P})**: {how}. Passers: {passers or 'none'}.",
          "- The season-own-MLE rows are a post-hoc diagnostic (in sample), used for no choice.", ""]
    PARITY_DOC.write_text("\n".join(L), encoding="utf-8")
    print(Tshow.to_string(), flush=True)
    print(cs.to_string(), flush=True)
    print(now(), "selected", sel, how, flush=True)


# ---------------------------------------------------------------------------------------------------- arms
def selected():
    return json.loads(SELECT.read_text())


def shuffled_snapshot(D, cell_H, cell_P):
    """L1x-as2: the selected cell recomputed from a within-day shuffled row order (spec-identical rerun)."""
    r, off = D["r"], D["off"]
    msk, rr, A, C, zf, za, y = offset_inputs(D, r, off)
    p = np.random.default_rng(2).permutation(len(rr))
    rr2 = rr.iloc[p]
    return SC.asof_scale(rr2.game_date_local.to_numpy(), rr2["drop"].to_numpy(), A[p], C[p], y[p], zf[p], za[p],
                         cell_H, cell_P)


def arm_preds(fold, part):
    """Predictions of every arm on the fold's training ('train') or test ('test') rows."""
    D = fold_data(fold)
    S = selected()
    r, off, ntr = D["r"], D["off"], D["ntr"]
    sl = slice(0, ntr) if part == "train" else slice(ntr, len(r))
    x, ox = r.iloc[sl].reset_index(drop=True), off[sl]
    F = snapshots(fold)
    sf, sa = cell_scale(F, S["selected"], x.game_date_local.to_numpy())
    out = {"L0s": MS.l0s_levelled(D["l0s"], x, ox), "L1x": predict_ref(D, x, ox), "L1xas": predict_as(D, x, ox, sf, sa)}
    if part == "test":
        F2 = shuffled_snapshot(D, S["H"], S["P"])
        sf2, sa2 = SC.attach_scale(x.game_date_local.to_numpy(), F2)
        out["L1xas2"] = predict_as(D, x, ox, sf2, sa2)
        out["_snap_shuffle_max_abs"] = float(max(np.abs(sf2 - sf).max(), np.abs(sa2 - sa).max()))
    return D, x, ox, out


def outdir(fold):
    return RES if fold == 2 else RES / "fold1"


def cmd_insample():
    D, tr, otr, P = arm_preds(2, "train")
    xg = D["xg"]
    grp = tr.grp.to_numpy()
    xg_cls = xg[:, grp].T
    act = xg[tr.cls.to_numpy(), grp]
    st, pt = tr.st.to_numpy(), tr.ptype.to_numpy()
    cells = [(f"{MS.STATE_NAMES[s]}", st == s) for s in range(7)]
    cells += [(f"{MS.STATE_NAMES[s]} {'OT' if p_ else 'reg'}", (st == s) & (pt == p_)) for s in range(7) for p_ in (0, 1)]
    rows = []
    for scope, smask in (("all training rows", np.ones(len(tr), bool)),
                         ("excl. 2021-22 burn-in (reported)", (tr.season != FIRST).to_numpy())):
        for nm, m0 in cells:
            m = m0 & smask
            n = int(m.sum())
            if n == 0:
                continue
            base = (P["L0s"][m] * xg_cls[m]).sum(1).mean()
            rec = dict(scope=scope, stratum=nm, n=n, actual=float(act[m].mean()), L0s_vs_actual=float(base / act[m].mean() - 1))
            for a in ("L1x", "L1xas"):
                v = (P[a][m] * xg_cls[m]).sum(1).mean()
                rec[f"{a}_vs_L0s"] = float(v / base - 1)
                for k in range(3):
                    rec[f"{a}_{TIER_NAMES[k]}_pp"] = float((P[a][m][:, CLASS_TIER == k].sum(1).mean()
                                                            - P["L0s"][m][:, CLASS_TIER == k].sum(1).mean()) * 100)
            rec["gated"] = scope == "all training rows" and n >= V6.N_MIN
            rec["pass"] = (not rec["gated"]) or abs(rec["L1xas_vs_L0s"]) <= V6.TOL
            rows.append(rec)
    ok = all(x["pass"] for x in rows)
    en = np.isin(st, MS.EN_STATES)
    res = dict(fold=2, rule=f"L1x-as xG_ref per attempt within +/-{V6.TOL:.1%} of L0s in every stratum with n >= {V6.N_MIN} "
               "(state x period type, and state), all fold-2 training rows", pass_all=bool(ok), rows=rows,
               en_identical=bool(np.array_equal(P["L1xas"][en], P["L0s"][en])),
               ll_per_attempt={a: float(M.joint_ll(P[a], tr.cls.to_numpy()).mean()) for a in ("L0s", "L1x", "L1xas")})
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "insample.json").write_text(json.dumps(res, indent=1))
    print(pd.DataFrame(rows).to_string(), flush=True)
    print(now(), "EN identical", res["en_identical"], "LL/att", res["ll_per_attempt"], "PASS" if ok else "FAIL", flush=True)
    return ok


def write_preds(fold):
    D, te, ote, P = arm_preds(fold, "test")
    out = outdir(fold)
    out.mkdir(parents=True, exist_ok=True)
    te2 = te.copy()
    te2["own_r"], te2["opp_r"] = te[OC], te[PC]          # the grader buckets by the arm's own construction (Qa)
    te2.assign(**{f"off{c}": ote[:, c] for c in range(ote.shape[1])})[V6.KEEP + [f"off{c}" for c in range(ote.shape[1])]] \
        .to_parquet(out / f"fold{fold}_rows.parquet", index=False)
    info = dict(snap_shuffle_max_abs=P.pop("_snap_shuffle_max_abs"))
    for a in ARMS:
        Pa = P[a].astype(np.float32)
        if Pa.shape != (len(te), N_CLASS) or not np.allclose(Pa.sum(1), 1, atol=1e-4):
            raise ValueError(f"{a}: bad probability matrix")
        np.save(out / f"fold{fold}_pred_{label(a)}.npy", Pa)
    # the SL-R6 reference must reproduce SL-R6's prediction file (array comparison only; no metric is read)
    lab6 = hashlib.sha1(f"{V6.SALT}|L1x".encode()).hexdigest()[:8]
    f6 = (R6 if fold == 2 else R6 / "fold1") / f"fold{fold}_pred_{lab6}.npy"
    info["L1x_vs_sl_r6_file_max_abs"] = float(np.abs(np.load(f6).astype(np.float64) - P["L1x"].astype(np.float32)).max())
    info["L1xas_vs_L1xas2_max_abs"] = float(np.abs(P["L1xas"] - P["L1xas2"]).max())
    labels = {a: label(a) for a in ARMS}
    (out / "labels_sealed.json").write_text(json.dumps(labels))
    (out / "hashes.json").write_text(json.dumps(sorted(labels.values())))
    (out / "pred_info.json").write_text(json.dumps(info, indent=1))
    print(now(), f"fold {fold}: wrote {len(ARMS)} hash-labelled prediction files; {info}", flush=True)
    return D, te, P


def cmd_guard():
    Dd = RES / "fold1"
    r = pd.read_parquet(Dd / "fold1_rows.parquet")
    lab = json.loads((Dd / "labels_sealed.json").read_text())
    P = {a: np.load(Dd / f"fold1_pred_{lab[a]}.npy").astype(np.float64) for a in ("L0s", "L1xas")}
    xg = V6.xgref(1)
    grp = r.grp.to_numpy()
    xc = xg[:, grp].T
    px = {a: (P[a] * xc).sum(1) for a in P}
    rows = []

    def add(kind, cell, m, tol, gated, v):
        rows.append(dict(check=kind, cell=cell, n=int(m.sum()), value=float(v), tol=tol,
                         status=("reported (EN, gates at stage 8, D28)" if cell in EN else
                                 ("UNDERPOWERED" if not gated else ("PASS" if abs(v) <= tol else "FAIL")))))
    allm = np.ones(len(r), bool)
    add("xG rel", "overall", allm, 0.02, True, px["L1xas"].mean() / px["L0s"].mean() - 1)
    for g in range(5):
        m = grp == g
        add("xG rel", GROUP_NAMES[g], m, 0.03, m.sum() >= 2000, px["L1xas"][m].mean() / px["L0s"][m].mean() - 1)
    mon = pd.to_datetime(r.game_date_local).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = mon == mo
        add("xG rel", mo, m, 0.04, r.game_id[m].nunique() >= 100, px["L1xas"][m].mean() / px["L0s"][m].mean() - 1)
    for nm, m in [("overall", allm)] + [(GROUP_NAMES[g], grp == g) for g in range(5)]:
        for k in range(3):
            d = (P["L1xas"][m][:, CLASS_TIER == k].sum(1).mean() - P["L0s"][m][:, CLASS_TIER == k].sum(1).mean()) * 100
            add(f"tier {TIER_NAMES[k]} pp", nm, m, 1.5, nm == "overall" or m.sum() >= 2000, d)
    for k in range(N_TYPE):
        d = (P["L1xas"][:, CLASS_TYPE == k].sum(1).mean() - P["L0s"][:, CLASS_TYPE == k].sum(1).mean()) * 100
        add(f"type {k} pp", "overall", allm, 1.5, True, d)
    T = pd.DataFrame(rows)
    ok = bool((T.status != "FAIL").all())
    print(T.to_string(float_format=lambda v: f"{v:+.5f}"), flush=True)
    act = xg[r.cls.to_numpy(), grp]
    lvl = []
    for arm in ("L0s", "L1xas"):
        pred = px[arm]
        rec = dict(arm=arm, xg_all=float(pred.mean() / act.mean() - 1))
        for g in range(5):
            m = grp == g
            rec[f"xg_{GROUP_NAMES[g]}"] = float(pred[m].mean() / act[m].mean() - 1)
        R = V6.resp(pred, act, r, "own_r", "opp_r", n_boot=200)
        rec.update(R_for=R["for"]["R"], R_against=R["against"]["R"])
        lvl.append(rec)
    print(pd.DataFrame(lvl).to_string(float_format=lambda v: f"{v:+.4f}"), flush=True)
    g = dict(guard_basis="L1x-as minus L0s (D28)", guard_pass=ok, rows=rows,
             max_abs_xg_rel=float(T[T.check == "xG rel"].value.abs().max()),
             max_abs_tier_pp=float(T[T.check.str.startswith("tier")].value.abs().max()), level_read=lvl)
    (Dd / "guard.json").write_text(json.dumps(g, indent=1, default=float))
    T.to_csv(Dd / "guard.csv", index=False)
    print(now(), "D28 guard (L1x-as minus L0s):", "PASS" if ok else "FAIL", flush=True)
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["snap", "parity", "insample", "fold1", "guard", "pred2"])
    a = ap.parse_args()
    print(now(), "start", a.cmd, flush=True)
    if a.cmd == "snap":
        cmd_snap()
    elif a.cmd == "parity":
        cmd_parity()
    elif a.cmd == "insample":
        if not cmd_insample():
            print(now(), "IN-SAMPLE CHECK FAILED: stop; nothing on fold 2 is read", flush=True)
            sys.exit(3)
    elif a.cmd == "fold1":
        write_preds(1)
    elif a.cmd == "guard":
        if not cmd_guard():
            print(now(), "D28 GUARD FAILED: stop; nothing on fold 2 is read", flush=True)
            sys.exit(4)
    else:
        if not json.loads((RES / "insample.json").read_text())["pass_all"]:
            raise SystemExit("in-sample check did not pass; fold 2 is not predicted")
        g1 = RES / "fold1" / "guard.json"
        if not g1.exists() or not json.loads(g1.read_text()).get("guard_pass"):
            raise SystemExit("fold-1 D28 guard has not passed; fold 2 is not predicted")
        write_preds(2)
    print(now(), "done", a.cmd, flush=True)
