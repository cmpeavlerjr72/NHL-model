"""INV-78 (Lane D2, 2026-10-21): noise floor and decomposition of the 55:00 tie gap. DIAGNOSIS ONLY (rates re-weighted,
nothing fitted, no table touched).

  1. Per-seed noise floor (L39): each of the 200 sim seeds is one synthetic season on the real schedule. Per seed: the
     observed RS 55:00 tie share, the tie share implied by that seed's own period x bucket goal rates through the INV-71
     chain, and their difference. The SD across seeds is the one-season sampling SD of the real-side quantities.
  2. Real chain uncertainty: Poisson redraw of the real goal counts per (period, bucket) cell -> SD of the real chain tie.
  3. Additive (Shapley over P1 / P2 / P3) attribution of the chain gap at 40:00 and 55:00; cell swaps at 40:00.
  4. |margin| <= 1 share and margin SD at 55:00 by fold (compression on both folds?).
  5. Part 3: INV-71 factor realisation. Loop rate ratios (repair / incumbent) by period x bucket vs the INV-71 factors
     (results/diag_margin_inv71_v1/markov.json), and the chain-predicted vs observed tie change per repair.

    diag_margin_inv78_extra_v1.py        -> results/diag_margin_inv78_v1/extra.json
    diag_margin_inv78_extra_v1.py post   -> results/diag_margin_inv78_v1/post_goal.json (section 6)
    diag_margin_inv78_extra_v1.py cf     -> results/diag_margin_inv78_v1/cf_p2tied.json (section 7)
"""
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "diag_margin_inv78_v1"


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


G = load_mod("inv78g", "diag_margin_inv78_grade_v1.py")
B7 = G.B_OF_SC7
X = {}


def pr(*a):
    print(*a, flush=True)


def per_seed(fold, S, Gl, F):
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    sm = rs[S.gi.to_numpy()]
    N = len(S)
    E = G.expo_from_goals(N, Gl)                         # (N, 3, 7)
    sc, p = G.team_view_goals(Gl)
    m = Gl.t.to_numpy() < 3600
    seeds = S.seed.to_numpy()
    useeds = np.unique(seeds)
    sidx = np.searchsorted(useeds, seeds)
    Es = np.zeros((len(useeds), 3, 7))
    np.add.at(Es, sidx[sm], E[sm])
    Gs = np.zeros((len(useeds), 3, 7))
    gsim = Gl.sim.to_numpy()
    k = m & sm[gsim]
    np.add.at(Gs, (sidx[gsim[k]], p[k], sc[k]), 1)
    obs = pd.Series((S["d55:00"].to_numpy() == 0)[sm]).groupby(seeds[sm]).mean().to_numpy()
    obs40 = pd.Series((S["d40:00"].to_numpy() == 0)[sm]).groupby(seeds[sm]).mean().to_numpy()
    ch, ch40 = [], []
    for i in range(len(useeds)):
        Etv = Es[i] + Es[i][:, ::-1]
        e5 = np.stack([Etv[:, B7 == b].sum(1) for b in range(5)], 1)
        g5 = np.stack([Gs[i][:, B7 == b].sum(1) for b in range(5)], 1)
        c = G.chain(g5 / e5 * 3600)
        ch.append(G.tie(c[3300]))
        ch40.append(G.tie(c[2400]))
    ch, ch40 = np.array(ch), np.array(ch40)
    d = obs - ch
    out = dict(obs_mean=float(obs.mean()), obs_sd=float(obs.std(ddof=1)), chain_mean=float(ch.mean()), chain_sd=float(ch.std(ddof=1)),
               diff_mean=float(d.mean()), diff_sd=float(d.std(ddof=1)), corr_obs_chain=float(np.corrcoef(obs, ch)[0, 1]),
               obs40_sd=float(obs40.std(ddof=1)), diff40_mean=float((obs40 - ch40).mean()), diff40_sd=float((obs40 - ch40).std(ddof=1)))
    pr(f"  fold {fold} per-seed: obs tie55 {out['obs_mean']:.4f} (SD {out['obs_sd']:.4f}); chain {out['chain_mean']:.4f} "
       f"(SD {out['chain_sd']:.4f}); obs - chain {out['diff_mean']:+.4f} (SD {out['diff_sd']:.4f}); corr {out['corr_obs_chain']:.2f}")
    return out


def real_chain_sd(lam_r, goals_r, n=300, seed=7):
    rng = np.random.default_rng(seed)
    e = goals_r / lam_r
    t55, t40 = [], []
    for _ in range(n):
        gg = rng.poisson(goals_r)
        c = G.chain(gg / e)
        t55.append(G.tie(c[3300]))
        t40.append(G.tie(c[2400]))
    return float(np.std(t55)), float(np.std(t40))


def shapley(lam_s, lam_r, T):
    """Additive attribution over periods of tie(sim rates) - tie(real rates) at time T."""
    P = (0, 1, 2)
    val = {}
    for k in range(4):
        for sub in itertools.combinations(P, k):
            lam = lam_s.copy()
            for p in sub:
                lam[p] = lam_r[p]
            val[sub] = G.tie(G.chain(lam, T_end=T, snaps=(T,))[T])
    phi = {}
    from math import factorial
    for p in P:
        s = 0.0
        others = [q for q in P if q != p]
        for k in range(3):
            for sub in itertools.combinations(others, k):
                w = factorial(k) * factorial(2 - k) / factorial(3)
                with_p = tuple(sorted(sub + (p,)))
                s += w * (val[tuple(sorted(sub))] - val[with_p])
        phi[f"P{p + 1}"] = s
    return phi, val[()] - val[P]


def cells40(lam_s, lam_r):
    base = G.tie(G.chain(lam_s, T_end=2400, snaps=(2400,))[2400])
    out = {}
    for p in (0, 1):
        for glab, idx in (("trailing", [0, 1]), ("tied", [2]), ("leading", [3, 4])):
            lam = lam_s.copy()
            lam[p, idx] = lam_r[p, idx]
            out[f"P{p + 1} {glab}"] = G.tie(G.chain(lam, T_end=2400, snaps=(2400,))[2400]) - base
    return out


def compression(S, F, g):
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()
    sm = rs[S.gi.to_numpy()]
    ds = S["d55:00"].to_numpy()[sm]
    m = (g.game_time_s < 3300) & ~g.g_out
    x = g[m].groupby(["game_id", "home_sc"]).size().unstack(fill_value=0).reindex(F.game_id, fill_value=0)
    dr = (x.get(True, 0) - x.get(False, 0)).to_numpy()[rs]
    n = len(dr)
    p1r = float((np.abs(dr) <= 1).mean())
    return dict(le1_sim=float((np.abs(ds) <= 1).mean()), le1_real=p1r, le1_se=float(np.sqrt(p1r * (1 - p1r) / n)),
                sd_sim=float(ds.std()), sd_real=float(dr.std()), sd_real_se=float(dr.std() / np.sqrt(2 * n)),
                mean_abs_sim=float(np.abs(ds).mean()), mean_abs_real=float(np.abs(dr).mean()))


def main():
    for fold in (1, 2):
        pr(f"\n== fold {fold}")
        games, S, Gl, agg = G.load_rec(OUT / f"f{fold}")
        D1, F, g = G.real(fold, games)
        X[f"seed_f{fold}"] = per_seed(fold, S, Gl, F)
        M = json.loads((OUT / "grade.json").read_text())[f"markov_f{fold}"]
        lam_s, lam_r, gr = np.array(M["lam_sim"]), np.array(M["lam_real"]), np.array(M["real_goals"])
        sd55, sd40 = real_chain_sd(lam_r, gr)
        X[f"real_chain_sd_f{fold}"] = dict(sd55=sd55, sd40=sd40)
        pr(f"  real chain tie SD from goal-count noise: 55:00 {sd55:.4f}, 40:00 {sd40:.4f}")
        for T in (2400, 3300):
            phi, tot = shapley(lam_s, lam_r, T)
            X[f"shapley_f{fold}_{T}"] = dict(phi=phi, total=tot)
            pr(f"  chain gap at {T // 60}:00 {tot:+.4f}; Shapley by period " + ", ".join(f"{k} {v:+.4f}" for k, v in phi.items()))
        X[f"cells40_f{fold}"] = cells40(lam_s, lam_r)
        pr("  cell swaps at 40:00:", {k: round(v, 4) for k, v in X[f"cells40_f{fold}"].items()})
        X[f"compression_f{fold}"] = compression(S, F, g)
        pr("  55:00 compression:", {k: round(v, 4) for k, v in X[f"compression_f{fold}"].items()})
    # ---- part 3: factor realisation (fold 2)
    pr("\n== part 3: INV-71 factors vs the realised loop rate changes (fold 2, RS)")
    mk = json.loads((ROOT / "results/diag_margin_inv71_v1/markov.json").read_text())
    fac = {k: np.array(v) for k, v in mk["factors"].items()}
    L = json.loads((OUT / "grade.json").read_text())["part3_loops"]
    lam = {k: np.array(v["lam"]) for k, v in L.items()}
    obs = {k: v["obs"]["55:00"] for k, v in L.items()}
    chn = {k: v["chain"]["3300"] if "3300" in v["chain"] else v["chain"][3300] for k, v in L.items()}

    def shape(x):                                         # relative to tied, per period
        return x / x[:, [2]]
    rep = {}
    for lab, a, b, f in (("goal C1s -> C1s-sap (E4, B1a-as)", "E4 c1s (B1a-as)", "E4 sap (B1a-as)", "goal|SOG (C1s)"),
                         ("goal C1s -> C1s-sap (G4, B0)", "G4 c1s (B0)", "G4 sap (B0)", "goal|SOG (C1s)"),
                         ("block B0 -> B1a-as (+OT level), C1s", "G4 c1s (B0)", "E4 c1s (B1a-as)", "block (B0)"),
                         ("block B0 -> B1a-as (+OT level), sap", "G4 sap (B0)", "E4 sap (B1a-as)", "block (B0)")):
        realised = np.log(lam[a] / lam[b])                 # log rate removed by the repair
        wanted = np.log(fac[f])                            # log rate the INV-71 counterfactual removed
        rs_, ws_ = np.log(shape(lam[a]) / shape(lam[b])), np.log(shape(fac[f]))
        frac = float((rs_ * ws_).sum() / (ws_ * ws_).sum())    # projection of the realised shape change on the wanted one
        cf = G.tie(G.chain(lam[a] / fac[f])[3300])          # INV-71-style CF on this loop's rates
        rep[lab] = dict(obs_change=obs[b] - obs[a], chain_change=chn[b] - chn[a], factor_cf_change=cf - chn[a],
                        shape_fraction_realised=frac, realised_log=realised.round(4).tolist(), wanted_log=wanted.round(4).tolist())
        pr(f"  {lab}: observed tie change {obs[b] - obs[a]:+.4f}; chain on the realised loop rates {chn[b] - chn[a]:+.4f}; "
           f"INV-71 factor CF on the incumbent loop {cf - chn[a]:+.4f}; share of the factor's score shape realised {frac:.2f}")
    X["part3"] = rep
    (OUT / "extra.json").write_text(json.dumps(X, indent=1, default=float))
    pr("wrote", OUT / "extra.json")


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


# ------------------------------------------------------------------------------------- 6. post-goal dependence (added)
def post_goal(S, Gl, F, g, windows=((0, 30), (30, 60), (60, 120), (120, 300))):
    """Goals per team-hour in windows after a goal (same team / other team), relative to that game-set's regulation
    rate, for goals before 50:00 (regulation, RS; real without goalie-out goals). A memoryless (chain-like) process
    gives 1.0 everywhere; the engine's score effect alone moves 'other' up (the conceding side now trails)."""
    rs = ((F.gtype == 2) & F.pbp_ok).to_numpy()

    def calc(key, t, tm, n_games):
        o = np.lexsort((t, key))
        key, t, tm = key[o], t[o], tm[o]
        base = len(t) / (n_games * 3600.0 * 2)             # per team-second
        res = {}
        for a, b in windows:
            same = other = 0
            src = np.flatnonzero(t < 3000)
            for k in range(1, 12):
                j = src + k
                ok = j < len(t)
                j2, s2 = j[ok], src[ok]
                hit = (key[j2] == key[s2]) & (t[j2] - t[s2] >= a) & (t[j2] - t[s2] < b)
                same += int((hit & (tm[j2] == tm[s2])).sum())
                other += int((hit & (tm[j2] != tm[s2])).sum())
            expd = len(src) * (b - a) * base
            res[f"{a}-{b}s"] = dict(same=same / expd, other=other / expd, n_other=other, n_src=int(len(src)))
        return res
    sm = rs[S.gi.to_numpy()]
    x = Gl[(Gl.t < 3600) & sm[Gl.sim.to_numpy()]]
    sim = calc(x.sim.to_numpy(), x.t.to_numpy(), x.team.to_numpy(), int(sm.sum()))
    y = g[(g.game_time_s < 3600) & ~g.g_out & g.game_id.isin(F.game_id[rs])]
    real_ = calc(y.game_id.to_numpy(), y.game_time_s.to_numpy(), (~y.home_sc).astype(int).to_numpy(), int(rs.sum()))
    return dict(sim=sim, real=real_)


def main_post():
    Y = {}
    for fold in (1, 2):
        games, S, Gl, agg = G.load_rec(OUT / f"f{fold}")
        D1, F, g = G.real(fold, games)
        Y[f"f{fold}"] = post_goal(S, Gl, F, g)
        for w in Y[f"f{fold}"]["sim"]:
            s_, r_ = Y[f"f{fold}"]["sim"][w], Y[f"f{fold}"]["real"][w]
            se = r_["other"] / np.sqrt(max(r_["n_other"], 1))
            pr(f"  fold {fold} after a goal {w:9s}: same team sim {s_['same']:.3f} real {r_['same']:.3f} | "
               f"other team sim {s_['other']:.3f} real {r_['other']:.3f} (SE {se:.3f}, n {r_['n_other']})")
    (OUT / "post_goal.json").write_text(json.dumps(Y, indent=1, default=float))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "post":
    main_post()


# ------------------------------------------------------------------------------- 7. P2-tied deviation CF (added)
def main_cf():
    """DIAGNOSTIC: how much of the fold-2 rate-implied gap is the 2024-25 P2-tied real rate above the other seasons.
    Real fold-2 chain with the P2-tied real rate replaced by (a) fold 1's real P2-tied rate, (b) the fold-2 sim rate
    divided by fold 1's sim / real P2-tied ratio (the systematic part only)."""
    J = json.loads((OUT / "grade.json").read_text())
    m1, m2 = J["markov_f1"], J["markov_f2"]
    ls1, lr1 = np.array(m1["lam_sim"]), np.array(m1["lam_real"])
    ls2, lr2 = np.array(m2["lam_sim"]), np.array(m2["lam_real"])
    base_r, base_s = G.tie(G.chain(lr2)[3300]), G.tie(G.chain(ls2)[3300])
    out = dict(chain_real=base_r, chain_sim=base_s)
    for lab, v in (("real P2-tied = fold-1 real rate", lr1[1, 2]),
                   ("real P2-tied = fold-2 sim / fold-1 sim-real ratio", ls2[1, 2] / (ls1[1, 2] / lr1[1, 2]))):
        lam = lr2.copy()
        lam[1, 2] = v
        t = G.tie(G.chain(lam)[3300])
        out[lab] = dict(rate=float(v), tie55=t, gap_after=base_s - t, gap_change=(base_s - t) - (base_s - base_r))
        pr(f"  {lab}: rate {v:.3f} (fold-2 real {lr2[1, 2]:.3f}); real chain tie {t:.4f}; rate-implied gap "
           f"{100 * (base_s - t):+.2f} pp (was {100 * (base_s - base_r):+.2f})")
    for fold, (ls, lr) in ((1, (ls1, lr1)), (2, (ls2, lr2))):
        for lab, cells in (("P3 trailing + lead1", [(2, 0), (2, 1), (2, 3)]), ("P3 all", [(2, b) for b in range(5)]),
                           ("P2 tied", [(1, 2)]), ("P2 + P3 all", [(p, b) for p in (1, 2) for b in range(5)])):
            lam = ls.copy()
            for c in cells:
                lam[c] = lr[c]
            t = G.tie(G.chain(lam)[3300])
            out[f"f{fold} sim with real {lab}"] = t
            pr(f"  fold {fold}: sim chain with the real {lab} rates: tie55 {t:.4f} (sim chain {G.tie(G.chain(ls)[3300]):.4f}, "
               f"real chain {G.tie(G.chain(lr)[3300]):.4f})")
    # the C1s-sap loop (E4): which cells carry its remaining rate-implied gap
    lsap = np.array(J["part3_loops"]["E4 sap (B1a-as)"]["lam"])
    bs = G.tie(G.chain(lsap)[3300])
    out["sap_chain"] = bs
    for lab, cells in (("P3 trailing", [(2, 0), (2, 1)]), ("P3 lead1", [(2, 3)]), ("P3 all", [(2, b) for b in range(5)]),
                       ("P2 tied", [(1, 2)]), ("P2 all", [(1, b) for b in range(5)]), ("P1 all", [(0, b) for b in range(5)])):
        lam = lsap.copy()
        for c in cells:
            lam[c] = lr2[c]
        t = G.tie(G.chain(lam)[3300])
        out[f"sap with real {lab}"] = t
        pr(f"  E4 sap loop: chain with the real fold-2 {lab} rates: tie55 {t:.4f} (sap chain {bs:.4f}, change {t - bs:+.4f}; "
           f"rate-implied gap {100 * (bs - base_r):+.2f} pp)")
    (OUT / "cf_p2tied.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "cf":
    main_cf()
