"""INV-71 (Lane D1, 2026-10-21): where does the regulation margin compression come from? DIAGNOSIS ONLY: no fix, no
tuning, no table change. Every counterfactual here is a re-weighting of recorded sim output, labelled DIAGNOSTIC.

Inputs (fold 2 = 2024-25; nothing from 2025-26 is read):
  sim  results/diag_margin_inv71_v1/rec_*.npz      (diag_margin_inv71_sim_v1.py; pull OFF default set, 200 seeds,
                                                    identical games to results/engine_defaults_v1)
       results/engine_defaults_v1/part_*.parquet   (Lane E3's per-sim stage counts; same seeds and streams)
  real data/reference/verified_finals_v2.parquet   (finals), data/processed/events/events_20242025.parquet (pbp goals,
       shots), data/processed/shot_attempt/attempt_rows_v1_20242025.parquet (attempts / goals / exposure by team-view
       state x pre-event score bucket x period), results/goal_g_r3/fold2 (C1s offline rows / predictions).

    diag_margin_inv71_grade_v1.py   -> results/diag_margin_inv71_v1/grade.json + printed tables (the report is
                                       docs/tests/margin_diagnosis_inv71_2026-10-21.md)
"""
import json
import warnings
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402

warnings.filterwarnings("ignore")

REC = ROOT / "results" / "diag_margin_inv71_v1"
E3 = ROOT / "results" / "engine_defaults_v1"
SEASON = 20242025
SNAP_T = (1200, 2400, 3300, 3600)
SNAP_L = ("20:00", "40:00", "55:00", "60:00")
SWAP = np.array([0, 2, 1, 3, 4])
BUCK = ["trail2+", "trail1", "tied", "lead1", "lead2+"]
B_OF_SC7 = np.array([0, 0, 1, 2, 3, 4, 4])
OUTJ = {}


def pr(*a):
    print(*a, flush=True)


def team_view_st(sk_own, sk_opp):
    return np.where(sk_own > sk_opp, 1, np.where(sk_own < sk_opp, 2, np.where(sk_own == 5, 0, np.where(sk_own == 4, 3, 4))))


# ----------------------------------------------------------------------------------------------- load sim
def load_sim():
    fs = sorted(REC.glob("rec_*.npz"))
    games = None
    rows, goals = [], []
    att = np.zeros((4, 2, 5, 7))
    expo = np.zeros((4, 5, 7))
    off = 0
    for f in fs:
        z = np.load(f)
        if games is None:
            games = z["game_id"]
        assert (z["game_id"] == games).all()
        n = len(z["seed"])
        snap = z["snap"]
        d = dict(gi=z["game_idx"], seed=z["seed"], h=z["score"][:, 0].astype(int), a=z["score"][:, 1].astype(int),
                 es=z["end_state"], so_hw=z["so_home_win"])
        for k, lab in enumerate(SNAP_L):
            d[f"h{lab}"] = snap[k, :, 0].astype(int)
            d[f"a{lab}"] = snap[k, :, 1].astype(int)
        rows.append(pd.DataFrame(d))
        goals.append(pd.DataFrame(dict(sim=z["g_idx"] + off, team=z["g_team"], t=z["g_t"], ph=z["g_pre"][:, 0],
                                       pa=z["g_pre"][:, 1], skh=z["g_sk"][:, 0], ska=z["g_sk"][:, 1])))
        att += z["att"]
        expo += z["expo"]
        off += n
    S = pd.concat(rows, ignore_index=True)
    Gl = pd.concat(goals, ignore_index=True)
    Gl["gi"] = S.gi.to_numpy()[Gl.sim.to_numpy()]
    pr("sim files", len(fs), "sims", len(S), "seeds", S.seed.nunique(), "goals", len(Gl))
    return games, S, Gl, att, expo


# ----------------------------------------------------------------------------------------------- load real
def load_real(games):
    v = pd.read_parquet(ROOT / "data/reference/verified_finals_v2.parquet")
    v = v[(v.season == SEASON) & v.verified_v2].set_index("game_id").loc[games].reset_index()
    so = v.end_state == "SO"
    # SO bonus goal excluded (schema): the SO winner's final score minus 1
    hs = v.home_score.to_numpy() - (so & (v.home_score > v.away_score)).to_numpy()
    as_ = v.away_score.to_numpy() - (so & (v.away_score > v.home_score)).to_numpy()
    F = pd.DataFrame(dict(game_id=v.game_id, gtype=v.game_type, home=v.home, away=v.away, H=hs, A=as_, es=v.end_state,
                          hw=(v.home_score > v.away_score).to_numpy()))
    e = pd.read_parquet(ROOT / f"data/processed/events/events_{SEASON}.parquet",
                        columns=["game_id", "type_desc_key", "period", "period_type", "game_time_s", "owner_is_home",
                                 "home_goalie", "away_goalie", "home_skaters", "away_skaters", "home_score_pre",
                                 "away_score_pre", "goalie_id", "shooting_team_id", "situation_code"])
    e = e[e.game_id.isin(games) & (e.period_type != "SO")]
    g = e[e.type_desc_key == "goal"].copy()
    g["home_sc"] = g.owner_is_home.astype(bool)
    g["own_g_out"] = np.where(g.home_sc, g.home_goalie == 0, g.away_goalie == 0)
    g["opp_g_out"] = np.where(g.home_sc, g.away_goalie == 0, g.home_goalie == 0)
    g["g_out"] = g.own_g_out | g.opp_g_out
    pre_d = np.where(g.home_sc, g.home_score_pre - g.away_score_pre, g.away_score_pre - g.home_score_pre)
    # the pulled side is trailing before the goal: own goalie out & own deficit, or opp goalie out & opp deficit
    pulled_trailing = (g.own_g_out & (pre_d < 0)) | (g.opp_g_out & (pre_d > 0))
    g["late_pull"] = g.g_out & (g.game_time_s >= 3000) & (g.game_time_s < 3600) & pulled_trailing
    g["other_out"] = g.g_out & ~g.late_pull
    # pbp goals == verified final (SO bonus excluded)?
    cnt = g.groupby(["game_id", "home_sc"]).size().unstack(fill_value=0).reindex(games, fill_value=0)
    ok = (cnt[True].to_numpy() == F.H.to_numpy()) & (cnt[False].to_numpy() == F.A.to_numpy())
    F["pbp_ok"] = ok
    pr("real games", len(F), "pbp goal sums == verified final:", int(ok.sum()), "mismatch", int((~ok).sum()))
    OUTJ["pbp_mismatch"] = F.loc[~ok, "game_id"].tolist()
    return F, g, e


def score_at(gtab, games, T, drop=None):
    m = gtab.game_time_s < T
    if drop is not None:
        m &= ~gtab[drop]
    x = gtab[m].groupby(["game_id", "home_sc"]).size().unstack(fill_value=0).reindex(games, fill_value=0)
    return x.get(True, pd.Series(0, index=games)).to_numpy(), x.get(False, pd.Series(0, index=games)).to_numpy()


def dist_margin(d, w=None):
    """|margin| 0 / 1 / 2 / 3+ and home margin <=-3 .. >=3 proportions (weights w)."""
    w = np.ones(len(d)) if w is None else w
    ab = np.minimum(np.abs(d), 3)
    hm = np.clip(d, -3, 3)
    W = w.sum()
    return ([float(w[ab == k].sum() / W) for k in range(4)], [float(w[hm == k].sum() / W) for k in range(-3, 4)],
            float(np.sqrt((w * (d - (w * d).sum() / W) ** 2).sum() / W)))


# ----------------------------------------------------------------------------------------------- item 1
def item1(S, F, g, games, rs):
    pr("\n== ITEM 1: margin / score state at 20:00, 40:00, 55:00, 60:00 (", "RS" if rs else "ALL", ")")
    gmask = (F.gtype == 2).to_numpy() if rs else np.ones(len(F), bool)
    gmask = gmask & F.pbp_ok.to_numpy()
    sm = gmask[S.gi.to_numpy()]
    out = {}
    n = int(gmask.sum())
    for T, lab in zip(SNAP_T, SNAP_L):
        ds = (S[f"h{lab}"] - S[f"a{lab}"]).to_numpy()[sm]
        abs_s, hm_s, sd_s = dist_margin(ds)
        vers = {"real (all goals)": None, "real (no goalie-out goals)": "g_out"}
        if lab == "60:00":
            vers["real (no late-pull goals only)"] = "late_pull"
        res = {"sim": dict(abs=abs_s, home=hm_s, sd=sd_s)}
        for name, drop in vers.items():
            h, a = score_at(g, games, T, drop)
            dr = (h - a)[gmask]
            abs_r, hm_r, sd_r = dist_margin(dr)
            res[name] = dict(abs=abs_r, home=hm_r, sd=sd_r)
        out[lab] = res
        pr(f"-- {lab}  n_real={n}")
        pr("   |margin| 0/1/2/3+   sim", np.round(abs_s, 4), "SD", round(sd_s, 3))
        for name in vers:
            r = res[name]
            se0 = np.sqrt(r["abs"][0] * (1 - r["abs"][0]) / n)
            pr(f"   {name:32s}", np.round(r["abs"], 4), "SD", round(r["sd"], 3), f" tie SE {se0:.4f}",
               f" sim-real tie {abs_s[0] - r['abs'][0]:+.4f} ({(abs_s[0] - r['abs'][0]) / se0:+.1f} SE)")
        pr("   home margin -3..+3  sim", np.round(hm_s, 4))
        for name in vers:
            pr(f"   {name:32s}", np.round(res[name]["home"], 4))
    # goalie-out goal inventory
    gg = g[g.game_id.isin(np.asarray(games)[gmask])]
    out["inventory"] = dict(n_goals=int(len(gg)), late_pull=int(gg.late_pull.sum()), other_out=int(gg.other_out.sum()),
                            other_out_before_3300=int((gg.other_out & (gg.game_time_s < 3300)).sum()),
                            per_game_late_pull=float(gg.late_pull.sum() / n), per_game_other=float(gg.other_out.sum() / n))
    pr("   goalie-out goals:", out["inventory"])
    OUTJ[f"item1_{'rs' if rs else 'all'}"] = out
    return out


# ----------------------------------------------------------------------------------------------- item 2
def item2(Gl, att, expo):
    pr("\n== ITEM 2: score effects, attempts and goals per 60 by pre-event team-view score bucket (all 1,398 games)")
    ar = pd.read_parquet(ROOT / f"data/processed/shot_attempt/attempt_rows_v1_{SEASON}.parquet",
                         columns=["game_id", "period", "st", "sc", "exposure_s", "y", "y_goal", "is_home", "team"])
    ar = ar[ar.st <= 4]
    ar["p"] = np.minimum(ar.period, 4) - 1
    # sim goals, team view
    th = Gl.team.to_numpy() == 0
    own = np.where(th, Gl.skh, Gl.ska)
    opp = np.where(th, Gl.ska, Gl.skh)
    st = team_view_st(own, opp)
    dd = np.where(th, Gl.ph - Gl.pa, Gl.pa - Gl.ph)
    sc = np.clip(dd, -3, 3) + 3
    p = np.minimum(Gl.t.to_numpy() // 1200, 3)
    gsim = np.zeros((4, 5, 7))
    np.add.at(gsim, (p, st, sc), 1)
    # sim exposure team view (both teams): home view expo[p, st, sc] + away view expo[p, SWAP st, 6 - sc]
    ex_tv = expo + expo[:, SWAP][:, :, ::-1]
    a_tv = att.sum(1)
    real_e = np.zeros((4, 5, 7))
    real_a = np.zeros((4, 5, 7))
    real_g = np.zeros((4, 5, 7))
    for arr, col in ((real_e, "exposure_s"), (real_a, "y"), (real_g, "y_goal")):
        s = ar.groupby(["p", "st", "sc"])[col].sum()
        for (pp, ss, cc), val in s.items():
            arr[pp, ss, cc] = val
    res = {}
    for slab, sts in (("all non-EN states", [0, 1, 2, 3, 4]), ("5v5", [0])):
        for plab, ps in (("all periods", [0, 1, 2, 3]), ("P1", [0]), ("P2", [1]), ("P3", [2]), ("OT", [3])):
            def agg(arr):
                x = arr[np.ix_(ps, sts)].sum((0, 1))
                return np.array([x[B_OF_SC7 == b].sum() for b in range(5)])
            se, sa, sg = agg(ex_tv), agg(a_tv), agg(gsim)
            re_, ra, rg = agg(real_e), agg(real_a), agg(real_g)
            row = dict(sim_att60=(sa / se * 3600).tolist(), real_att60=(ra / re_ * 3600).tolist(),
                       sim_g60=(sg / se * 3600).tolist(), real_g60=(rg / re_ * 3600).tolist(),
                       sim_hours=(se / 3600).tolist(), real_hours=(re_ / 3600).tolist(), real_goals=rg.tolist(),
                       real_att=ra.tolist())
            # goal SE (Poisson) on the real side
            row["real_g60_se"] = (np.sqrt(rg) / re_ * 3600).tolist()
            res[f"{slab} | {plab}"] = row
            pr(f"-- {slab} | {plab}")
            pr("   bucket      ", BUCK)
            pr("   time share  sim", np.round(se / se.sum(), 4), " real", np.round(re_ / re_.sum(), 4))
            pr("   att/60 sim  ", np.round(row["sim_att60"], 2), " real", np.round(row["real_att60"], 2),
               " ratio", np.round(np.array(row["sim_att60"]) / np.array(row["real_att60"]), 3))
            pr("   g/60   sim  ", np.round(row["sim_g60"], 3), " real", np.round(row["real_g60"], 3),
               " ratio", np.round(np.array(row["sim_g60"]) / np.array(row["real_g60"]), 3), " real n goals", rg.astype(int))
    OUTJ["item2"] = res
    return res


def item2_std(Gl, S, F, games):
    """Team-standardised score effect: O/E by bucket with E = exposure x the team's own season rate (all states),
    normalised to tied = 1. Separates the response to the score from who is trailing (team composition)."""
    pr("\n== ITEM 2b: team-standardised score effect (O/E by bucket, tied = 1), all games, all non-EN states")
    cols = ["game_id", "seed"] + [f"att_{s}_sc{k}" for s in "ha" for k in range(7)] + \
           [f"toi_{st}_{k}" for st in range(5) for k in range(7)]
    P = pd.concat([pd.read_parquet(f, columns=cols) for f in sorted(E3.glob("part_*.parquet"))], ignore_index=True)
    gpos = pd.Series(np.arange(len(games)), index=games)
    gi = gpos.loc[P.game_id].to_numpy()
    home_t, away_t = F.home.to_numpy()[gi], F.away.to_numpy()[gi]
    toi_h = np.stack([sum(P[f"toi_{st}_{k}"].to_numpy() for st in range(5)) for k in range(7)], 1).astype(float)
    toi_a = toi_h[:, ::-1]
    att_h = np.stack([P[f"att_h_sc{k}"].to_numpy() for k in range(7)], 1).astype(float)
    att_a = np.stack([P[f"att_a_sc{k}"].to_numpy() for k in range(7)], 1).astype(float)
    # sim goals by (sim row, team, sc) -> align to part rows by (game_id, seed)
    S_key = pd.Series(np.arange(len(S)), index=pd.MultiIndex.from_arrays([games[S.gi.to_numpy()], S.seed.to_numpy()]))
    srow = S_key.loc[pd.MultiIndex.from_arrays([P.game_id.to_numpy(), P.seed.to_numpy()])].to_numpy()
    inv = np.empty(len(S), np.int64)
    inv[srow] = np.arange(len(P))
    th = Gl.team.to_numpy() == 0
    dd = np.where(th, Gl.ph - Gl.pa, Gl.pa - Gl.ph)
    sc = np.clip(dd, -3, 3) + 3
    gh = np.zeros((len(P), 7))
    ga = np.zeros((len(P), 7))
    r_ = inv[Gl.sim.to_numpy()]
    np.add.at(gh, (r_[th], sc[th]), 1)
    np.add.at(ga, (r_[~th], sc[~th]), 1)

    def oe(teams_h, teams_a, Eh, Ea, Yh, Ya):
        df = pd.DataFrame(np.vstack([Eh, Ea]), columns=range(7))
        y = pd.DataFrame(np.vstack([Yh, Ya]), columns=range(7))
        tm = np.concatenate([teams_h, teams_a])
        rate = y.sum(1).groupby(tm).sum() / df.sum(1).groupby(tm).sum()
        E = df.mul(rate.loc[tm].to_numpy(), axis=0).sum(0).to_numpy()
        O = y.sum(0).to_numpy()
        o5 = np.array([O[B_OF_SC7 == b].sum() for b in range(5)])
        e5 = np.array([E[B_OF_SC7 == b].sum() for b in range(5)])
        r = o5 / e5
        return r / r[2], o5

    res = {}
    for lab, (Yh, Ya) in (("attempts", (att_h, att_a)), ("goals", (gh, ga))):
        res[f"sim {lab}"] = oe(home_t, away_t, toi_h, toi_a, Yh, Ya)[0].tolist()
    # real
    ar = pd.read_parquet(ROOT / f"data/processed/shot_attempt/attempt_rows_v1_{SEASON}.parquet",
                         columns=["game_id", "st", "sc", "exposure_s", "y", "y_goal", "is_home"])
    ar = ar[ar.st <= 4]
    fi = F.set_index("game_id")
    ar["tm"] = np.where(ar.is_home == 1, fi.home.loc[ar.game_id].to_numpy(), fi.away.loc[ar.game_id].to_numpy())
    for lab, col in (("attempts", "y"), ("goals", "y_goal")):
        rate = ar.groupby("tm")[col].sum() / ar.groupby("tm").exposure_s.sum()
        E = (ar.exposure_s * rate.loc[ar.tm].to_numpy()).groupby(ar.sc).sum().reindex(range(7), fill_value=0).to_numpy()
        O = ar.groupby("sc")[col].sum().reindex(range(7), fill_value=0).to_numpy()
        o5 = np.array([O[B_OF_SC7 == b].sum() for b in range(5)])
        e5 = np.array([E[B_OF_SC7 == b].sum() for b in range(5)])
        r = o5 / e5
        res[f"real {lab}"] = (r / r[2]).tolist()
        res[f"real {lab} n"] = o5.tolist()
        # Poisson SE of log ratio vs tied
        res[f"real {lab} se"] = (np.sqrt(1 / np.maximum(o5, 1) + 1 / o5[2]) * (r / r[2])).tolist()
    for k, v in res.items():
        pr(f"   {k:16s}", np.round(v, 3))
    OUTJ["item2_std"] = res
    return res


def item2_offline():
    """Offline residual by score bucket on actual fold-2 rows: the stage-3 attempt table and the C1s goal model."""
    pr("\n== ITEM 2c: offline sum(pred) / sum(actual) by team-view score bucket on fold-2 rows (no closed loop)")
    res = {}
    gd = ROOT / "results/goal_g_r3/fold2"
    lab = json.loads((gd / "labels_sealed.json").read_text())["C1s"]
    r = pd.read_parquet(gd / "fold2_rows.parquet", columns=["sg", "sc", "y", "period"])
    p = np.load(gd / f"fold2_pred_{lab}.npy").astype(float)
    m = (r.sg <= 4).to_numpy()
    for slab, mm in (("all", m), ("5v5", m & (r.sg == 0).to_numpy())):
        b = B_OF_SC7[r.sc.to_numpy()[mm]]
        yy, pp = r.y.to_numpy()[mm], p[mm]
        ratio = [float(pp[b == k].sum() / yy[b == k].sum()) for k in range(5)]
        n = [int(yy[b == k].sum()) for k in range(5)]
        res[f"goal C1s {slab}"] = dict(pred_over_actual=ratio, n_goals=n)
        pr(f"   goal C1s per SOG ({slab}) pred/actual", np.round(ratio, 3), "n goals", n)
    # stage 3 A3g-c offline: the served att_lam table on the actual attempt rows
    z = np.load(sorted(REC.glob("rec_*.npz"))[0])
    games = z["game_id"]
    att = np.load(ROOT / "results/shot_attempt_r3/att_lam_A3g-c_fold2.npy")
    ar = pd.read_parquet(ROOT / f"data/processed/shot_attempt/attempt_rows_v1_{SEASON}.parquet",
                         columns=["game_id", "t0", "st", "sc", "exposure_s", "y", "is_home"])
    ar = ar[ar.st <= 4]
    gpos = pd.Series(np.arange(len(games)), index=games)
    gi = gpos.loc[ar.game_id].to_numpy()
    tm = np.where(ar.is_home.to_numpy() == 1, 0, 1)
    mi = np.minimum(ar.t0.to_numpy() // 60, att.shape[2] - 1)
    lam = att[gi, tm, mi, ar.st.to_numpy(), ar.sc.to_numpy()].astype(float) / 3600 * ar.exposure_s.to_numpy()
    for slab, mm in (("all", np.ones(len(ar), bool)), ("5v5", (ar.st == 0).to_numpy())):
        b = B_OF_SC7[ar.sc.to_numpy()[mm]]
        yy, pp = ar.y.to_numpy()[mm], lam[mm]
        ratio = [float(pp[b == k].sum() / yy[b == k].sum()) for k in range(5)]
        res[f"attempts A3g-c {slab}"] = dict(pred_over_actual=ratio, n=[int(yy[b == k].sum()) for k in range(5)])
        pr(f"   attempts A3g-c ({slab}) pred/actual", np.round(ratio, 3))
    OUTJ["item2_offline"] = res
    return res


# ----------------------------------------------------------------------------------------------- item 3 / 4
def load_e3_stage(games):
    cols = ["game_id", "seed", "goalie_vs_h", "goalie_vs_a"] + [f"{q}_{s}_st{k}" for q in ("att", "sog", "gl", "xg")
                                                                 for s in "ha" for k in range(5)]
    P = pd.concat([pd.read_parquet(f, columns=cols) for f in sorted(E3.glob("part_*.parquet"))], ignore_index=True)
    out = pd.DataFrame(dict(game_id=P.game_id, seed=P.seed, gv_h=P.goalie_vs_h, gv_a=P.goalie_vs_a))
    for q in ("att", "sog", "gl", "xg"):
        for s in "ha":
            out[f"{q}_{s}"] = sum(P[f"{q}_{s}_st{k}"] for k in range(5))
    return out.groupby("game_id").agg({c: "mean" for c in out.columns if c not in ("game_id", "seed")} |
                                      {"gv_h": "first", "gv_a": "first"}).loc[games]


def real_stage(F, e, games):
    ar = pd.read_parquet(ROOT / f"data/processed/shot_attempt/attempt_rows_v1_{SEASON}.parquet",
                         columns=["game_id", "st", "y", "is_home"])
    ar = ar[ar.st <= 4]
    a = ar.groupby(["game_id", "is_home"]).y.sum().unstack(fill_value=0).reindex(games, fill_value=0)
    gin = (e.home_goalie == 1) & (e.away_goalie == 1)          # both goalies in: like with like (no pull in the sim)
    sh = e[gin & e.type_desc_key.isin(["shot-on-goal", "goal"])]
    sog = sh.groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0).reindex(games, fill_value=0)
    gl = sh[sh.type_desc_key == "goal"].groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0) \
        .reindex(games, fill_value=0)
    R = pd.DataFrame(dict(att_h=a[1].to_numpy(), att_a=a[0].to_numpy(), sog_h=sog[True].to_numpy(),
                          sog_a=sog[False].to_numpy(), gl_h=gl[True].to_numpy(), gl_a=gl[False].to_numpy()), index=games)
    return R


def wls_slope(x, y, w):
    w = w / w.sum()
    mx, my = (w * x).sum(), (w * y).sum()
    b = (w * (x - mx) * (y - my)).sum() / (w * (x - mx) ** 2).sum()
    return float(b)


def item3(S, F, g, e, games, ST, RT):
    pr("\n== ITEM 3: team spread (regular season, pbp-verified games)")
    gm = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    sm = gm[S.gi.to_numpy()]
    S2 = S[sm]
    # per game sim means
    S2 = S2.assign(m60=S2["h60:00"] - S2["a60:00"], m55=S2["h55:00"] - S2["a55:00"], mf=S2.h - S2.a)
    gmean = S2.groupby("gi")[["m60", "m55", "mf", "h", "a"]].mean()
    gvar = S2.groupby("gi")[["m60", "m55", "mf"]].var(ddof=0)
    gidx = np.flatnonzero(gm)
    h55, a55 = score_at(g, games, 3300)
    h60n, a60n = score_at(g, games, 3600, "g_out")
    hf_n = F.H.to_numpy() - np.bincount(np.searchsorted(games, g.game_id[g.g_out & g.home_sc]), minlength=len(games))
    af_n = F.A.to_numpy() - np.bincount(np.searchsorted(games, g.game_id[g.g_out & ~g.home_sc]), minlength=len(games))
    real = pd.DataFrame(dict(m55=(h55 - a55), m60=(h60n - a60n), mf=(F.H - F.A).to_numpy(), mf_n=hf_n - af_n),
                        index=np.arange(len(games))).loc[gidx]
    res = {}
    # game-level: actual on sim game mean (D32 helper, deciles of the sim mean) + OLS with SE
    for lab, sc_, rc in (("55:00 regulation", "m55", "m55"), ("60:00 regulation, real without goalie-out goals", "m60", "m60"),
                         ("final incl OT, real without goalie-out goals", "mf", "mf_n"), ("final incl OT, real all goals", "mf", "mf")):
        x = gmean.loc[gidx, sc_].to_numpy()
        y = real[rc].to_numpy()
        X = np.c_[np.ones_like(x), x]
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        s2 = resid.var(ddof=2)
        cov = s2 * np.linalg.inv(X.T @ X)
        sr = slope_ratio(x, y, x, np.ones_like(x), games[gidx], n_boot=500)
        within = float(gvar.loc[gidx, sc_].mean())
        res[lab] = dict(a=float(beta[0]), b=float(beta[1]), b_se=float(np.sqrt(cov[1, 1])), R=sr["R"], R_ci=sr["ci"],
                        sim_between_var=float(x.var()), sim_within_var=within, sim_total_var=float(x.var() + within),
                        real_total_var=float(y.var()), real_resid_var=float(resid.var()),
                        real_mean=float(y.mean()), sim_mean=float(x.mean()), n=int(len(x)))
        r = res[lab]
        pr(f"-- {lab}: actual = {r['a']:+.3f} + {r['b']:.3f} (SE {r['b_se']:.3f}) x sim mean; D32 R = {r['R']:.3f} "
           f"CI {r['R_ci'][0]:.2f}-{r['R_ci'][1]:.2f}")
        pr(f"   var: sim between {r['sim_between_var']:.3f} within {r['sim_within_var']:.3f} total {r['sim_total_var']:.3f} | "
           f"real total {r['real_total_var']:.3f} resid {r['real_resid_var']:.3f} | b^2 x sim between {r['b'] ** 2 * r['sim_between_var']:.3f}"
           f" | means sim {r['sim_mean']:+.3f} real {r['real_mean']:+.3f}")
    OUTJ["item3_game"] = res
    # per team
    T = []
    for side, sgn in (("home", 1), ("away", -1)):
        d = pd.DataFrame(dict(team=F[side].to_numpy()[gidx], sim_m=sgn * gmean.loc[gidx, "mf"].to_numpy(),
                              sim_m60=sgn * gmean.loc[gidx, "m60"].to_numpy(),
                              real_m=sgn * real.mf.to_numpy(), real_mn=sgn * real.mf_n.to_numpy(), real_m60=sgn * real.m60.to_numpy()))
        for q in ("att", "sog", "gl"):
            o, x = ("h", "a") if side == "home" else ("a", "h")
            d[f"sim_{q}_f"] = ST[f"{q}_{o}"].to_numpy()[gidx]
            d[f"sim_{q}_a"] = ST[f"{q}_{x}"].to_numpy()[gidx]
            d[f"real_{q}_f"] = RT[f"{q}_{o}"].to_numpy()[gidx]
            d[f"real_{q}_a"] = RT[f"{q}_{x}"].to_numpy()[gidx]
        T.append(d)
    T = pd.concat(T, ignore_index=True)
    tm = T.groupby("team").mean()
    nG = T.groupby("team").size()
    tv = T.groupby("team").var()
    out = {}
    metrics = {"margin final (real all goals)": ("sim_m", "real_m"), "margin final (real no goalie-out)": ("sim_m", "real_mn"),
               "margin 60:00 (real no goalie-out)": ("sim_m60", "real_m60")}
    for q in ("att", "sog", "gl"):
        tm[f"sim_{q}_d"] = tm[f"sim_{q}_f"] - tm[f"sim_{q}_a"]
        tm[f"real_{q}_d"] = tm[f"real_{q}_f"] - tm[f"real_{q}_a"]
        T[f"real_{q}_d"] = T[f"real_{q}_f"] - T[f"real_{q}_a"]
        metrics[f"{q} for"] = (f"sim_{q}_f", f"real_{q}_f")
        metrics[f"{q} against"] = (f"sim_{q}_a", f"real_{q}_a")
        metrics[f"{q} diff"] = (f"sim_{q}_d", f"real_{q}_d")
    tv = T.groupby("team").var()
    # finishing (sh% for) and goaltending + defence (sv% against) per team
    tm["sim_shp"] = tm.sim_gl_f / tm.sim_sog_f
    tm["real_shp"] = tm.real_gl_f / tm.real_sog_f
    tm["sim_svp"] = 1 - tm.sim_gl_a / tm.sim_sog_a
    tm["real_svp"] = 1 - tm.real_gl_a / tm.real_sog_a
    metrics["sh% for"] = ("sim_shp", "real_shp")
    metrics["sv% against"] = ("sim_svp", "real_svp")
    pr(f"-- per team (n teams {len(tm)}, games per team {int(nG.min())}-{int(nG.max())}): slope b of actual on sim, "
       f"R = 1/b, SD sim vs SD real (noise-corrected where a per-game variance exists)")
    for k, (sc_, rc) in metrics.items():
        x, y = tm[sc_].to_numpy(), tm[rc].to_numpy()
        b = wls_slope(x, y, nG.to_numpy().astype(float))
        corr = float(np.corrcoef(x, y)[0, 1])
        sd_s, sd_r = float(x.std()), float(y.std())
        noise = float((tv[rc] / nG).mean()) if rc in tv else float("nan")
        sd_rc = float(np.sqrt(max(y.var() - noise, 0))) if np.isfinite(noise) else float("nan")
        # SE of b: bootstrap over teams' games
        out[k] = dict(b=b, R=1 / b if b else float("nan"), corr=corr, sd_sim=sd_s, sd_real=sd_r, sd_real_noise_corr=sd_rc,
                      mean_sim=float(x.mean()), mean_real=float(y.mean()))
        pr(f"   {k:34s} b {b:6.3f} R {1 / b if b else float('nan'):6.3f} corr {corr:5.2f} | SD sim {sd_s:.4f} real {sd_r:.4f} "
           f"(noise-corr {sd_rc:.4f}) | mean sim {x.mean():.4f} real {y.mean():.4f}")
    OUTJ["item3_team"] = out
    # bootstrap SE for the team margin slope (resample games within team)
    rng = np.random.default_rng(0)
    bs = []
    grp = [np.flatnonzero(T.team.to_numpy() == t) for t in np.unique(T.team)]
    sim_m, real_mn = T.sim_m.to_numpy(), T.real_mn.to_numpy()
    for _ in range(300):
        xs, ys = [], []
        for ix in grp:
            j = rng.choice(ix, len(ix))
            xs.append(sim_m[j].mean())
            ys.append(real_mn[j].mean())
        bs.append(wls_slope(np.array(xs), np.array(ys), np.ones(len(xs))))
    out["margin final (real no goalie-out)"]["b_boot_ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    pr("   team margin slope (no goalie-out) bootstrap 95% CI", np.round(out["margin final (real no goalie-out)"]["b_boot_ci"], 3))
    return res, out, gmean, real, gidx


def item4(F, e, games, ST):
    pr("\n== ITEM 4: goalie spread (regular season; sim = box-score starter faces every SOG, ORACLE)")
    gm = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    gidx = np.flatnonzero(gm)
    gin = (e.home_goalie == 1) & (e.away_goalie == 1)
    sh = e[gin & e.type_desc_key.isin(["shot-on-goal", "goal"])]
    # team-defence in that game: shots against the defending team (all its goalies) -> like the oracle starter
    sog = sh.groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0).reindex(games, fill_value=0)
    gl = sh[sh.type_desc_key == "goal"].groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0).reindex(games, fill_value=0)
    rows = []
    for side, opp in (("h", False), ("a", True)):
        # goalie_vs_h = goalie facing the home team's shots = away starter
        gk = ST[f"gv_{side}"].to_numpy()[gidx]
        rows.append(pd.DataFrame(dict(goalie=gk, sim_sa=ST[f"sog_{side}"].to_numpy()[gidx], sim_ga=ST[f"gl_{side}"].to_numpy()[gidx],
                                      real_sa=sog[side == "h"].to_numpy()[gidx],
                                      real_ga=gl[side == "h"].to_numpy()[gidx])))
    D = pd.concat(rows, ignore_index=True)
    agg = D.groupby("goalie").agg(n=("sim_sa", "size"), sim_sa=("sim_sa", "sum"), sim_ga=("sim_ga", "sum"),
                                  real_sa=("real_sa", "sum"), real_ga=("real_ga", "sum"))
    agg = agg[agg.n >= 10]
    agg["sim_sv"] = 1 - agg.sim_ga / agg.sim_sa
    agg["real_sv"] = 1 - agg.real_ga / agg.real_sa
    agg["sim_gapg"] = agg.sim_ga / agg.n
    agg["real_gapg"] = agg.real_ga / agg.n
    w = agg.real_sa.to_numpy().astype(float)
    b = wls_slope(agg.sim_sv.to_numpy(), agg.real_sv.to_numpy(), w)
    corr = float(np.corrcoef(agg.sim_sv, agg.real_sv)[0, 1])
    # binomial noise in real sv%
    noise_sv = float((agg.real_sv * (1 - agg.real_sv) / agg.real_sa).mean())
    sd_sv_r = float(agg.real_sv.std(ddof=0))
    sd_sv_rc = float(np.sqrt(max(agg.real_sv.var(ddof=0) - noise_sv, 0)))
    sd_sv_s = float(agg.sim_sv.std(ddof=0))
    Dv = D.groupby("goalie").real_ga.var()
    noise_ga = float((Dv.loc[agg.index] / agg.n).mean())
    out = dict(n_goalies=int(len(agg)), b_sv=b, R_sv=1 / b, corr_sv=corr, sd_sv_sim=sd_sv_s, sd_sv_real=sd_sv_r,
               sd_sv_real_noise_corr=sd_sv_rc, sd_gapg_sim=float(agg.sim_gapg.std(ddof=0)),
               sd_gapg_real=float(agg.real_gapg.std(ddof=0)),
               sd_gapg_real_noise_corr=float(np.sqrt(max(agg.real_gapg.var(ddof=0) - noise_ga, 0))),
               sv_sim=float(1 - agg.sim_ga.sum() / agg.sim_sa.sum()), sv_real=float(1 - agg.real_ga.sum() / agg.real_sa.sum()),
               sa_pg_sim=float(agg.sim_sa.sum() / agg.n.sum()), sa_pg_real=float(agg.real_sa.sum() / agg.n.sum()))
    # per-start dispersion of GA (within-game): sim per-start variance is not in E3 means; report real per-start SD
    out["real_ga_per_start_sd"] = float(D.real_ga.std())
    for k, v in out.items():
        pr(f"   {k:28s} {v:.4f}" if isinstance(v, float) else f"   {k:28s} {v}")
    OUTJ["item4"] = out
    return out


# ----------------------------------------------------------------------------------------------- item 5
def item5(S, Gl, F, g, games):
    pr("\n== ITEM 5: period structure (regular season, pbp-verified)")
    gm = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    n = int(gm.sum())
    sm = gm[S.gi.to_numpy()]
    nsim = int(sm.sum())
    G2 = Gl[gm[Gl.gi.to_numpy()]]
    p = np.minimum(G2.t.to_numpy() // 1200, 3)
    sim_pp = np.bincount(p, minlength=4) / nsim
    gg = g[g.game_id.isin(np.asarray(games)[gm])]
    pr_ = np.minimum(gg.game_time_s.to_numpy() // 1200, 3)
    real_pp = np.bincount(pr_, minlength=4) / n
    real_pp_n = np.bincount(pr_[~gg.g_out.to_numpy()], minlength=4) / n
    real_out = np.bincount(pr_[gg.g_out.to_numpy()], minlength=4) / n
    pr("   goals/game by period P1 P2 P3 OT  sim", np.round(sim_pp, 4))
    pr("   real all goals                       ", np.round(real_pp, 4))
    pr("   real without goalie-out goals        ", np.round(real_pp_n, 4), " goalie-out", np.round(real_out, 4))
    # P3 split: before 55:00 and after
    s3a = ((G2.t >= 2400) & (G2.t < 3300)).sum() / nsim
    s3b = ((G2.t >= 3300) & (G2.t < 3600)).sum() / nsim
    r3a = (((gg.game_time_s >= 2400) & (gg.game_time_s < 3300)) & ~gg.g_out).sum() / n
    r3b = (((gg.game_time_s >= 3300) & (gg.game_time_s < 3600)) & ~gg.g_out).sum() / n
    pr(f"   P3 40:00-55:00 sim {s3a:.4f} real(no g-out) {r3a:.4f} | 55:00-60:00 sim {s3b:.4f} real(no g-out) {r3b:.4f}")
    # first-goal time
    fs = G2.groupby("sim").t.min()
    fsim = np.full(nsim, np.nan)
    simids = np.flatnonzero(sm)
    pos = pd.Series(np.arange(nsim), index=simids)
    fsim[pos.loc[fs.index].to_numpy()] = fs.to_numpy()
    fr = gg.groupby("game_id").game_time_s.min().reindex(np.asarray(games)[gm])
    qs = [0.1, 0.25, 0.5, 0.75]
    out = dict(sim_per_period=sim_pp.tolist(), real_per_period=real_pp.tolist(), real_per_period_no_gout=real_pp_n.tolist(),
               real_gout_per_period=real_out.tolist(), p3_split_sim=[float(s3a), float(s3b)], p3_split_real=[float(r3a), float(r3b)],
               first_goal_q_sim=np.nanquantile(fsim, qs).tolist(), first_goal_q_real=np.nanquantile(fr.to_numpy(), qs).tolist(),
               p_no_goal_by_20_sim=float(np.mean(~(fsim < 1200))), p_no_goal_by_20_real=float(np.mean(~(fr.to_numpy() < 1200))),
               p_scoreless_reg_sim=float(np.mean(~(fsim < 3600))), p_scoreless_reg_real=float(np.mean(~(fr.to_numpy() < 3600))))
    pr("   first-goal second quantiles 10/25/50/75  sim", np.round(out["first_goal_q_sim"]), " real", np.round(out["first_goal_q_real"]))
    pr(f"   P(no goal by 20:00) sim {out['p_no_goal_by_20_sim']:.4f} real {out['p_no_goal_by_20_real']:.4f} "
       f"(SE {np.sqrt(out['p_no_goal_by_20_real'] * (1 - out['p_no_goal_by_20_real']) / n):.4f})")
    # goals per period by pre-goal |margin| (where the goals land)
    OUTJ["item5"] = out
    return out


# ----------------------------------------------------------------------------------------------- item 6
def tilt_weights(m, target, iters=50):
    """Exponential tilting of equally weighted samples m to mean target: w ~ exp(theta m). DIAGNOSTIC re-weighting."""
    th = 0.0
    for _ in range(iters):
        w = np.exp(th * (m - m.mean()))
        w /= w.sum()
        mu = (w * m).sum()
        v = (w * (m - mu) ** 2).sum()
        if v <= 1e-12:
            break
        step = (target - mu) / v
        th += step
        if abs(step) < 1e-10:
            break
    w = np.exp(th * (m - m.mean()))
    return w / w.sum()


def g56(h, a, w, es, hw):
    w = w / w.sum()
    tot = h + a
    d = h - a
    P = [float(w[tot == k].sum()) for k in range(10)] + [float(w[tot >= 10].sum())]
    mt, md = (w * tot).sum(), (w * d).sum()
    mh, ma = (w * h).sum(), (w * a).sum()
    cov = (w * (h - mh) * (a - ma)).sum()
    corr = cov / np.sqrt((w * (h - mh) ** 2).sum() * (w * (a - ma) ** 2).sum())
    return dict(P_total=P, total_mean=float(mt), total_sd=float(np.sqrt((w * (tot - mt) ** 2).sum())),
                margin_sd=float(np.sqrt((w * (d - md) ** 2).sum())), home_goal_diff=float(md), corr=float(corr),
                home_win=float((w * hw).sum()), reg_tie=float(w[es != 1].sum()))


def item6(S, F, g, games, gres):
    pr("\n== ITEM 6: G5 / G6 decomposition, sim vs real, with DIAGNOSTIC re-weighting counterfactuals (not fixes)")
    out = {}
    for scope in ("RS", "ALL"):
        gm = F.pbp_ok.to_numpy() & ((F.gtype == 2).to_numpy() if scope == "RS" else True)
        sm = gm[S.gi.to_numpy()]
        S2 = S[sm].reset_index(drop=True)
        h, a = S2.h.to_numpy(), S2.a.to_numpy()
        es = S2.es.to_numpy()
        hw = np.where(es == 3, S2.so_hw.to_numpy(), h > a).astype(float)
        base_w = np.ones(len(S2))
        res = {"sim": g56(h, a, base_w, es, hw)}
        # real, all goals and without goalie-out goals
        gi = np.flatnonzero(gm)
        H, A = F.H.to_numpy()[gi], F.A.to_numpy()[gi]
        res_es = F.es.to_numpy()[gi]
        esn = np.where(res_es == "REG", 1, np.where(res_es == "OT", 2, 3))
        res["real all goals"] = g56(H, A, np.ones(len(gi)), esn, F.hw.to_numpy()[gi].astype(float))
        oh = np.bincount(np.searchsorted(games, g.game_id[g.g_out & g.home_sc]), minlength=len(games))[gi]
        oa = np.bincount(np.searchsorted(games, g.game_id[g.g_out & ~g.home_sc]), minlength=len(games))[gi]
        h60n, a60n = score_at(g, games, 3600, "g_out")
        tie_n = float(np.mean((h60n - a60n)[gi] == 0))
        rn = g56(H - oh, A - oa, np.ones(len(gi)), esn, F.hw.to_numpy()[gi].astype(float))
        rn["reg_tie"] = tie_n
        rn["note"] = "goalie-out goals removed from the final score; reg_tie = 60:00 margin without them; home_win is the real result"
        res["real no goalie-out goals"] = rn
        # counterfactuals: tilt each game's seeds so its mean 60:00 margin = a + b x sim mean (game-level regression of
        # the real 60:00 margin without goalie-out goals on the sim mean)
        reg = gres["60:00 regulation, real without goalie-out goals"]
        m60 = (S2["h60:00"] - S2["a60:00"]).to_numpy()
        gg = S2.gi.to_numpy()
        order = np.argsort(gg, kind="stable")
        bounds = np.flatnonzero(np.diff(gg[order])) + 1
        for lab in ("CF spread b only", "CF spread b + home intercept a", "CF home level only"):
            w = np.empty(len(S2))
            for idx in np.split(order, bounds):
                mm = m60[idx]
                mu = mm.mean()
                if lab == "CF spread b only":          # stretch about the sim's own population mean
                    tgt = reg["sim_mean"] + reg["b"] * (mu - reg["sim_mean"])
                elif lab == "CF home level only":      # shift every game by the population mean gap
                    tgt = mu + (reg["real_mean"] - reg["sim_mean"])
                else:
                    tgt = reg["a"] + reg["b"] * mu
                w[idx] = tilt_weights(mm, tgt)
            res[lab] = g56(h, a, w, es, hw)
        out[scope] = res
        pr(f"-- {scope}")
        keys = ["reg_tie", "margin_sd", "home_goal_diff", "home_win", "corr", "total_mean", "total_sd"]
        pr("   " + " ".join(f"{k:>14s}" for k in ["arm"] + keys))
        for name, r in res.items():
            pr(f"   {name[:34]:34s}" + " ".join(f"{r[k]:14.4f}" for k in keys))
        pr("   P(total=k) k=0..9,10+")
        for name, r in res.items():
            pr(f"   {name[:34]:34s}", np.round(r["P_total"], 4))
    OUTJ["item6"] = out
    return out


def main():
    games, S, Gl, att, expo = load_sim()
    F, g, e = load_real(games)
    item1(S, F, g, games, rs=True)
    item1(S, F, g, games, rs=False)
    item2(Gl, att, expo)
    item2_std(Gl, S, F, games)
    item2_offline()
    ST = load_e3_stage(games)
    RT = real_stage(F, e, games)
    gres, tres, *_ = item3(S, F, g, e, games, ST, RT)
    item4(F, e, games, ST)
    item5(S, Gl, F, g, games)
    item6(S, F, g, games, gres)
    (REC / "grade.json").write_text(json.dumps(OUTJ, indent=1, default=float))
    pr("\nwrote", REC / "grade.json")


if __name__ == "__main__":
    main()
