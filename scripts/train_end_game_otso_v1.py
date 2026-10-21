"""EG-R1 parts B and C (Lane H8b): 3v3 OT attempt level (INV-35) and the shootout (INV-67), offline.

    train_end_game_otso_v1.py ot_parity     training-season parity table + selection (no 2024-25 read)
    train_end_game_otso_v1.py ot_fold2      fold-2 parity of the selected level (reads 2024-25 3v3 rows; AFTER the commit)
    train_end_game_otso_v1.py so_fold1      shootout S1 mechanics inputs + S2 fold-1 s-grid (training seasons only)
    train_end_game_otso_v1.py so_fold2      blind fold-2 S1 bias checks and S2 vs S1 (reads 2024-25; AFTER the commit)

Outputs: results/end_game_otso_v1/ (gitignored) and docs/tests/end_game_eg_r1_otso_*.md pieces written by the
subcommands; every table is also printed.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.end_game import ot_level as OL  # noqa: E402

OUT = ROOT / "results" / "end_game_otso_v1"
OUT.mkdir(parents=True, exist_ok=True)
SLAB = {20212022: "2021-22", 20222023: "2022-23", 20232024: "2023-24", 20242025: "2024-25"}


def md(df, nd=4):
    return df.round(nd).to_markdown(index=False)


def ot_parity():
    seasons = [20212022, 20222023, 20232024]                  # training seasons only: 2024-25 is not loaded
    games = OL.game_table(seasons)
    rows = OL.load_rows(seasons)
    assert rows.season.max() <= 20232024
    res = {}
    tabs = []
    for fold in (1, 2):
        tr = OL.TRAIN[fold]
        specs = {**{k: v for k, v in OL.GRID.items()}, "E": ("E", None), "O": ("O", None)}
        gm = games[games.season.isin(tr)]
        meta, lev = OL.asof_levels(rows[rows.season.isin(tr)], gm, specs, train_seasons=tr)
        par = OL.level_parity(rows, meta, lev, OL.JUDGED[fold])
        par.insert(0, "fold", fold)
        tabs.append(par)
        sel = OL.select_level(par, OL.JUDGED[fold])
        res[fold] = sel
        np.savez(OUT / f"ot_levels_fold{fold}_train.npz", game_id=meta.game_id.to_numpy(), **lev)
    T = pd.concat(tabs, ignore_index=True)
    T["season"] = T.season.map(SLAB)
    T["pass_0.5pp"] = T.parity.abs() <= OL.TOL
    T["pred_per_team_hour"] = T.predicted / T.team_hours
    T["actual_per_team_hour"] = T.actual / T.team_hours
    T.to_csv(OUT / "ot_parity_training.csv", index=False)
    (OUT / "ot_selection.json").write_text(json.dumps(res, indent=1))
    print(md(T[["fold", "season", "level", "actual", "predicted", "parity", "pass_0.5pp", "team_hours",
                "games_with_3v3", "actual_per_team_hour", "pred_per_team_hour"]]))
    print(json.dumps(res, indent=1))
    # SE of the season-level count (Poisson) for context
    ctx = T[T.level == "O"][["season", "actual"]].drop_duplicates()
    ctx["poisson_se_rel"] = 1 / np.sqrt(ctx.actual)
    print(md(ctx))
    doc = ["# EG-R1 part B: 3v3 attempt level, training-season parity (Lane H8b, 2026-10-21)", "",
           "Training seasons only (2021-22 .. 2023-24); the 2024-25 rows were not loaded. Level = attempts per team-hour, "
           "regular-season 3v3 team-view rows, both teams. Parity = predicted / actual - 1 per genuine-prior training "
           "season; limit 0.5% (SA-R2 form). E and O are reported, never selectable (D35, L29). 2021-22 is burn-in "
           "(its prior is its own final rate) and is never judged.", "",
           md(T[["fold", "season", "level", "actual", "predicted", "parity", "pass_0.5pp", "team_hours",
                 "games_with_3v3", "actual_per_team_hour", "pred_per_team_hour"]]), "",
           "Poisson relative SE of the season's 3v3 attempt count (the floor under any parity read):", "", md(ctx), "",
           "Selection (rule in the experiments.md H8b execution note):", "", "```", json.dumps(res, indent=1), "```", "",
           "No construction passes the 0.5% limit in any judged season (the sampling error of a season's own count is "
           "about 2.6%, five times the limit). The fallback rule applies. Fold 2 (the served fold): the smallest max "
           "|parity| is M1 K500 (1.92%), 0.13 pp better than M1 K2000 and M2 H30, so **M1 K500 is selected**. Fold 1 "
           "(D13 guard): K2000 0.87%, K500 0.90%, within the 0.1 pp tie; the same M1 K500 is carried on fold 1 for "
           "consistency (labelled). The 2023-24 over-prediction (+1.9%) is the as-of level lagging a falling 3v3 "
           "attempt rate (55.7 vs 56.9 per team-hour); E (the era mean) is in-sample on 2023-24 and not selectable."]
    (ROOT / "docs" / "tests" / "end_game_eg_r1_otso_ot_parity_2026-10-21.md").write_text("\n".join(doc), encoding="utf-8")


def ot_fold2():
    """Fold-2 (2024-25) parity of the selected level M1 K500, plus the other grid members and O for reference."""
    sel = json.loads((OUT / "ot_selection.json").read_text())["2"]["selected"]
    seasons = [20212022, 20222023, 20232024, 20242025]
    games = OL.game_table(seasons)
    rows = OL.load_rows(seasons)
    specs = {**OL.GRID, "E": ("E", None), "O": ("O", None)}
    meta, lev = OL.asof_levels(rows, games, specs, train_seasons=OL.TRAIN[2])
    par = OL.level_parity(rows, meta, lev, [20242025])
    par["season"] = par.season.map(SLAB)
    par["per_team_hour_actual"] = par.actual / par.team_hours
    par["per_team_hour_pred"] = par.predicted / par.team_hours
    r = rows[rows.season == 20242025]
    par["goals"] = int(r.y_goal.sum())
    par["poisson_se_rel"] = 1 / np.sqrt(par.actual)
    par["selected"] = par.level == sel
    par["within_poisson_se"] = par.parity.abs() <= par.poisson_se_rel
    print(md(par))
    par.to_csv(OUT / "ot_parity_fold2.csv", index=False)
    # served form: A3g(row, old level) x exp(L_new - L_old) x exp(refit 3v3 cell), against the A3g-c table
    lev = OL.selected_level(2, sel)
    cell, info = OL.training_cell(2, lev)
    tr, te = OL.frames_3v3(2)
    bst = OL.booster(2)
    old_cell = json.loads((ROOT / "results/shot_attempt_r3/models/A3g-c.json").read_text())["cell"][4]
    mu_old, _ = OL.swapped_prediction(te, bst, pd.Series(te.level.to_numpy(), index=te.game_id.to_numpy()).groupby(level=0).first(), old_cell)
    mu_new, dl = OL.swapped_prediction(te, bst, lev, cell)
    y = te.y.to_numpy(float)
    rows_ = []
    for nm, mu in (("A3g-c (shared ES level, cell %.4f)" % old_cell, mu_old), ("own %s level, refit cell %.4f" % (sel, cell), mu_new)):
        rows_.append(dict(arm=nm, actual=y.sum(), predicted=mu.sum(), bias=mu.sum() / y.sum() - 1,
                          per60_combined_pred=2 * mu.sum() / (te.exposure_s.sum() / 3600), per60_combined_actual=2 * y.sum() / (te.exposure_s.sum() / 3600),
                          poisson_se_rel=1 / np.sqrt(y.sum())))
    served = pd.DataFrame(rows_)
    print(md(served))
    print("training cell", cell, info)
    served.to_csv(OUT / "ot_served_offline_fold2.csv", index=False)
    json.dump(dict(cell=cell, old_cell=old_cell, **info), open(OUT / "ot_cell_fold2.json", "w"))
    doc = ["# EG-R1 part B: fold-2 parity and offline served bias of the 3v3 level (Lane H8b, 2026-10-21)", "",
           "Read AFTER the training parity table and the selection were committed (e977e74). Fold 2 = 2024-25 regular season, "
           "3v3 team-view rows, both teams. Parity is of the level alone (reported); the gate is the closed-loop G2 3v3 cell.", "",
           md(par), "",
           "Offline served form on the same rows (A3g booster x exp(L_new - L_old) x exp(cell); the cell is the SA-R3 "
           "recipe refit on the fold-2 TRAINING rows with the own level in place; with the old level the same code "
           "reproduces the frozen A3g-c cell to 1e-12):", "", md(served), "",
           "Training diagnostics of the refit cell: " + json.dumps(info) + f"; frozen A3g-c cell {old_cell:.5f}, refit cell {cell:.5f}.",
           "", "UNDERPOWERED note: about 1,370 attempts and 160 goals in the season; the Poisson count error is 2.7%."]
    (ROOT / "docs" / "tests" / "end_game_eg_r1_otso_ot_fold2_2026-10-21.md").write_text(chr(10).join(doc), encoding="utf-8")
    return par


# =========================================================================== part C: the shootout
from nhl_sim.data.load import load_events  # noqa: E402
from nhl_sim.end_game import shootout as SO  # noqa: E402

S_GRID = (0.5, 0.75, 1.0, 1.25, 1.5)
RW, RB = 0.7, 50.0
NB = 1000
NL = chr(10)


def so_attempts(seasons) -> pd.DataFrame:
    """Regular-season shootout attempts (audit rule): SHOT / MISS / GOAL / FAILED_SHOT_ATTEMPT in period type SO,
    in sort order; round from strict alternation; shoot_home = shooter's team is the home team."""
    ev = load_events(seasons, columns=["game_id", "season", "game_type", "sort_order", "period_type", "event",
                                       "owner_is_home", "shooter_id", "goalie_id"])
    x = ev[(ev.period_type == "SO") & ev.event.isin(["SHOT", "MISS", "GOAL", "FAILED_SHOT_ATTEMPT"]) & (ev.game_type == 2)]
    x = x.sort_values(["game_id", "sort_order"], kind="stable").copy()
    x["k"] = x.groupby("game_id").cumcount()
    x["round"] = x.k // 2 + 1
    x["success"] = (x.event == "GOAL").astype(float)
    x["shoot_home"] = x.owner_is_home.astype(bool)
    g = OL.game_table(seasons)[["game_id", "date", "drop"]]
    x = x.merge(g, on="game_id", how="left", validate="many_to_one")
    if x.date.isna().any():
        raise ValueError("shootout attempt without a game date")
    alt = x.groupby("game_id").shoot_home.apply(lambda v: bool((v.to_numpy()[1:] != v.to_numpy()[:-1]).all()))
    assert alt.all(), "shootout attempts do not alternate"
    return x.drop(columns=["owner_is_home", "event", "period_type", "game_type"]).reset_index(drop=True)


def so_levels(att: pd.DataFrame, seasons):
    """As-of S1 inputs per regular-season game: p (M1 K500 over attempts) and the home-first share (M1, K = 100)."""
    games = OL.game_table(seasons)
    games = games[games.game_type == 2].reset_index(drop=True)
    gi = pd.Series(np.arange(len(games)), index=games.game_id.to_numpy())
    ix = gi.reindex(att.game_id.to_numpy()).to_numpy().astype(np.int64)
    xg = np.bincount(ix, weights=att.success.to_numpy(), minlength=len(games))
    mg = np.bincount(ix, minlength=len(games)).astype(float)
    first = att[att.k == 0]
    fi = gi.reindex(first.game_id.to_numpy()).to_numpy().astype(np.int64)
    xf = np.bincount(fi, weights=first.shoot_home.to_numpy(float), minlength=len(games))
    mf = np.bincount(fi, minlength=len(games)).astype(float)
    meta, p = SO.asof_m1(games, xg, mg, SO.K_SUCCESS)
    _, hf = SO.asof_m1(games, xf, mf, SO.K_FIRST)
    return pd.DataFrame({"game_id": games.game_id.to_numpy(), "season": games.season.to_numpy(), "p": p, "home_first": hf,
                         "created_at": meta.created_at.to_numpy(), "puck_drop": meta.puck_drop.to_numpy()})


def s1_bias(att: pd.DataFrame, lv: pd.DataFrame, season: int, n_sim: int = 2000, seed: int = 20261021):
    """S1 bias checks on one season of shootouts: per-attempt success, share past round 3 (> 6 attempts), winner home
    share. Predicted by simulating each actual shootout game with its as-of (p, home_first)."""
    a = att[att.season == season]
    gm = a.groupby("game_id").agg(n_att=("k", "size"), home_first=("shoot_home", "first"))
    goals = a[a.success == 1].groupby(["game_id", "shoot_home"]).size().unstack(fill_value=0).reindex(gm.index).fillna(0)
    gm["home_win"] = goals[True].to_numpy() > goals[False].to_numpy()
    l = lv.set_index("game_id").reindex(gm.index)
    rng = np.random.default_rng(seed)
    G = len(gm)
    u = rng.random((G * n_sim, 100))
    p = np.repeat(l.p.to_numpy(), n_sim)
    hf = np.repeat(l.home_first.to_numpy(), n_sim)
    hw, natt, gh, ga, hfirst = SO.shootout_home_win(rng.random(G * n_sim), u, p, p, hf)
    hw, natt = hw.reshape(G, n_sim), natt.reshape(G, n_sim)
    ev_ = dict(
        shootouts=G, attempts=len(a),
        success_actual=float(a.success.mean()), success_pred=float((l.p.to_numpy() * gm.n_att.to_numpy()).sum() / gm.n_att.sum()),
        past3_actual=float((gm.n_att > 6).mean()), past3_pred=float((natt > 6).mean()),
        home_win_actual=float(gm.home_win.mean()), home_win_pred=float(hw.mean()),
        mean_att_actual=float(gm.n_att.mean()), mean_att_pred=float(natt.mean()),
        home_first_actual=float(gm.home_first.mean()), home_first_pred=float(l.home_first.mean()))
    out = []
    for nm, k, lim in (("per-attempt success", "success", 0.02), ("share past round 3", "past3", 0.05),
                       ("winner home share", "home_win", 0.05)):
        d = ev_[k + "_pred"] - ev_[k + "_actual"]
        n_ = len(a) if k == "success" else G
        pa = ev_[k + "_actual"]
        se = float(np.sqrt(pa * (1 - pa) / n_))
        out.append(dict(check=nm, actual=ev_[k + "_actual"], predicted=ev_[k + "_pred"], diff_pp=100 * d, limit_pp=100 * lim,
                        PASS=bool(abs(d) <= lim), binomial_SE_pp=100 * se, label="UNDERPOWERED" if 2 * se > lim else ""))
    return pd.DataFrame(out), ev_


def so_s2(att, lv, rating, season, s):
    a = att[att.season == season]
    p1 = lv.set_index("game_id").p.reindex(a.game_id.to_numpy()).to_numpy()
    r = rating.reindex(a.index).to_numpy()
    p2 = SO._sigmoid(SO._logit(p1) + s * r)
    y = a.success.to_numpy()
    return a, p1, p2, y * np.log(p1) + (1 - y) * np.log(1 - p1), y * np.log(p2) + (1 - y) * np.log(1 - p2), r


def resp_R(y, pred, rating, gids, nb=NB, seed=20261021):
    """D32 responsiveness: decile buckets of the rating, n-weighted LS slope b of bucket-mean actual on bucket-mean
    predicted, R = 1 / b; game-block bootstrap CI."""
    def one(idx):
        q = pd.qcut(pd.Series(rating[idx]).rank(method="first"), 10, labels=False).to_numpy()
        n = np.bincount(q, minlength=10).astype(float)
        ya = np.bincount(q, weights=y[idx], minlength=10) / n
        pp = np.bincount(q, weights=pred[idx], minlength=10) / n
        w = n / n.sum()
        xb, yb = (w * pp).sum(), (w * ya).sum()
        return (w * (pp - xb) * (ya - yb)).sum() / (w * (pp - xb) ** 2).sum()
    b = one(np.arange(len(y)))
    rng = np.random.default_rng(seed)
    gu, gx = np.unique(gids, return_inverse=True)
    rows_by_g = [np.flatnonzero(gx == i) for i in range(len(gu))]
    bs = np.array([one(np.concatenate([rows_by_g[i] for i in rng.integers(0, len(gu), len(gu))])) for _ in range(nb)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    inv = lambda v: float(1 / v) if v > 0 else float("inf")  # noqa: E731
    return dict(slope_b=float(b), R=inv(b), R_lo=inv(hi), R_hi=inv(lo))


def s2_table(att, lv, rating, season, grid=S_GRID):
    rows = []
    for s in (0.0,) + tuple(grid):
        a, p1, p2, l1, l2, r = so_s2(att, lv, rating, season, s)
        d = l2 - l1
        rr = resp_R(a.success.to_numpy(), p2, r, a.game_id.to_numpy()) if s > 0 else {}
        rows.append(dict(s=s, n_attempts=len(a), ll_per_attempt=l2.mean(), ll_minus_S1=d.mean(),
                         se=d.std(ddof=1) / np.sqrt(len(d)) if s > 0 else 0.0, R=rr.get("R"), R_lo=rr.get("R_lo"),
                         R_hi=rr.get("R_hi"), slope_b=rr.get("slope_b"), sd_rating=float(np.std(r)),
                         label="UNDERPOWERED"))
    return pd.DataFrame(rows)


def pick_s(tab: pd.DataFrame):
    """D27 rule: among s within 2 SE of the best LL, the one whose |log R| is closest to 1 (s > 0 only)."""
    t = tab[tab.s > 0].copy()
    i = t.ll_minus_S1.idxmax()
    ok = t[t.ll_minus_S1 >= t.loc[i, "ll_minus_S1"] - 2 * t.loc[i, "se"]]
    ok = ok[np.isfinite(ok.R) & (ok.R > 0)]
    if ok.empty:
        return float(t.loc[i, "s"]), "no finite positive R; best LL"
    return float(ok.loc[np.abs(np.log(ok.R)).idxmin(), "s"]), "D27: closest |log R| to 1 among cells within 2 SE of the best LL"


def so_fold1():
    seasons = [20212022, 20222023, 20232024]
    att = so_attempts(seasons)
    assert att.season.max() <= 20232024
    lv = so_levels(att, seasons)
    rating = SO.asof_shooter_ratings(att, RW, RB)
    integ = att.groupby("season").agg(shootouts=("game_id", "nunique"), attempts=("k", "size"), success=("success", "mean"),
                                      null_shooter=("shooter_id", lambda v: int(v.isna().sum()))).reset_index()
    integ["season"] = integ.season.map(SLAB)
    lvs = lv[lv.game_id.isin(att.game_id)].groupby("season").agg(p_mean=("p", "mean"), home_first_asof=("home_first", "mean")).reset_index()
    lvs["season"] = lvs.season.map(SLAB)
    bias1, ev1 = s1_bias(att, lv, 20232024)
    tab = s2_table(att, lv, rating, 20232024)
    s_sel, why = pick_s(tab)
    out = dict(s_selected=s_sel, why=why, S_GRID=list(S_GRID), w=RW, b=RB)
    (OUT / "so_fold1.json").write_text(json.dumps(out, indent=1))
    print(md(integ)); print(md(lvs)); print(md(bias1)); print(md(tab)); print(out)
    doc = ["# EG-R1 part C: shootout, fold-1 table (Lane H8b, 2026-10-21)", "",
           "Training seasons only (2021-22 .. 2023-24); the 2024-25 events were not loaded. Fold 1 = train through 2022-23, "
           "test 2023-24 (about 80 shootouts, about 500 attempts: every cell here is UNDERPOWERED). Committed before any fold-2 grade.", "",
           "## Attempt data (audit rule: SO SHOT / MISS / GOAL / FAILED_SHOT_ATTEMPT, regular season; strict alternation asserted)", "", md(integ), "",
           "## As-of S1 inputs per season (mean over that season's shootout games): p = M1 K500 over attempts; home-first share = M1, K = 100 shootouts (labelled)", "", md(lvs), "",
           "## S1 bias checks on fold 1 (2023-24; the D13 guard; simulated from each shootout game's as-of inputs)", "", md(bias1), "",
           "## S2 (shooter rating, w 0.7, b 50 attempts, relative to the snapshot mean) on fold 1: per-attempt LL minus S1 with paired SE; R by the D32 recipe (decile buckets of the rating, 1,000 game-block bootstrap)", "",
           md(tab), "",
           f"S2 scale selected on fold 1: **s = {s_sel}** ({why}). The LL surface over s is flat; s is fixed here and carried unchanged to fold 2. "
           "The rating is the as-of shrunk log-odds relative to the as-of league mean, entered at the fixed scale s ('standardised' in the spec's grid wording means relative to the snapshot mean, not divided by its SD)."]
    (ROOT / "docs" / "tests" / "end_game_eg_r1_otso_so_fold1_2026-10-21.md").write_text(NL.join(doc), encoding="utf-8")


def so_fold2():
    s_sel = json.loads((OUT / "so_fold1.json").read_text())["s_selected"]
    seasons = [20212022, 20222023, 20232024, 20242025]
    att = so_attempts(seasons)
    lv = so_levels(att, seasons)
    rating = SO.asof_shooter_ratings(att, RW, RB)
    bias2, ev2 = s1_bias(att, lv, 20242025)
    tab = s2_table(att, lv, rating, 20242025, grid=(s_sel,))
    a = att[att.season == 20242025]
    p0 = lv.set_index("game_id").p.reindex(a.game_id.to_numpy()).to_numpy()
    c = pd.DataFrame({"s": a.shooter_id.to_numpy(), "y": a.success.to_numpy(), "p": p0}).groupby("s").agg(
        n=("y", "size"), g=("y", "sum"), e=("p", "sum"))
    cs = c[c.n >= 5]
    disp = float(((cs.g - cs.e) ** 2).sum() / (cs.e * (1 - cs.e / cs.n)).sum()) if len(cs) else float("nan")
    print(md(bias2)); print(md(tab)); print("dispersion", disp, len(cs))
    doc = ["# EG-R1 part C: shootout, blind fold-2 grade (Lane H8b, 2026-10-21)", "",
           f"Read AFTER the fold-1 table and the S2 scale (s = {s_sel}) were committed. Fold 2 = 2024-25 regular season.", "",
           "## S1 bias checks (UNDERPOWERED where 2 x binomial SE exceeds the limit)", "", md(bias2), "",
           "Other S1 quantities: " + json.dumps({k: round(v, 4) for k, v in ev2.items()}), "",
           "## S2 vs S1 (per-attempt LL difference with paired SE; R by D32)", "", md(tab), "",
           f"Shooter dispersion (squared deviation of goals from the S1 expectation over its binomial variance, shooters with >= 5 attempts, n = {len(cs)}): {disp:.2f} (1.0 = no shooter signal; the audit found 1.21 on training seasons). {a.shooter_id.nunique()} distinct shooters in the season.", "",
           "Nothing is served from S2 (the shooter order is chosen in game)."]
    (ROOT / "docs" / "tests" / "end_game_eg_r1_otso_so_fold2_2026-10-21.md").write_text(NL.join(doc), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ot_parity", "ot_fold2", "so_fold1", "so_fold2"])
    a = ap.parse_args()
    {"ot_parity": ot_parity, "ot_fold2": ot_fold2, "so_fold1": so_fold1, "so_fold2": so_fold2}[a.cmd]()
