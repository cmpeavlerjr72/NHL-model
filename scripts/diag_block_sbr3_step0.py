"""SB-R3 step 0: why the fitted block-rating response does not transfer (docs/models/block/experiments.md SB-R3, D29).

Training seasons 2021-22..2023-24 only (2023-24 = fold-1 test = last fold-2 training season). 2024-25 is NOT read.
Ratings b 1000, w 0.7 (ratings_v1); level M1_K500; B1 as SB-R1.

  0.1 per-season actual ES Q5-Q1 block-share spread by quintile of each as-of rating, 1,000 game-bootstrap CI;
      with B1 (fold-1 fit, fold-2 fit) predicted spread / ratio on each season
  0.2 B1 rating coefficients on fold-1 train vs fold-2 train (and each single season), model-based and game-cluster SEs
  0.3 by month and by rating exposure, pooled over the three seasons: the rating slopes refit with the rest of the fold-2
      B1 linear predictor as offset; rating SD and Fisher-information share by month
  0.4 rating coefficients with and without the arena factor (both folds)
  0.5 time-forward persistence: slope of realised blocks in games t+k on the as-of rating at t (B0 offset), k = 0 and
      k in 1..20 pooled (the B1p coefficient, per fold's training seasons), by season and by k
-> results/block_sb_r3/step0.json, docs/tests/block_sb_r3_step0_2026-10-16.md
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.block import data as D  # noqa: E402
from nhl_sim.block import models as BM  # noqa: E402
from nhl_sim.block import response as R  # noqa: E402

RES = Path("results/block_sb_r3")
OUTMD = Path("docs/tests/block_sb_r3_step0_2026-10-16.md")
W_, B_ = 0.7, 1000
LEVEL = "M1_K500"
SEAS = [20212022, 20222023, 20232024]
F = {1: [20212022, 20222023], 2: SEAS}
NB, BSEED = 1000, 20261016
IR = {"own_r": 10 + 6 + 3, "opp_r": 10 + 6 + 4, "arena_f": 10 + 6 + 5}  # column indices in design_b1


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def md(df, f=".4f"):
    return df.to_markdown(floatfmt=f)


def load():
    a = D.load_attempts(SEAS)
    games = pd.read_parquet(D.OUT / "games_v1.parquet")
    rt = pd.read_parquet(D.OUT / "ratings_v1.parquet")
    af = pd.read_parquet(D.OUT / "arena_v1.parquet")
    L = pd.read_parquet(D.OUT / "level_v1.parquet")
    L = L[L.construction == LEVEL]
    r = D.assemble(a, games, rt, af, W_, B_)
    ex = R.exposure(games)
    r = r.merge(ex, on=["game_id", "team_id"], how="left", validate="many_to_one")
    r = r.merge(ex.rename(columns={"team_id": "opp_id", "n_prior": "n_prior_opp"}), on=["game_id", "opp_id"], how="left",
                validate="many_to_one")
    return r.reset_index(drop=True), L   # all rows (B1 is fit on all rows, as SB-R1); diagnostics filter to gated rows


def offsets(r, L, fold):
    tr = r[r.season.isin(F[fold])]
    return D.row_offset(r, L, D.share_table(tr))


def spread(x, p, col, W, gp, G):
    tg = x.groupby(["game_id", "team"])[col].first()
    q = pd.qcut(tg.rank(method="first"), 5, labels=False)
    qq = x.join(q.rename("q"), on=["game_id", "team"]).q.to_numpy().astype(int)
    S = {}
    for k, v in (("a", x.y.to_numpy(float)), ("n", np.ones(len(x))), ("x", x[col].to_numpy(float)),
                 *((("p" + str(i), pi) for i, pi in enumerate(p)))):
        Z = np.zeros((G, 5))
        np.add.at(Z, (gp, qq), v)
        S[k] = Z

    def sp(key, Wt):
        m = (Wt @ S[key]) / (Wt @ S["n"])
        return m[..., 4] - m[..., 0], m
    a_sp, am = sp("a", np.ones(G))
    bs, _ = sp("a", W)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    x_sp, xm = sp("x", np.ones(G))
    out = dict(rating_q1=xm[0], rating_q5=xm[4], act_q=np.round(100 * am, 2).tolist(), act_spread_pp=100 * a_sp,
               ci_lo_pp=100 * lo, ci_hi_pp=100 * hi, act_pp_per_rating_unit=100 * a_sp / x_sp)
    for i in range(len(p)):
        p_sp, _ = sp("p" + str(i), np.ones(G))
        pb, _ = sp("p" + str(i), W)
        rb = pb / bs
        out[f"pred{i}_spread_pp"] = 100 * p_sp
        out[f"ratio{i}"] = p_sp / a_sp
        out[f"ratio{i}_lo"], out[f"ratio{i}_hi"] = np.percentile(rb, [2.5, 97.5])
    return out


def b1_fit(r, off, fold, cols_drop=(), cluster=True, mask=None):
    m = r.season.isin(F[fold]).to_numpy() if mask is None else mask
    X = BM.design_b1(r[m])
    keep = [i for i in range(X.shape[1]) if i not in [IR[c] for c in cols_drop]]
    f = R.fit_se(X[:, keep], r.y.to_numpy()[m], off[m], cluster=r.game_id.to_numpy()[m] if cluster else None)
    full = np.full(X.shape[1], np.nan)
    se1, se2 = full.copy(), full.copy()
    full[keep], se1[keep], se2[keep] = f["coef"], f["se_model"], f["se_cluster"]
    return full, se1, se2


def main():
    t0 = time.time()
    RES.mkdir(parents=True, exist_ok=True)
    print(now(), "load", flush=True)
    r, L = load()
    print(now(), "rows", len(r), flush=True)
    off = {k: offsets(r, L, k) for k in (1, 2)}
    X = BM.design_b1(r)
    out, md_ = {}, ["# SB-R3 step 0: diagnosis of the block-rating over-response (Lane B3, 2026-10-16)", "",
                    "Spec: `docs/models/block/experiments.md` SB-R3 step 0. Seasons 2021-22..2023-24 only; 2024-25 not read. "
                    "Ratings b 1000, w 0.7; level M1_K500. Gated rows (ES / PP / PK). 'for' = shooting team's as-of "
                    "blocked-against rating (`own_r`), 'against' = defending team's as-of blocks-for rating (`opp_r`). "
                    f"Generated {now()} by `scripts/diag_block_sbr3_step0.py`.", ""]

    # ---- 0.2 coefficients by fold and by single season (also fits used by 0.1 / 0.3)
    co = []
    fits = {}
    for nm, mask, k in (("fold-1 train (21-22, 22-23)", r.season.isin(F[1]).to_numpy(), 1),
                        ("fold-2 train (21-22..23-24)", r.season.isin(F[2]).to_numpy(), 2),
                        *((f"season {s} alone", (r.season == s).to_numpy(), 2) for s in SEAS)):
        c, s1, s2 = b1_fit(r, off[k], k, mask=mask)
        fits[nm] = c
        for v in ("own_r", "opp_r", "arena_f"):
            i = IR[v]
            sd = r.loc[mask, v].std()
            co.append(dict(fit=nm, feature=v, coef=c[i], se_model=s1[i], se_cluster=s2[i], rating_sd=sd, coef_x_sd=c[i] * sd))
    CO = pd.DataFrame(co)
    out["coef"] = CO.to_dict("records")
    print(now(), "0.2 done", flush=True)
    f1, f2 = fits["fold-1 train (21-22, 22-23)"], fits["fold-2 train (21-22..23-24)"]

    # ---- 0.1 per-season actual spread (ES), with B1 fold-1 / fold-2 predictions
    p1 = BM.sigmoid(X @ np.nan_to_num(f1) + off[1])
    p2 = BM.sigmoid(X @ np.nan_to_num(f2) + off[2])
    sp_rows = []
    for s in SEAS:
        m = ((r.season == s) & (r.grp == 0)).to_numpy()
        x = r[m]
        games = np.sort(x.game_id.unique())
        gp = np.searchsorted(games, x.game_id.to_numpy())
        G = len(games)
        W = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)
        for col, nm in (("own_rf_es", "for"), ("opp_ra_es", "against")):
            d = spread(x, [p1[m], p2[m]], col, W, gp, G)
            sp_rows.append(dict(season=s, side=nm, **d))
    SP = pd.DataFrame(sp_rows)
    out["spread"] = SP.to_dict("records")
    print(now(), "0.1 done", flush=True)

    # ---- 0.3 by month and by exposure (pooled over the three seasons), offset = fold-2 B1 minus rating terms
    m2 = (r.season.isin(F[2]) & (r.grp <= 2)).to_numpy()
    c_nr = np.nan_to_num(f2).copy()
    c_nr[[IR["own_r"], IR["opp_r"]]] = 0.0
    off_nr = X @ c_nr + off[2]
    mon = pd.to_datetime(r.date).dt.month.to_numpy()
    mlab = np.where(np.isin(mon, [5, 6]), "May-Jun", pd.to_datetime(r.date).dt.strftime("%m-%b").to_numpy())
    rows = []
    Xr = r[["own_r", "opp_r"]].to_numpy(float)
    p_full = p2
    info = (p_full * (1 - p_full))
    for lab in sorted(set(mlab)):
        mk = (mlab == lab) & m2
        f = R.fit_se(Xr[mk], r.y.to_numpy()[mk], off_nr[mk], cluster=r.game_id.to_numpy()[mk])
        rows.append(dict(month=lab, n=int(mk.sum()), coef_own=f["coef"][0], se_own=f["se_cluster"][0], coef_opp=f["coef"][1],
                         se_opp=f["se_cluster"][1], sd_own=Xr[mk, 0].std(), sd_opp=Xr[mk, 1].std(),
                         info_share_own=(info[mk] * Xr[mk, 0] ** 2).sum() / (info[m2] * Xr[m2, 0] ** 2).sum(),
                         info_share_opp=(info[mk] * Xr[mk, 1] ** 2).sum() / (info[m2] * Xr[m2, 1] ** 2).sum()))
    fall = R.fit_se(Xr[m2], r.y.to_numpy()[m2], off_nr[m2], cluster=r.game_id.to_numpy()[m2])
    rows.append(dict(month="all (check = B1 fold-2)", n=int(m2.sum()), coef_own=fall["coef"][0], se_own=fall["se_cluster"][0],
                     coef_opp=fall["coef"][1], se_opp=fall["se_cluster"][1], sd_own=Xr[m2, 0].std(), sd_opp=Xr[m2, 1].std(),
                     info_share_own=1.0, info_share_opp=1.0))
    MO = pd.DataFrame(rows)
    # by season x month-half (Oct-Dec vs Jan-Jun) for the season split
    sh = []
    for s in SEAS:
        for half, hm in (("Oct-Dec", np.isin(mon, [10, 11, 12])), ("Jan-Jun", ~np.isin(mon, [10, 11, 12]))):
            mk = (r.season == s).to_numpy() & hm & (r.grp <= 2).to_numpy()
            f = R.fit_se(Xr[mk], r.y.to_numpy()[mk], off_nr[mk], cluster=r.game_id.to_numpy()[mk])
            sh.append(dict(season=s, half=half, n=int(mk.sum()), coef_own=f["coef"][0], se_own=f["se_cluster"][0],
                           coef_opp=f["coef"][1], se_opp=f["se_cluster"][1], sd_own=Xr[mk, 0].std(), sd_opp=Xr[mk, 1].std()))
    SH = pd.DataFrame(sh)
    ex_rows = []
    eb = [(0, 10), (10, 20), (20, 40), (40, 60), (60, 200)]
    for side, col, ncol in (("for", "own_r", "n_prior"), ("against", "opp_r", "n_prior_opp")):
        for lo, hi in eb:
            mk = m2 & (r[ncol].to_numpy() >= lo) & (r[ncol].to_numpy() < hi)
            f = R.fit_se(Xr[mk], r.y.to_numpy()[mk], off_nr[mk], cluster=r.game_id.to_numpy()[mk])
            j = 0 if side == "for" else 1
            ex_rows.append(dict(side=side, exposure_games=f"{lo}-{hi - 1}", n=int(mk.sum()), coef=f["coef"][j],
                                se=f["se_cluster"][j], rating_sd=Xr[mk, j].std()))
    EX = pd.DataFrame(ex_rows)
    out.update(month=MO.to_dict("records"), season_half=SH.to_dict("records"), exposure=EX.to_dict("records"))
    print(now(), "0.3 done", flush=True)

    # ---- 0.4 with / without arena factor
    ar = []
    for k in (1, 2):
        cw, sw1, sw2 = b1_fit(r, off[k], k)
        cn, sn1, sn2 = b1_fit(r, off[k], k, cols_drop=("arena_f",))
        for v in ("own_r", "opp_r"):
            i = IR[v]
            ar.append(dict(fold=k, feature=v, coef_with_arena=cw[i], se_with=sw2[i], coef_without_arena=cn[i], se_without=sn2[i]))
        ar.append(dict(fold=k, feature="arena_f", coef_with_arena=cw[IR["arena_f"]], se_with=sw2[IR["arena_f"]],
                       coef_without_arena=np.nan, se_without=np.nan))
    AR = pd.DataFrame(ar)
    # correlation of ratings with the arena factor (team-game level, home team's own ratings vs its arena)
    cor = dict(own_r=float(np.corrcoef(r.own_r[m2], r.arena_f[m2])[0, 1]), opp_r=float(np.corrcoef(r.opp_r[m2], r.arena_f[m2])[0, 1]))
    out.update(arena=AR.to_dict("records"), arena_corr=cor)
    print(now(), "0.4 done", flush=True)

    # ---- 0.5 time-forward persistence (B0 offset fit on each fold's training rows)
    pers = {}
    prow = []
    for k in (1, 2):
        mk = r.season.isin(F[k]).to_numpy()
        rr = r[mk].reset_index(drop=True)
        m0 = BM.fit_b0(rr, off[k][mk])
        lp0 = BM.logit(BM.predict_b0(m0, rr, off[k][mk]))
        gk = (rr.grp <= 2).to_numpy()
        rr, lp0 = rr[gk].reset_index(drop=True), lp0[gk]
        cells = R.persistence_cells(rr, lp0)
        res = {}
        for side, rcol, tcol in (("own", "own_r", "team_id"), ("opp", "opp_r", "opp_id")):
            g0 = rr.assign(lp0=lp0).groupby([tcol, "game_id", "l0"]).agg(y=("y", "sum"), n=("y", "size"), x=(rcol, "first"),
                                                                          off=("lp0", "mean"), season=("season", "first")).reset_index()
            f0 = R.fit_se(g0[["x"]].to_numpy(), g0.y.to_numpy(), g0.off.to_numpy(), cluster=g0.game_id.to_numpy(),
                          n_trials=g0.n.to_numpy())
            cs = cells[cells.side == side]
            clus = cs.season.astype(str).to_numpy() + "_" + cs.team.astype(str).to_numpy()
            fk = R.fit_se(cs[["x"]].to_numpy(), cs.y.to_numpy(), cs.off.to_numpy(), cluster=clus, n_trials=cs.n.to_numpy())
            res[side] = dict(lag0=float(f0["coef"][0]), lag0_se=float(f0["se_cluster"][0]), fwd=float(fk["coef"][0]),
                             fwd_se_team_season=float(fk["se_cluster"][0]), n_cells=int(len(cs)))
            prow.append(dict(fold=k, side=side, scope="pooled", lag0=res[side]["lag0"], lag0_se=res[side]["lag0_se"],
                             fwd_1_20=res[side]["fwd"], fwd_se=res[side]["fwd_se_team_season"]))
            for s in F[k]:
                ms = (cs.season == s).to_numpy()
                fs = R.fit_se(cs[["x"]].to_numpy()[ms], cs.y.to_numpy()[ms], cs.off.to_numpy()[ms], cluster=clus[ms],
                              n_trials=cs.n.to_numpy()[ms])
                g0s = (g0.season == s).to_numpy()
                f0s = R.fit_se(g0[["x"]].to_numpy()[g0s], g0.y.to_numpy()[g0s], g0.off.to_numpy()[g0s],
                               cluster=g0.game_id.to_numpy()[g0s], n_trials=g0.n.to_numpy()[g0s])
                prow.append(dict(fold=k, side=side, scope=f"season {s}", lag0=f0s["coef"][0], lag0_se=f0s["se_cluster"][0],
                                 fwd_1_20=fs["coef"][0], fwd_se=fs["se_cluster"][0]))
            if k == 2:
                for kk in (1, 5, 10, 15, 20):
                    mkk = (cs.k == kk).to_numpy()
                    fkk = R.fit_se(cs[["x"]].to_numpy()[mkk], cs.y.to_numpy()[mkk], cs.off.to_numpy()[mkk], cluster=clus[mkk],
                                   n_trials=cs.n.to_numpy()[mkk])
                    prow.append(dict(fold=k, side=side, scope=f"lag k={kk} only", lag0=np.nan, lag0_se=np.nan,
                                     fwd_1_20=fkk["coef"][0], fwd_se=fkk["se_cluster"][0]))
        pers[k] = res
        print(now(), f"0.5 fold {k}", res, flush=True)
    PE = pd.DataFrame(prow)
    out.update(persistence={str(k): v for k, v in pers.items()}, persistence_table=PE.to_dict("records"))
    (RES / "persistence.json").write_text(json.dumps({str(k): {s: dict(coef=v[s]["fwd"], se=v[s]["fwd_se_team_season"])
                                                               for s in ("own", "opp")} for k, v in pers.items()}, indent=1))
    (RES / "step0.json").write_text(json.dumps(out, indent=1, default=float))

    md_ += ["## 0.1 Per-season actual ES Q5-Q1 spread (game-bootstrap 95% CI), with B1 predicted spreads", "",
            "pred0 / ratio0 = B1 fit on fold-1 train; pred1 / ratio1 = B1 fit on fold-2 train (in-sample for all three seasons). "
            "`act_pp_per_rating_unit` = actual spread / rating Q5-Q1 mean difference.", "",
            md(SP.drop(columns=["act_q"]).set_index(["season", "side"]), ".3f"), "",
            "Actual quintile shares (%):", "", md(SP[["season", "side", "act_q"]].assign(act_q=SP.act_q.astype(str)).set_index(["season", "side"])), "",
            "## 0.2 B1 rating coefficients by training set (raw rating units; SEs model-based and game-cluster)", "",
            md(CO.set_index(["fit", "feature"]), ".4f"), "",
            "## 0.3 Rating slopes by month (pooled 2021-22..2023-24; offset = the fold-2 B1 linear predictor without the rating terms)", "",
            md(MO.set_index("month"), ".4f"), "", "By season and half:", "", md(SH.set_index(["season", "half"]), ".4f"), "",
            "By rating exposure (team's games already played this season):", "", md(EX.set_index(["side", "exposure_games"]), ".4f"), "",
            "## 0.4 Rating coefficients with and without the arena factor (game-cluster SE)", "",
            md(AR.set_index(["fold", "feature"]), ".4f"), "",
            f"Row-level correlation with arena_f (fold-2 train): own_r {cor['own_r']:+.3f}, opp_r {cor['opp_r']:+.3f}.", "",
            "## 0.5 Time-forward persistence (B0 offset; lag 0 = rating at t on game t; fwd = games t+1..t+20 of the same season; "
            "SE clustered by team-season)", "", md(PE.set_index(["fold", "side", "scope"]), ".4f"), "",
            f"Elapsed {time.time() - t0:.0f} s.", ""]
    OUTMD.write_text("\n".join(md_), encoding="utf-8")
    print("\n".join(md_), flush=True)


if __name__ == "__main__":
    main()
