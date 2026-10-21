"""INV-78 (Lane D2, 2026-10-21): second-pass diagnosis of the 55:00 margin compression. DIAGNOSIS ONLY: no fix, no
tuning, no table change; every counterfactual is a re-weighting of recorded sim rates, labelled DIAGNOSTIC.

Inputs (nothing from 2025-26 is read):
  sim   results/diag_margin_inv78_v1/f1/rec_*.npz   fold 1 (2023-24), default set from the fold-1 tables, 200 seeds
        results/diag_margin_inv78_v1/f2/rec_*.npz   fold 2 (2024-25), default set (= Lane E4's c1s arm, checked by cmp)
        results/engine_defaults_v2_loop/{c1s,sap}  Lane E4 (B1a-as, OT level on); results/goal_r4_loop_v1/{c1s,sap}
        Lane G4 (block B0, OT level off): goal logs only; exposure is reconstructed from the goal log (validated
        against the recorded exposure of f2)
  real  verified_finals_v2, events_<season> (via Lane D1's diag_margin_inv71_grade_v1.load_real),
        attempt_rows_v1_<season> (exposure / attempts / goals by period x team-view state x score bucket),
        strength_state/type_rows_v2 (penalty events by period x penalised team's score bucket)

    diag_margin_inv78_grade_v1.py   -> results/diag_margin_inv78_v1/grade.json + printed tables
"""
import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

OUT = ROOT / "results" / "diag_margin_inv78_v1"
SEASON = {1: 20232024, 2: 20242025}
SNAP_T = (1200, 2400, 3300, 3600)
SNAP_L = ("20:00", "40:00", "55:00", "60:00")
BUCK = ["trail2+", "trail1", "tied", "lead1", "lead2+"]
B_OF_SC7 = np.array([0, 0, 1, 2, 3, 4, 4])
B_OF_SC5 = np.arange(5)
SWAP = np.array([0, 2, 1, 3, 4])
LOOPS = {"E4 c1s (B1a-as)": ROOT / "results/engine_defaults_v2_loop/c1s", "E4 sap (B1a-as)": ROOT / "results/engine_defaults_v2_loop/sap",
         "G4 c1s (B0)": ROOT / "results/goal_r4_loop_v1/c1s", "G4 sap (B0)": ROOT / "results/goal_r4_loop_v1/sap"}
J = {}


def pr(*a):
    print(*a, flush=True)


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tv_st(own, opp):
    return np.where(own > opp, 1, np.where(own < opp, 2, np.where(own == 5, 0, np.where(own == 4, 3, 4))))


# ------------------------------------------------------------------------------------------------- sim loading
def load_rec(d):
    fs = sorted(Path(d).glob("rec_*.npz"))
    games, rows, goals, off = None, [], [], 0
    agg = {}
    for f in fs:
        z = np.load(f)
        games = z["game_id"] if games is None else games
        assert (z["game_id"] == games).all()
        n = len(z["seed"])
        dct = dict(gi=z["game_idx"], seed=z["seed"], h=z["score"][:, 0].astype(int), a=z["score"][:, 1].astype(int))
        for k, lab in enumerate(SNAP_L):
            dct[f"d{lab}"] = (z["snap"][k, :, 0] - z["snap"][k, :, 1]).astype(int)
        rows.append(pd.DataFrame(dct))
        g = dict(sim=z["g_idx"] + off, team=z["g_team"].astype(int), t=z["g_t"].astype(int), ph=z["g_pre"][:, 0].astype(int),
                 pa=z["g_pre"][:, 1].astype(int))
        if "g_sk" in z:
            g.update(skh=z["g_sk"][:, 0].astype(int), ska=z["g_sk"][:, 1].astype(int))
        goals.append(pd.DataFrame(g))
        for k in ("att", "expo", "pen", "coinc"):
            if k in z:
                agg[k] = agg.get(k, 0) + z[k]
        off += n
    S = pd.concat(rows, ignore_index=True)
    Gl = pd.concat(goals, ignore_index=True)
    Gl["gi"] = S.gi.to_numpy()[Gl.sim.to_numpy()]
    return games, S, Gl, agg


def expo_from_goals(N, Gl, T_end=3600):
    """(N, 3, 7) regulation seconds per sim in (period, home-view sc7), from the goal log: second t of a goal belongs to
    the pre-goal score (the engine counts exposure before the event)."""
    g = Gl[Gl.t < T_end].sort_values(["sim", "t"], kind="stable")
    sim = g.sim.to_numpy()
    e = g.t.to_numpy() + 1
    dlt = np.where(g.team.to_numpy() == 0, 1, -1)
    cum = np.zeros(len(g), np.int64)
    # cumulative home diff within each sim
    c = np.cumsum(dlt)
    first = np.r_[True, sim[1:] != sim[:-1]]
    base = np.where(first, c - dlt, 0)
    base = np.maximum.accumulate(np.where(first, np.arange(len(g)), 0))
    cum = c - (c[base] - dlt[base])                    # diff after event k within its sim
    pre = cum - dlt
    out = np.zeros((N, 3, 7))
    start = np.where(first, 0, np.r_[0, e[:-1]])
    # segments ending at each event (pre-state), plus the final segment of each sim
    last = np.r_[sim[1:] != sim[:-1], True]
    seg_s = np.concatenate([start, e[last]])
    seg_e = np.concatenate([e, np.full(int(last.sum()), T_end)])
    seg_d = np.concatenate([pre, cum[last]])
    seg_i = np.concatenate([sim, sim[last]])
    # sims with no goal: one segment at diff 0
    nog = np.setdiff1d(np.arange(N), np.unique(sim))
    seg_s = np.concatenate([seg_s, np.zeros(len(nog), np.int64)])
    seg_e = np.concatenate([seg_e, np.full(len(nog), T_end)])
    seg_d = np.concatenate([seg_d, np.zeros(len(nog), np.int64)])
    seg_i = np.concatenate([seg_i, nog])
    sc = np.clip(seg_d, -3, 3) + 3
    for p in range(3):
        ov = np.clip(np.minimum(seg_e, 1200 * (p + 1)) - np.maximum(seg_s, 1200 * p), 0, None)
        np.add.at(out, (seg_i, np.full(len(seg_i), p), sc), ov)
    return out


def team_view_goals(Gl):
    th = Gl.team.to_numpy() == 0
    d = np.where(th, Gl.ph - Gl.pa, Gl.pa - Gl.ph)
    return np.clip(d, -3, 3) + 3, np.minimum(Gl.t.to_numpy() // 1200, 3)


def rates_from_loop(S, Gl, mask):
    """lambda (3 periods, 5 buckets) goals per team-hour, regulation, all states, sims in mask."""
    N = len(S)
    E = expo_from_goals(N, Gl)[mask].sum(0)                         # (3, 7) home view
    Etv = E + E[:, ::-1]                                            # both teams' views
    sc, p = team_view_goals(Gl)
    m = mask[Gl.sim.to_numpy()] & (Gl.t.to_numpy() < 3600)
    G = np.zeros((3, 7))
    np.add.at(G, (p[m], sc[m]), 1)
    e5 = np.stack([Etv[:, B_OF_SC7 == b].sum(1) for b in range(5)], 1)
    g5 = np.stack([G[:, B_OF_SC7 == b].sum(1) for b in range(5)], 1)
    return g5 / e5 * 3600, g5, e5


# ------------------------------------------------------------------------------------------------- Markov chain
MMAX = 12


def chain(lam, T_end=3300, snaps=(1200, 2400, 3300), lam_t=None):
    """INV-71's symmetric margin chain (one-second steps). lam (3, 5) per team-hour; lam_t: optional callable t ->
    (5,) rates (time-varying)."""
    m = np.arange(-MMAX, MMAX + 1)
    P = np.zeros(len(m))
    P[MMAX] = 1.0
    out = {}
    for t in range(T_end):
        L = (lam[min(t // 1200, 2)] if lam_t is None else lam_t(t)) / 3600.0
        ph = np.where(m > 0, np.where(m == 1, L[3], L[4]), np.where(m < 0, np.where(m == -1, L[1], L[0]), L[2]))
        pa = np.where(m > 0, np.where(m == 1, L[1], L[0]), np.where(m < 0, np.where(m == -1, L[3], L[4]), L[2]))
        new = P * (1 - ph - pa)
        new[1:] += (P * ph)[:-1]
        new[:-1] += (P * pa)[1:]
        P = new
        if t + 1 in snaps:
            out[t + 1] = P.copy()
    return out


def tie(P):
    return float(P[MMAX])


# ------------------------------------------------------------------------------------------------- real loading
def real(fold, games):
    D1 = load_mod(f"inv71g_{fold}", "diag_margin_inv71_grade_v1.py")
    D1.SEASON = SEASON[fold]
    F, g, e = D1.load_real(games)
    return D1, F, g


def real_rates(fold, F, rs_only=True):
    ar = pd.read_parquet(ROOT / f"data/processed/shot_attempt/attempt_rows_v1_{SEASON[fold]}.parquet",
                         columns=["game_id", "game_type", "period", "st", "sc", "exposure_s", "y", "y_goal", "is_home", "t0"])
    ar = ar[(ar.st <= 4) & ar.game_id.isin(F.game_id[F.pbp_ok])]
    if rs_only:
        ar = ar[ar.game_type == 2]
    return ar


# ================================================================================================== PART 1: G5b by fold
def part1(fold, games, S, F, g):
    pr(f"\n== PART 1, fold {fold} ({SEASON[fold]}): |margin| at 20:00 / 40:00 / 55:00 / 60:00, RS, pull off")
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    n = int(rs.sum())
    sm = rs[S.gi.to_numpy()]
    res = {}
    for T, lab in zip(SNAP_T, SNAP_L):
        ds = S[f"d{lab}"].to_numpy()[sm]
        ab = np.minimum(np.abs(ds), 3)
        sim = [float((ab == k).mean()) for k in range(4)]
        row = dict(sim=sim, n_real=n)
        for name, drop in (("real_all", None), ("real_no_gout", "g_out")):
            m = g.game_time_s < T
            if drop:
                m &= ~g[drop]
            x = g[m].groupby(["game_id", "home_sc"]).size().unstack(fill_value=0).reindex(F.game_id, fill_value=0)
            dr = (x.get(True, 0) - x.get(False, 0)).to_numpy()[rs]
            ar_ = np.minimum(np.abs(dr), 3)
            row[name] = [float((ar_ == k).mean()) for k in range(4)]
        r0 = row["real_no_gout"][0]
        row["tie_se"] = float(np.sqrt(r0 * (1 - r0) / n))
        row["gap_pp"] = [100 * (a - b) for a, b in zip(sim, row["real_no_gout"])]
        row["tie_gap_se"] = (sim[0] - r0) / row["tie_se"]
        res[lab] = row
        pr(f"  {lab}: sim {np.round(sim, 4)}  real(no g-out) {np.round(row['real_no_gout'], 4)}  "
           f"gap pp {np.round(row['gap_pp'], 2)}  tie {row['tie_gap_se']:+.2f} SE (SE {100 * row['tie_se']:.2f} pp)")
    J[f"part1_f{fold}"] = res
    return res


def tie_profile(fold, S, Gl, F, g, step=300):
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    sm = rs[S.gi.to_numpy()]
    out = []
    gsim = Gl[["sim", "team", "t"]]
    N = len(S)
    for T in range(step, 3301, step):
        x = gsim[gsim.t < T]
        h = np.bincount(x.sim[x.team == 0], minlength=N)
        a = np.bincount(x.sim[x.team == 1], minlength=N)
        ts = float(((h - a)[sm] == 0).mean())
        m = (g.game_time_s < T) & ~g.g_out
        y = g[m].groupby(["game_id", "home_sc"]).size().unstack(fill_value=0).reindex(F.game_id, fill_value=0)
        dr = (y.get(True, 0) - y.get(False, 0)).to_numpy()[rs]
        tr = float((dr == 0).mean())
        out.append(dict(t=T, sim=ts, real=tr, gap_pp=100 * (ts - tr), se_pp=100 * np.sqrt(tr * (1 - tr) / rs.sum())))
    return out


# ================================================================================================== PART 2: period origin
def part2(fold, games, S, Gl, agg, F):
    pr(f"\n== PART 2, fold {fold}: by period x team-view score bucket (RS + PO, all games; non-EN states)")
    ar = real_rates(fold, F, rs_only=False)
    ar["p"] = np.minimum(ar.period, 4) - 1
    expo = agg["expo"].astype(float)                       # (4, 5 st_h, 7 sc_h)
    ex_tv = expo + expo[:, SWAP][:, :, ::-1]               # team view, both teams (4, 5, 7)
    att_tv = agg["att"].sum(1).astype(float)               # (4, 5, 7)
    sc, p = team_view_goals(Gl)
    th = Gl.team.to_numpy() == 0
    st = tv_st(np.where(th, Gl.skh, Gl.ska), np.where(th, Gl.ska, Gl.skh))
    gsim = np.zeros((4, 5, 7))
    np.add.at(gsim, (p, st, sc), 1)
    R = {k: np.zeros((4, 5, 7)) for k in ("e", "a", "g")}
    for k, col in (("e", "exposure_s"), ("a", "y"), ("g", "y_goal")):
        s = ar.groupby(["p", "st", "sc"])[col].sum()
        for (pp, ss, cc), v in s.items():
            R[k][pp, ss, cc] = v
    # penalties: sim (4, 2 team, 7 home-view sc, 3 kind) -> penalised team view; real type_rows (st <= 4)
    pen = agg["pen"].sum(3).astype(float)                  # (4, 2, 7)
    pen_tv = pen[:, 0, :] + pen[:, 1, ::-1]                 # penalised team's view sc7
    coin = agg["coinc"].astype(float)                       # (4, 7) home view; |margin| symmetric
    coin_tv = coin + coin[:, ::-1]
    tr = pd.read_parquet(ROOT / "data/processed/strength_state/type_rows_v2.parquet")
    tr = tr[(tr.season == SEASON[fold]) & tr.game_id.isin(F.game_id[F.pbp_ok]) & (tr.st <= 4)]
    tr["p"] = np.minimum(tr.period, 4) - 1
    rpen = np.zeros((4, 5))
    rco = np.zeros((4, 5))
    for (pp, cc), v in tr[tr.cls != "coincidental"].groupby(["p", "sc"]).size().items():
        rpen[pp, cc] = v
    for (pp, cc), v in tr[tr.cls == "coincidental"].groupby(["p", "sc"]).size().items():
        rco[pp, cc] = v
    res = {}

    def b5(x):                                             # (..., 7) -> (..., 5)
        return np.stack([x[..., B_OF_SC7 == b].sum(-1) for b in range(5)], -1)
    for plab, ps in (("P1", [0]), ("P2", [1]), ("P3", [2]), ("all reg", [0, 1, 2])):
        se, re_ = b5(ex_tv[ps].sum((0, 1))), b5(R["e"][ps].sum((0, 1)))
        sa, ra = b5(att_tv[ps].sum((0, 1))), b5(R["a"][ps].sum((0, 1)))
        sg, rg = b5(gsim[ps].sum((0, 1))), b5(R["g"][ps].sum((0, 1)))
        sg5, rg5 = b5(gsim[ps][:, 0].sum(0)), b5(R["g"][ps][:, 0].sum(0))
        se5, re5 = b5(ex_tv[ps][:, 0].sum(0)), b5(R["e"][ps][:, 0].sum(0))
        spp, rpp = b5(ex_tv[ps][:, 1].sum(0)), b5(R["e"][ps][:, 1].sum(0))
        spk, rpk = b5(ex_tv[ps][:, 2].sum(0)), b5(R["e"][ps][:, 2].sum(0))
        sgpp, rgpp = b5(gsim[ps][:, 1].sum(0)), b5(R["g"][ps][:, 1].sum(0))
        spen, rpn = b5(pen_tv[ps].sum(0)), rpen[ps].sum(0)
        sco, rcn = b5(coin_tv[ps].sum(0)), rco[ps].sum(0)
        row = dict(
            time_share_sim=(se / se.sum()).tolist(), time_share_real=(re_ / re_.sum()).tolist(),
            att60_sim=(sa / se * 3600).tolist(), att60_real=(ra / re_ * 3600).tolist(),
            g60_sim=(sg / se * 3600).tolist(), g60_real=(rg / re_ * 3600).tolist(), g_real_n=rg.tolist(),
            g60_5v5_sim=(sg5 / se5 * 3600).tolist(), g60_5v5_real=(rg5 / re5 * 3600).tolist(),
            gpa_sim=(sg / sa).tolist(), gpa_real=(rg / ra).tolist(),
            pp_share_sim=(spp / se).tolist(), pp_share_real=(rpp / re_).tolist(),
            pk_share_sim=(spk / se).tolist(), pk_share_real=(rpk / re_).tolist(),
            ppg60pp_sim=(sgpp / spp * 3600).tolist(), ppg60pp_real=(rgpp / rpp * 3600).tolist(), ppg_real_n=rgpp.tolist(),
            pen_taken60_sim=(spen / se * 3600).tolist(), pen_taken60_real=(rpn / re_ * 3600).tolist(), pen_real_n=rpn.tolist(),
            coinc60_sim=(sco / se * 3600).tolist(), coinc60_real=(rcn / re_ * 3600).tolist())
        res[plab] = row
        pr(f"-- fold {fold} {plab}  buckets {BUCK}")
        for k, lab in (("att60", "att/60"), ("g60", "goals/60"), ("g60_5v5", "5v5 g/60"), ("gpa", "goals/att"),
                       ("pen_taken60", "pen taken/60"), ("pp_share", "PP time share"), ("pk_share", "PK time share"),
                       ("ppg60pp", "PP goals/PP-hr"), ("coinc60", "coinc/60")):
            s_, r_ = np.array(row[f"{k}_sim"]), np.array(row[f"{k}_real"])
            pr(f"   {lab:15s} sim {np.round(s_, 4)}  real {np.round(r_, 4)}  s/r {np.round(s_ / r_, 3)}")
        pr(f"   real goals n {rg.astype(int)}  real pen n {rpn.astype(int)}  real PP goals n {rgpp.astype(int)}")
    J[f"part2_f{fold}"] = res
    return res


def team_std_oe(fold, games, S, Gl, F):
    """Team-standardised goal O/E by bucket (tied = 1), regulation, RS + PO, from reconstructed sim exposure."""
    N = len(S)
    E = expo_from_goals(N, Gl)                              # (N, 3, 7) home view
    Eh = E.sum(1)
    Ea = Eh[:, ::-1]
    sc, p = team_view_goals(Gl)
    m = Gl.t.to_numpy() < 3600
    th = Gl.team.to_numpy() == 0
    Yh, Ya = np.zeros((N, 7)), np.zeros((N, 7))
    np.add.at(Yh, (Gl.sim.to_numpy()[m & th], sc[m & th]), 1)
    np.add.at(Ya, (Gl.sim.to_numpy()[m & ~th], sc[m & ~th]), 1)
    fi = F.set_index("game_id")
    gid = games[S.gi.to_numpy()]
    ok = fi.pbp_ok.loc[gid].to_numpy()
    th_, ta_ = fi.home.loc[gid].to_numpy(), fi.away.loc[gid].to_numpy()

    def oe(teams, Ex, Y):
        df, y = pd.DataFrame(Ex), pd.DataFrame(Y)
        rate = y.sum(1).groupby(teams).sum() / df.sum(1).groupby(teams).sum()
        Ee = df.mul(rate.loc[teams].to_numpy(), axis=0).sum(0).to_numpy()
        O = y.sum(0).to_numpy()
        o5 = np.array([O[B_OF_SC7 == b].sum() for b in range(5)])
        e5 = np.array([Ee[B_OF_SC7 == b].sum() for b in range(5)])
        r = o5 / e5
        return (r / r[2]).tolist()
    sim = oe(np.concatenate([th_[ok], ta_[ok]]), np.vstack([Eh[ok], Ea[ok]]), np.vstack([Yh[ok], Ya[ok]]))
    ar = real_rates(fold, F, rs_only=False)
    ar = ar[ar.period <= 3]
    ar["tm"] = np.where(ar.is_home == 1, fi.home.loc[ar.game_id].to_numpy(), fi.away.loc[ar.game_id].to_numpy())
    rate = ar.groupby("tm").y_goal.sum() / ar.groupby("tm").exposure_s.sum()
    Ee = (ar.exposure_s * rate.loc[ar.tm].to_numpy()).groupby(ar.sc).sum().reindex(range(7), fill_value=0).to_numpy()
    O = ar.groupby("sc").y_goal.sum().reindex(range(7), fill_value=0).to_numpy()
    o5 = np.array([O[B_OF_SC7 == b].sum() for b in range(5)])
    e5 = np.array([Ee[B_OF_SC7 == b].sum() for b in range(5)])
    r = o5 / e5
    real_ = (r / r[2]).tolist()
    se = (np.sqrt(1 / np.maximum(o5, 1) + 1 / o5[2]) * (r / r[2])).tolist()
    return dict(sim=sim, real=real_, real_se=se, z=[(a - b) / s if s > 0 else 0 for a, b, s in zip(sim, real_, se)])


def markov_locate(fold, S, Gl, F):
    """Chain on the sim's and the real regulation RS rates (period x bucket), then swap the real rate into one
    (period, bucket group) cell at a time: the change in the 55:00 tie locates the cells that carry the excess."""
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    sm = rs[S.gi.to_numpy()]
    lam_s, g5, e5 = rates_from_loop(S, Gl, sm)
    ar = real_rates(fold, F, rs_only=True)
    ar["p"] = np.minimum(ar.period, 4) - 1
    ar = ar[ar.p <= 2]
    ar["b"] = B_OF_SC7[ar.sc.to_numpy()]
    rg = ar.groupby(["p", "b"]).y_goal.sum().unstack().reindex(columns=range(5)).to_numpy()
    re_ = ar.groupby(["p", "b"]).exposure_s.sum().unstack().reindex(columns=range(5)).to_numpy()
    lam_r = rg / re_ * 3600
    cs, cr = chain(lam_s), chain(lam_r)
    base = tie(cs[3300])
    out = dict(lam_sim=lam_s.tolist(), lam_real=lam_r.tolist(), real_goals=rg.tolist(),
               chain_sim={k: tie(v) for k, v in cs.items()}, chain_real={k: tie(v) for k, v in cr.items()}, swaps={})
    pr(f"\n== PART 2 Markov location, fold {fold} (RS, regulation; rates per team-hour by period x bucket)")
    pr(f"   lam sim  {np.round(lam_s, 3).tolist()}")
    pr(f"   lam real {np.round(lam_r, 3).tolist()}  (real goals {rg.astype(int).tolist()})")
    pr(f"   chain tie 20/40/55: sim {[round(tie(cs[t]), 4) for t in (1200, 2400, 3300)]}  real {[round(tie(cr[t]), 4) for t in (1200, 2400, 3300)]}")
    gap = base - tie(cr[3300])
    for p in range(3):
        for glab, idx in (("trailing", [0, 1]), ("tied", [2]), ("leading", [3, 4]), ("all", [0, 1, 2, 3, 4])):
            lam = lam_s.copy()
            lam[p, idx] = lam_r[p, idx]
            t55 = tie(chain(lam)[3300])
            out["swaps"][f"P{p + 1} {glab}"] = dict(tie55=t55, d55=t55 - base, share=(base - t55) / gap if gap else None)
            pr(f"   swap real P{p + 1} {glab:9s}: 55:00 tie {t55:.4f} (change {t55 - base:+.4f}, share of chain gap {(base - t55) / gap:+.2f})")
    out["chain_gap55"] = gap
    return out


# ================================================================================================== PART 3: chain vs loop
def part3(F2, g2):
    pr("\n== PART 3: INV-71 chain vs the wired loops (fold 2, RS)")
    games0 = None
    res = {}
    rs = ((F2.gtype == 2) & F2.pbp_ok).to_numpy()
    for name, d in LOOPS.items():
        games, S, Gl, _ = load_rec(d)
        games0 = games if games0 is None else games0
        assert (games == games0).all()
        sm = rs[S.gi.to_numpy()]
        lam, g5, e5 = rates_from_loop(S, Gl, sm)
        c = chain(lam)
        obs = {lab: float((S[f"d{lab}"].to_numpy()[sm] == 0).mean()) for lab in ("20:00", "40:00", "55:00")}
        res[name] = dict(lam=lam.tolist(), chain={k: tie(v) for k, v in c.items()}, obs=obs, n_sims=int(sm.sum()))
        pr(f"  {name:18s} obs tie 20/40/55 {[round(obs[k], 4) for k in obs]}  chain {[round(tie(c[t]), 4) for t in (1200, 2400, 3300)]}")
        pr(f"  {'':18s} lam P1 {np.round(lam[0], 3)} P2 {np.round(lam[1], 3)} P3 {np.round(lam[2], 3)}")
    J["part3_loops"] = res
    return res


def goal_clustering(S, Gl, F, g, rs_mask_sim):
    """Within-game dependence the chain ignores: share of goals followed by another goal within 120 s, by the same
    team and by the other team (regulation, RS, pre-55:00), sim vs real (no goalie-out goals)."""
    def stats(df, key):
        df = df.sort_values([key, "t"])
        same_game = df[key].to_numpy()[1:] == df[key].to_numpy()[:-1]
        dt = df.t.to_numpy()[1:] - df.t.to_numpy()[:-1]
        same_team = df.tm.to_numpy()[1:] == df.tm.to_numpy()[:-1]
        k = same_game & (dt <= 120)
        n = len(df)
        return dict(n_goals=int(n), next_within120_same=float((k & same_team).sum() / n),
                    next_within120_other=float((k & ~same_team).sum() / n))
    gs = Gl[(Gl.t < 3300) & rs_mask_sim[Gl.sim.to_numpy()]].rename(columns={"team": "tm"})
    rs = ((F.gtype == 2) & F.pbp_ok)
    gr = g[(g.game_time_s < 3300) & ~g.g_out & g.game_id.isin(F.game_id[rs])].copy()
    gr = gr.assign(t=gr.game_time_s, tm=(~gr.home_sc).astype(int))
    return dict(sim=stats(gs, "sim"), real=stats(gr, "game_id"))


def lead_persistence(S, Gl, F, g, rs_mask_sim):
    """E[goal differential 20:00-55:00, from the 20:00 leader's side | 20:00 |margin| = 1], sim vs real: the chain's
    score-effect-only dependence vs team heterogeneity."""
    out = {}
    sm = rs_mask_sim
    d20 = S["d20:00"].to_numpy()
    d55 = S["d55:00"].to_numpy()
    for k in (1, 2):
        m = sm & (np.abs(d20) == k)
        out[f"sim |m20|={k}"] = dict(n=int(m.sum()), mean_gain=float((np.sign(d20[m]) * (d55[m] - d20[m])).mean()),
                                     p_tied55=float((d55[m] == 0).mean()))
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()

    def diff_at(T):
        x = g[(g.game_time_s < T) & ~g.g_out].groupby(["game_id", "home_sc"]).size().unstack(fill_value=0).reindex(F.game_id, fill_value=0)
        return (x.get(True, 0) - x.get(False, 0)).to_numpy()
    r20, r55 = diff_at(1200), diff_at(3300)
    for k in (1, 2):
        m = rs & (np.abs(r20) == k)
        gain = np.sign(r20[m]) * (r55[m] - r20[m])
        out[f"real |m20|={k}"] = dict(n=int(m.sum()), mean_gain=float(gain.mean()), se=float(gain.std() / np.sqrt(m.sum())),
                                      p_tied55=float((r55[m] == 0).mean()))
    return out


def stratified_chain(fold, S, Gl, F, games, nq=3):
    """Heterogeneity check: split games into terciles of the sim's own game-mean regulation goal differential
    (|E[home - away]|, a pregame quantity of the engine's tables), chain per stratum on that stratum's rates
    (sim and real), and average. The pooled chain assumes one league rate for every game."""
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    sm = rs[S.gi.to_numpy()]
    gm = pd.Series(S.h.to_numpy() - S.a.to_numpy()).groupby(S.gi.to_numpy()).mean()
    spread = np.abs(gm.reindex(range(len(games))).to_numpy())
    q = np.quantile(spread[rs], np.linspace(0, 1, nq + 1))
    strat = np.clip(np.searchsorted(q, spread, side="right") - 1, 0, nq - 1)
    ar = real_rates(fold, F, rs_only=True)
    ar["p"] = np.minimum(ar.period, 4) - 1
    ar = ar[ar.p <= 2]
    ar["b"] = B_OF_SC7[ar.sc.to_numpy()]
    gpos = pd.Series(np.arange(len(games)), index=games)
    ar["s"] = strat[gpos.loc[ar.game_id].to_numpy()]
    # the real chain must be in the "leader view": stratum rates by bucket keep the team-strength mix of that stratum
    out = dict(strata=[])
    ws, wr, ts, tr, os_, or_ = [], [], [], [], [], []
    d55s = S["d55:00"].to_numpy()
    for k in range(nq):
        mk_games = (strat == k) & rs
        msim = sm & (strat[S.gi.to_numpy()] == k)
        lam_s, _, _ = rates_from_loop(S, Gl, msim)
        x = ar[ar.s == k]
        rg = x.groupby(["p", "b"]).y_goal.sum().unstack().reindex(columns=range(5)).to_numpy()
        re_ = x.groupby(["p", "b"]).exposure_s.sum().unstack().reindex(columns=range(5)).to_numpy()
        lam_r = rg / re_ * 3600
        cs, cr = tie(chain(lam_s)[3300]), tie(chain(lam_r)[3300])
        out["strata"].append(dict(k=k, n_games=int(mk_games.sum()), chain_sim=cs, chain_real=cr,
                                  obs_sim=float((d55s[msim] == 0).mean())))
        ws.append(mk_games.sum())
        ts.append(cs)
        tr.append(cr)
        os_.append(float((d55s[msim] == 0).mean()))
    w = np.array(ws, float) / np.sum(ws)
    out["mix_chain_sim"], out["mix_chain_real"], out["mix_obs_sim"] = float(w @ ts), float(w @ tr), float(w @ os_)
    return out


def p3_split_chain(fold, S, Gl, F):
    """Time-homogeneity check within P3: rates for 40:00-55:00 only (the chain's horizon) vs the whole P3."""
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    sm = rs[S.gi.to_numpy()]
    lam_s, _, _ = rates_from_loop(S, Gl, sm)
    # sim P3 40-55 rates
    N = len(S)
    Gx = Gl[Gl.t < 3300]
    E = expo_from_goals(N, Gx, T_end=3300)[sm].sum(0)[2]
    Etv = E + E[::-1]
    sc, p = team_view_goals(Gx)
    m = sm[Gx.sim.to_numpy()] & (p == 2)
    G = np.bincount(sc[m], minlength=7).astype(float)
    lam_s55 = np.array([G[B_OF_SC7 == b].sum() for b in range(5)]) / np.array([Etv[B_OF_SC7 == b].sum() for b in range(5)]) * 3600
    ar = real_rates(fold, F, rs_only=True)
    ar["b"] = B_OF_SC7[ar.sc.to_numpy()]
    x = ar[(ar.period == 3) & (ar.t0 < 3300)]
    lam_r55 = (x.groupby("b").y_goal.sum() / x.groupby("b").exposure_s.sum() * 3600).reindex(range(5)).to_numpy()
    y = ar[(ar.period == 3) & (ar.t0 >= 3300)]
    lam_r60 = (y.groupby("b").y_goal.sum() / y.groupby("b").exposure_s.sum() * 3600).reindex(range(5)).to_numpy()
    xr = ar[ar.period <= 3]
    xr = xr.assign(p=xr.period - 1)
    lam_r = (xr.groupby(["p", "b"]).y_goal.sum() / xr.groupby(["p", "b"]).exposure_s.sum() * 3600).unstack().to_numpy()
    lr2 = lam_r.copy()
    lr2[2] = lam_r55
    ls2 = lam_s.copy()
    ls2[2] = lam_s55
    return dict(lam_sim_p3=lam_s[2].tolist(), lam_sim_p3_4055=lam_s55.tolist(), lam_real_p3=lam_r[2].tolist(),
                lam_real_p3_4055=lam_r55.tolist(), lam_real_p3_5560_nonEN=lam_r60.tolist(),
                chain_sim_p3all=tie(chain(lam_s)[3300]), chain_sim_p3_4055=tie(chain(ls2)[3300]),
                chain_real_p3all=tie(chain(lam_r)[3300]), chain_real_p3_4055=tie(chain(lr2)[3300]))


def main():
    J["validation"] = {}
    F2 = None
    for fold in (1, 2):
        games, S, Gl, agg = load_rec(OUT / f"f{fold}")
        pr(f"\nfold {fold}: sims {len(S):,} seeds {S.seed.nunique()} goals {len(Gl):,}")
        # reconstruction check: exposure from the goal log == recorded exposure (regulation, all states)
        E = expo_from_goals(len(S), Gl).sum(0)
        Er = agg["expo"][:3].sum(1)
        J["validation"][f"f{fold}_expo_reconstruction_max_abs"] = float(np.abs(E - Er).max())
        pr(f"   exposure reconstruction vs recorded: max |diff| {np.abs(E - Er).max():.0f} s of {Er.sum():,.0f}")
        D1, F, g = real(fold, games)
        part1(fold, games, S, F, g)
        J[f"profile_f{fold}"] = tie_profile(fold, S, Gl, F, g)
        pr("   tie-gap profile (pp, RS, no goalie-out goals):",
           [(r["t"] // 60, round(r["gap_pp"], 2)) for r in J[f"profile_f{fold}"]])
        part2(fold, games, S, Gl, agg, F)
        J[f"oe_f{fold}"] = team_std_oe(fold, games, S, Gl, F)
        pr(f"   team-std goal O/E sim {np.round(J[f'oe_f{fold}']['sim'], 3)} real {np.round(J[f'oe_f{fold}']['real'], 3)} "
           f"z {np.round(J[f'oe_f{fold}']['z'], 2)}")
        J[f"markov_f{fold}"] = markov_locate(fold, S, Gl, F)
        rsm = ((F.gtype == 2) & F.pbp_ok).to_numpy()[S.gi.to_numpy()]
        J[f"cluster_f{fold}"] = goal_clustering(S, Gl, F, g, rsm)
        J[f"persist_f{fold}"] = lead_persistence(S, Gl, F, g, rsm)
        J[f"strat_f{fold}"] = stratified_chain(fold, S, Gl, F, games)
        J[f"p3split_f{fold}"] = p3_split_chain(fold, S, Gl, F)
        for k in ("cluster", "persist", "strat", "p3split"):
            pr(f"   {k}: {json.dumps(J[f'{k}_f{fold}'], default=float)[:900]}")
        if fold == 2:
            F2, g2 = F, g
    part3(F2, g2)
    (OUT / "grade.json").write_text(json.dumps(J, indent=1, default=float))
    pr("wrote", OUT / "grade.json")


if __name__ == "__main__":
    main()
