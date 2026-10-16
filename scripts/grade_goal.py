"""G-R1 blind grader (docs/models/goal/experiments.md G-R1). One code path scores every hash-labelled arm BEFORE
`labels_sealed.json` is opened.

Rows: SOG with a goalie in net. Gated = 5v5, PP-for, PK (sg 0..2); 4v4 / 3v3 / EAF reported with n.
Primary: Bernoulli LL per game (gated rows) vs C0, paired SE from a 1,000-resample game-block bootstrap.
Bias checks (fold 2 gates; fold 1 diagnostic; gates.yaml g4_sv_pp = 0.5 pp), save% = 1 - P(goal):
  overall (gated) +/-0.5 pp; per gated group +/-1.0 pp (n >= 2,000); per location tier +/-1.0 pp (gated rows); by month
  +/-1.0 pp (n >= 100 games); goals from SOG, regular season, all in-scope rows: predicted / actual - 1 within +/-2%.
Responsiveness (D32): decile slope ratio R = 1/b by the goalie's as-of save rating and by the shooting team's as-of
finishing rating, gated rows, R in [0.8, 1.2], 1,000-resample game-block CI (UNDERPOWERED if wider than the band; the
point estimate gates, D18). 5v5-only R reported. C0 is flat by construction and not adoptable (D24).
Reported: per goalie (n >= 500 SOG), the G4 cell grid (goalie quintile x team-finishing quintile, n), per team,
segments, strength groups, periods.
Floor: |C2 - C2s2| per-game LL; a bit-identical retrain gives floor 0 (D26), labelled.

    grade_goal.py --fold 2   -> docs/tests/goal_g_r1_grade_2026-10-16.md (selection) + results json
    grade_goal.py --fold 1   -> fold-1 diagnostic and the D13 guard, appended
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402

RES = Path("results/goal_g_r1")
REPORT = Path("docs/tests/goal_g_r1_grade_2026-10-16.md")
ARMS = ("C0", "C1", "C2")            # complexity order C0 < C1 < C2
SEED = ("C2", "C2s2")
NB, BSEED = 1000, 20261016
OV_TOL, GRP_TOL, TIER_TOL, MON_TOL, GOALS_TOL = 0.5, 1.0, 1.0, 1.0, 2.0
N_GRP_MIN, N_MONTH_GAMES, N_GOALIE_MIN = 2000, 100, 500
BAND = (0.8, 1.2)
SG = ("5v5", "PP", "PK", "4v4", "3v3", "EAF")
TIERS = ("high", "medium", "low")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


def sv_row(p, y, level, cell, tol, gate, n_games=None):
    d = 100 * ((1 - p.mean()) - (1 - y.mean())) if len(y) else np.nan
    return dict(level=level, cell=cell, n=int(len(y)), n_games=n_games, sv_pred=100 * (1 - p.mean()) if len(y) else np.nan,
                sv_act=100 * (1 - y.mean()) if len(y) else np.nan, diff_pp=d, tol=tol,
                status=("UNDERPOWERED" if not gate else ("PASS" if abs(d) <= tol else "FAIL")) if np.isfinite(tol) else "reported")


def grade_label(p, r, gp, G):
    y = r.y.to_numpy().astype(float)
    g = (r.sg <= 2).to_numpy()
    out = {}
    ll = y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))
    out["ll_game"] = np.bincount(gp[g], weights=ll[g], minlength=G)
    out["ll_sog"] = float(ll[g].mean())
    rows = [sv_row(p[g], y[g], "overall", "5v5+PP+PK", OV_TOL, True)]
    for k in range(6):
        m = (r.sg == k).to_numpy()
        rows.append(sv_row(p[m], y[m], "group" if k <= 2 else "group (reported)", SG[k], GRP_TOL if k <= 2 else np.nan,
                           m.sum() >= N_GRP_MIN))
    for k in range(3):
        m = (r.tier == k).to_numpy() & g
        rows.append(sv_row(p[m], y[m], "tier", TIERS[k], TIER_TOL, True))
    mon = pd.to_datetime(r.date).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = (mon == mo) & g
        ng = r.game_id[m].nunique()
        rows.append(sv_row(p[m], y[m], "month", mo, MON_TOL, ng >= N_MONTH_GAMES, ng))
    out["bias"] = pd.DataFrame(rows)
    rs = (r.game_type == 2).to_numpy()
    ng = r.game_id[rs].nunique()
    gp_ = p[rs].sum() / ng
    ga_ = y[rs].sum() / ng
    gpct = 100 * (gp_ / ga_ - 1)
    out["goals"] = dict(games=int(ng), pred_per_game=gp_, act_per_game=ga_, diff_pct=gpct,
                        status="PASS" if abs(gpct) <= GOALS_TOL else "FAIL")
    resp = {}
    for nm, col in (("goalie", "g_r"), ("team", "t_r")):
        for scope, m in (("gated", g), ("5v5", (r.sg == 0).to_numpy())):
            rr = slope_ratio(p[m], y[m], r[col].to_numpy(float)[m], np.ones(m.sum()), r.game_id.to_numpy()[m],
                             n_buckets=10, n_boot=NB if scope == "gated" else 200)
            tb = rr["table"]
            resp[(nm, scope)] = dict(R=rr["R"], lo=rr["ci"][0], hi=rr["ci"][1], b=rr["b"], old_q5q1=rr["old_q5q1"],
                                     underpowered=rr["underpowered"], point=rr["status"],
                                     pred_goal_pct=np.round(tb.pred.to_numpy() * 100, 2).tolist(),
                                     act_goal_pct=np.round(tb.actual.to_numpy() * 100, 2).tolist())
    out["resp"] = resp
    seg = []
    for nm, m in {"rebound": r.rebound.to_numpy(), "rush": r.rush.to_numpy(), "playoffs": (r.game_type == 3).to_numpy(),
                  "regular season": rs, "home shooter": (r.is_home == 1).to_numpy(),
                  "away shooter": (r.is_home == 0).to_numpy(), "b2b shooter": (r.b2b_own == 1).to_numpy(),
                  "OT (any)": (r.ptype == 1).to_numpy()}.items():
        m = m & g
        if m.any():
            seg.append(sv_row(p[m], y[m], "segment", nm, np.nan, True))
    for per in sorted(r.period.unique()):
        m = (r.period == per).to_numpy() & g
        seg.append(sv_row(p[m], y[m], "period", f"period {int(per)}", np.nan, True))
    for sc in sorted(r.sc.unique()):
        m = (r.sc == sc).to_numpy() & g
        seg.append(sv_row(p[m], y[m], "score (shooter view)", f"{int(sc) - 3:+d}", np.nan, True))
    out["segments"] = pd.DataFrame(seg)
    # per goalie
    q = pd.DataFrame({"goalie": r.goalie_id.to_numpy()[g], "p": p[g], "y": y[g]}).groupby("goalie").agg(
        n=("p", "size"), xga=("p", "sum"), ga=("y", "sum"), pvar=("p", lambda v: (v * (1 - v)).sum()))
    q = q[q.n >= N_GOALIE_MIN]
    q["sv_pred"] = 100 * (1 - q.xga / q.n)
    q["sv_act"] = 100 * (1 - q.ga / q.n)
    q["diff_pp"] = q.sv_pred - q.sv_act
    q["z"] = (q.ga - q.xga) / np.sqrt(q.pvar)
    out["goalies"] = q.drop(columns="pvar").sort_values("n", ascending=False)
    # G4 grid
    gq = pd.qcut(pd.Series(r.g_r.to_numpy()[g]).rank(method="first"), 5, labels=False).to_numpy()
    tq = pd.qcut(pd.Series(r.t_r.to_numpy()[g]).rank(method="first"), 5, labels=False).to_numpy()
    c = pd.DataFrame({"gq": gq + 1, "tq": tq + 1, "p": p[g], "y": y[g]}).groupby(["gq", "tq"]).agg(
        n=("p", "size"), sv_pred=("p", "mean"), sv_act=("y", "mean"))
    c["sv_pred"] = 100 * (1 - c.sv_pred)
    c["sv_act"] = 100 * (1 - c.sv_act)
    c["diff_pp"] = c.sv_pred - c.sv_act
    out["g4"] = c
    for nm, col in (("shooting team", "team_id"), ("defending team", "opp_id")):
        t = pd.DataFrame({"t": r[col].to_numpy()[g], "p": p[g], "y": y[g]}).groupby("t").agg(
            n=("p", "size"), sv_pred=("p", "mean"), sv_act=("y", "mean"))
        t["sv_pred"] = 100 * (1 - t.sv_pred)
        t["sv_act"] = 100 * (1 - t.sv_act)
        t["diff_pp"] = t.sv_pred - t.sv_act
        out[nm] = t
    return out


def load_and_grade(fold):
    d = RES / f"fold{fold}"
    r = pd.read_parquet(d / f"fold{fold}_rows.parquet")
    games = np.sort(r.game_id.unique())
    gp = np.searchsorted(games, r.game_id.to_numpy())
    G = len(games)
    W = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)
    res, raw = {}, {}
    for f in sorted(d.glob(f"fold{fold}_pred_*.npy")):
        h = f.stem.rsplit("_", 1)[1]
        p = np.load(f).astype(np.float64)
        if p.shape != (len(r),):
            raise ValueError(f"{h}: shape {p.shape}")
        raw[h] = p
        res[h] = grade_label(p, r, gp, G)
        print(now(), "graded", h, f"LL/SOG {res[h]['ll_sog']:.5f}", flush=True)
    hs = sorted(res)
    pair = []
    for i in hs:
        for j in hs:
            if i != j:
                dv = res[i]["ll_game"] - res[j]["ll_game"]
                pair.append(dict(a=i, b=j, diff_per_game=dv.mean(), se=float(np.std(W @ dv / G))))
    pair = pd.DataFrame(pair)
    lab = json.loads((d / "labels_sealed.json").read_text())      # unsealed only now
    name = {v: k for k, v in lab.items()}
    print(now(), "unsealed", name, flush=True)
    return r, res, raw, pair, name, G


def write(fold):
    r, res, raw, pair, name, G = load_and_grade(fold)
    h = {v: k for k, v in name.items()}
    arms = [a for a in ARMS + (SEED[1],) if a in h]
    assert set(ARMS) <= set(arms)
    rows = []
    for a in arms:
        R = res[h[a]]
        B = R["bias"]
        fails = B[B.status == "FAIL"]
        gq, tq = R["resp"][("goalie", "gated")], R["resp"][("team", "gated")]
        q = pair[(pair.a == h[a]) & (pair.b == h["C0"])]
        bf = [f"{c} {v:+.2f}pp" for c, v in zip(fails.cell, fails.diff_pp)]
        if R["goals"]["status"] == "FAIL":
            bf.append(f"goals/game {R['goals']['diff_pct']:+.2f}%")
        rows.append(dict(arm=a, ll_sog=R["ll_sog"], ll_game_vs_C0=0.0 if a == "C0" else float(q.diff_per_game.iloc[0]),
                         se=np.nan if a == "C0" else float(q.se.iloc[0]),
                         sv_overall_pp=float(B[B.level == "overall"].diff_pp.iloc[0]), goals_pct=R["goals"]["diff_pct"],
                         bias_fails=", ".join(bf) or "none", R_goalie=gq["R"], Rg_lo=gq["lo"], Rg_hi=gq["hi"],
                         R_team=tq["R"], Rt_lo=tq["lo"], Rt_hi=tq["hi"],
                         underpowered=bool(gq["underpowered"] or tq["underpowered"])))
    S = pd.DataFrame(rows).set_index("arm")
    S["bias_gate"] = np.where(S.bias_fails == "none", "PASS", "FAIL")
    S["resp_gate"] = [("PASS" if (BAND[0] <= g_ <= BAND[1] and BAND[0] <= t_ <= BAND[1]) else "FAIL")
                      for g_, t_ in zip(S.R_goalie, S.R_team)]
    S.loc["C0", "resp_gate"] = "FAIL (flat, D24)"
    S["eligible"] = (S.bias_gate == "PASS") & (S.resp_gate == "PASS") & S.index.isin(ARMS)
    s1, s2 = SEED
    ident = bool(np.array_equal(raw[h[s1]], raw[h[s2]]))
    floor = 0.0 if ident else abs(float(pair[(pair.a == h[s1]) & (pair.b == h[s2])].diff_per_game.iloc[0]))
    L = [f"## Fold {fold} ({'selection' if fold == 2 else 'diagnostic + D13 guard'}): {r.season.iloc[0]} test, "
         f"{int((r.sg <= 2).sum()):,} gated SOG ({len(r):,} in scope), {G} games", "",
         f"Generated {now()} by `scripts/grade_goal.py --fold {fold}` (blind: every label scored before `labels_sealed.json` "
         "was opened; salt `G-R1-2026-10-16`).", "", "### Summary", "", md(S, ".4f"), "",
         f"- Seed floor |{s1} - {s2}| = {floor:.5f} nats/game ({'bit-identical retrain: floor 0, D26' if ident else 'retrain differs'}).",
         "- R = D32 decile slope ratio on gated rows (goalie: the goalie's as-of save rating; team: the shooting team's as-of "
         "finishing rating), 95% game-bootstrap CI. Goals = regular-season goals from SOG, predicted / actual - 1 (%).", ""]
    hn = {v: k for k, v in h.items()}
    P = pair.assign(a=pair.a.map(hn), b=pair.b.map(hn))
    order = {a: i for i, a in enumerate(arms)}
    P = P[P.a.map(order) > P.b.map(order)].sort_values(["a", "b"])
    P["z"] = P.diff_per_game / P.se
    L += ["### Pairwise per-game LL differences (a minus b; game-block bootstrap SE)", "", md(P.set_index(["a", "b"]), ".5f"), ""]
    for a in arms:
        R = res[h[a]]
        RR = pd.DataFrame({" ".join(k): {kk: (str(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}
                           for k, v in R["resp"].items()}).T
        L += [f"### {a}", "", "Save percentage, predicted vs actual:", "", md(R["bias"].set_index(["level", "cell"]), ".3f"), "",
              f"Goals from SOG, regular season: {R['goals']['pred_per_game']:.4f} predicted vs {R['goals']['act_per_game']:.4f} "
              f"actual per game ({R['goals']['games']} games): {R['goals']['diff_pct']:+.2f}% -> {R['goals']['status']}.", "",
              "Responsiveness (decile goal % predicted / actual):", "", md(RR, ".3f"), "",
              "Segments (no gate):", "", md(R["segments"].set_index(["level", "cell"]), ".3f"), ""]
        if a in ("C1", "C2"):
            L += [f"G4 cell grid (goalie save-rating quintile x shooting-team finishing quintile, gated rows; save %):", "",
                  md(R["g4"], ".3f"), "",
                  f"Per goalie (n >= {N_GOALIE_MIN} gated SOG; z = (GA - xGA) / sqrt(sum p(1-p))):", "",
                  md(R["goalies"], ".3f"), "",
                  f"Goalies with |z| > 2: {int((R['goalies'].z.abs() > 2).sum())} of {len(R['goalies'])} "
                  f"(expected about {0.0455 * len(R['goalies']):.1f} by chance).", "",
                  "Per shooting team (no gate):", "", md(R["shooting team"], ".3f"), "",
                  "Per defending team (no gate):", "", md(R["defending team"], ".3f"), ""]
    sel = None
    if fold == 2:
        el = [a for a in ARMS if S.loc[a, "eligible"]]
        L += ["### Decision rule (fold 2)", "",
              f"- Eligible arms (every bias check + R in [0.8, 1.2] for goalie and team; C0 flat, D24): {el or 'none'}.",
              f"- Seed floor {floor:.5f} nats/game."]

        def beats(a, b):
            q = pair[(pair.a == h[a]) & (pair.b == h[b])]
            dv, se = float(q.diff_per_game.iloc[0]), float(q.se.iloc[0])
            ok = dv > 2 * se and dv > floor
            L.append(f"- {a} vs {b}: {dv:+.5f} (SE {se:.5f}) -> {'beats' if ok else 'does not beat'}")
            return ok
        if "C2" in el and all([beats("C2", x) for x in ("C0", "C1") if x == "C0" or x in el]):
            sel = "C2"
        if sel is None and "C1" in el and beats("C1", "C0"):
            sel = "C1"
        L += [f"- **Selected: {sel}**" if sel else "- **No arm selected.**", ""]
    else:
        g2 = json.loads((RES / "grade_fold2.json").read_text())
        s2_ = g2.get("selected")
        if s2_:
            ok = S.loc[s2_, "resp_gate"] == "PASS"
            L += ["### D13 guard", "", f"- Fold-2 selection {s2_}: fold-1 R goalie {S.loc[s2_, 'R_goalie']:.3f}, team "
                  f"{S.loc[s2_, 'R_team']:.3f} -> {'PASS (in band)' if ok else 'FAIL'}.", ""]
        else:
            L += ["### D13 guard", "", "- No fold-2 selection; guard not applicable (fold 1 reported).", ""]
    text = "\n".join(L) + "\n"
    if fold == 2:
        REPORT.write_text("# G-R1 blind grade (Lane G, 2026-10-16)\n\nSpec: `docs/models/goal/experiments.md` G-R1. "
                          "Bias checks gate on fold 2; fold 1 is a diagnostic and carries the D13 guard.\n\n" + text,
                          encoding="utf-8")
    else:
        with REPORT.open("a", encoding="utf-8") as fh:
            fh.write("\n" + text)
    (RES / f"grade_fold{fold}.json").write_text(json.dumps(dict(fold=fold, selected=sel, seed_floor=floor, identical=ident,
                                                                summary=S.reset_index().to_dict("records"),
                                                                pairs=P.to_dict("records")), indent=1, default=float))
    print(md(S, ".4f"))
    print("\n".join(L[-8:]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, default=2, choices=[1, 2])
    write(ap.parse_args().fold)
