"""SB-R5 blind grader (docs/models/block/experiments.md SB-R5, D40 harmonised rule; copy of grade_block_v4 with the SB-R5 arm
set: comparator B0' (B0p), candidate B1a-as (B1aas), seed rerun B1aas2, references B0 (SB-R1) and B1a (SB-R4 fixed scale);
every rating column is the Ra construction). One code path scores every hash-labelled arm BEFORE
`labels_sealed.json` is opened.

Rows: gated = ES / PP / PK goalie-in attempts (grp 0..2); EN-for / EN-against rows are reported only.
Primary: Bernoulli LL per game vs B0, paired SE from a 1,000-resample game-block bootstrap (multinomial game weights).
Bias checks (fold 2 gates; fold 1 diagnostic): block share pred - actual overall +/-1.0 pp; per strength group +/-1.5 pp
(n >= 2,000); by month +/-2.0 pp (n >= 100 games); per arena reported (UNDERPOWERED < 1,500 attempts); regression of the
arena residual (pred - actual share) on the arena factor, slope with an arena-level jackknife SE (labelled), gating B1 / B2
only: |slope| <= 2 SE.
Responsiveness (ES, D32): decile slope ratio R = 1/b (nhl_sim.eval.responsiveness.slope_ratio) by each rating (shooting team's
blocked-against; defending team's blocks-for), R in [0.8, 1.2], game-block bootstrap CI. Because the rating column depends on the
arm and arms are hash-labelled, every label is scored on BOTH constructions' ratings (Rr, Ra) and the arm's own construction is read
after unsealing. The old Q5-Q1 endpoint ratio is reported (quintiles), not gating. PP / PK R and old ratios are reported only.
References B0n (no level) and B0o (oracle level) are graded blind alongside and are never selectable.

    grade_block_v5.py --fold 1   -> fold-1 D13 guard (run FIRST) -> docs/tests/block_sb_r5_grade_2026-10-21.md + json
    grade_block_v5.py --fold 2   -> fold-2 selection (reads the fold-1 guard), appended to the same file
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

RES = Path("results/block_sb_r5")
REPORT = Path("docs/tests/block_sb_r5_grade_2026-10-21.md")
ARMS = ("B0p", "B1aas")   # comparator (flat stand-in, D24 / D40) and candidate
SEED = ("B1aas", "B1aas2")
CONS = ("Ra",)
REFS = ("B0", "B1a")
NB, BSEED = 1000, 20261016
OV_TOL, GRP_TOL, MON_TOL = 1.0, 1.5, 2.0
N_GRP_MIN, N_MONTH_GAMES, N_ARENA_MIN = 2000, 100, 1500
BAND = (0.8, 1.2)
GN = ("ES", "PP", "PK", "ENF", "ENA")
ARENA_GATE = ("B1a", "B1aas", "B1aas2")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


def boot_weights(G):
    return np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)


def pp_row(p, y, level, cell, tol, gate, n_games=None):
    return dict(level=level, cell=cell, n=int(len(y)), n_games=n_games, pred_pct=100 * p.mean() if len(y) else np.nan,
                act_pct=100 * y.mean() if len(y) else np.nan,
                diff_pp=100 * (p.mean() - y.mean()) if len(y) else np.nan, tol=tol,
                status="UNDERPOWERED" if not gate else ("PASS" if abs(100 * (p.mean() - y.mean())) <= tol else "FAIL"))


def grade_label(p, r, W, gp, G):
    y = r.y.to_numpy().astype(float)
    g = (r.grp <= 2).to_numpy()
    out = {}
    ll = y * np.log(np.clip(p, 1e-12, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-12, 1))
    out["ll_game"] = np.bincount(gp[g], weights=ll[g], minlength=G)
    out["ll_att"] = float(ll[g].mean())
    rows = [pp_row(p[g], y[g], "overall", "ES+PP+PK", OV_TOL, True)]
    for k in range(3):
        m = (r.grp == k).to_numpy()
        rows.append(pp_row(p[m], y[m], "group", GN[k], GRP_TOL, m.sum() >= N_GRP_MIN))
    for k in (3, 4):
        m = (r.grp == k).to_numpy()
        rows.append(pp_row(p[m], y[m], "EN (reported)", GN[k], GRP_TOL, False))
    mon = pd.to_datetime(r.date).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = (mon == mo) & g
        ng = r.game_id[m].nunique()
        rows.append(pp_row(p[m], y[m], "month", mo, MON_TOL, ng >= N_MONTH_GAMES, ng))
    X = pd.DataFrame(rows)
    out["bias"] = X
    # arena
    A = pd.DataFrame({"arena": r.arena.to_numpy()[g], "res": (p - y)[g], "f": r.arena_f.to_numpy()[g]}).groupby("arena").agg(
        n=("res", "size"), resid_pp=("res", "mean"), arena_f=("f", "mean"))
    A["resid_pp"] *= 100
    A["status"] = np.where(A.n < N_ARENA_MIN, "UNDERPOWERED", "")
    Ap = A[A.n >= N_ARENA_MIN]
    sl = float(np.polyfit(Ap.arena_f, Ap.resid_pp, 1)[0])
    js = [np.polyfit(Ap.arena_f.drop(i), Ap.resid_pp.drop(i), 1)[0] for i in Ap.index]
    se = float(np.sqrt((len(js) - 1) / len(js) * ((np.array(js) - np.mean(js)) ** 2).sum()))
    out.update(arena=A, arena_slope=sl, arena_slope_se=se)
    # responsiveness: R (D32) per construction x group x side; old Q5-Q1 reported
    resp = {}
    for cn in CONS:
        for k in range(3):
            m = (r.grp == k).to_numpy()
            x = r[m]
            for nm, col in (("for", "own_rf_es" if k == 0 else "own_r"), ("against", "opp_ra_es" if k == 0 else "opp_r")):
                rr = slope_ratio(p[m], y[m], x[f"{col}_{cn}"].to_numpy(float), np.ones(m.sum()), x.game_id.to_numpy(),
                                 n_buckets=10, n_boot=NB if k == 0 else 200)
                tb = rr["table"]
                resp[(cn, GN[k], nm)] = dict(R=rr["R"], lo=rr["ci"][0], hi=rr["ci"][1], b=rr["b"], old_q5q1=rr["old_q5q1"],
                                             underpowered=rr["underpowered"], point=rr["status"],
                                             pred_d=np.round(tb.pred.to_numpy() * 100, 3).tolist(),
                                             act_d=np.round(tb.actual.to_numpy() * 100, 3).tolist())
    out["resp"] = resp
    # segments / strength states / teams (no gate)
    seg = []
    for nm, m in {"rebound": r.rebound.to_numpy(), "rush": r.rush.to_numpy(), "playoffs": (r.game_type == 3).to_numpy(),
                  "regular season": (r.game_type == 2).to_numpy(), "3v3 OT": ((r.st == 4) & (r.ptype == 1)).to_numpy(),
                  "OT (any)": (r.ptype == 1).to_numpy(), "home shooter": (r.is_home == 1).to_numpy(),
                  "away shooter": (r.is_home == 0).to_numpy(), "b2b shooter": (r.b2b_own == 1).to_numpy()}.items():
        m = m & g
        if m.any():
            seg.append(pp_row(p[m], y[m], "segment", nm, np.nan, True))
    for s_ in sorted(r.st.unique()):
        m = (r.st == s_).to_numpy() & g
        if m.any():
            seg.append(pp_row(p[m], y[m], "strength state", f"st {int(s_)}", np.nan, m.sum() >= N_GRP_MIN))
    for per in sorted(r.period.unique()):
        m = (r.period == per).to_numpy() & g
        seg.append(pp_row(p[m], y[m], "period", f"period {int(per)}", np.nan, True))
    out["segments"] = pd.DataFrame(seg)
    tm = []
    for nm, col in (("shooting team", "team_id"), ("defending team", "opp_id")):
        t = pd.DataFrame({"t": r[col].to_numpy()[g], "p": p[g], "y": y[g]}).groupby("t").agg(
            n=("p", "size"), pred_pct=("p", "mean"), act_pct=("y", "mean"))
        t["pred_pct"] *= 100
        t["act_pct"] *= 100
        t["diff_pp"] = t.pred_pct - t.act_pct
        out[nm] = t
    return out


def cmd_grade(fold):
    d = RES if fold == 2 else RES / "fold1"
    r = pd.read_parquet(d / f"fold{fold}_rows.parquet")
    games = np.sort(r.game_id.unique())
    gp = np.searchsorted(games, r.game_id.to_numpy())
    G = len(games)
    W = boot_weights(G)
    res = {}
    for f in sorted(d.glob(f"fold{fold}_pred_*.npy")):
        h = f.stem.rsplit("_", 1)[1]
        p = np.load(f).astype(np.float64)
        if p.shape != (len(r),):
            raise ValueError(f"{h}: shape {p.shape}")
        res[h] = grade_label(p, r, W, gp, G)
        print(now(), "graded", h, f"LL/att {res[h]['ll_att']:.5f}", flush=True)
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
    return r, res, pair, name, G


def write(fold):
    global ARM_CONS
    ARM_CONS = {a: "Ra" for a in ("B0p", "B0", "B1a", "B1aas", "B1aas2")}
    r, res, pair, name, G = cmd_grade(fold)
    h = {v: k for k, v in name.items()}
    hn = {v: k for k, v in h.items()}
    arms = [a for a in ARMS + (SEED[1],) + REFS if a in h]
    assert set(ARMS) <= set(arms)
    base = ARMS[0]
    rows = []
    for a in arms:
        R = res[h[a]]
        B = R["bias"]
        fails = B[B.status == "FAIL"]
        cn = ARM_CONS[a]
        es = R["resp"][(cn, "ES", "for")]
        esa = R["resp"][(cn, "ES", "against")]
        q = pair[(pair.a == h[a]) & (pair.b == h[base])]
        q0 = pair[(pair.a == h[a]) & (pair.b == h["B0"])]
        rows.append(dict(arm=a, label=h[a], ll_att=R["ll_att"], ll_game_vs_B0p=0.0 if a == base else float(q.diff_per_game.iloc[0]),
                         se=np.nan if a == base else float(q.se.iloc[0]),
                         ll_game_vs_B0=0.0 if a == "B0" else float(q0.diff_per_game.iloc[0]),
                         se_vs_B0=np.nan if a == "B0" else float(q0.se.iloc[0]),
                         share_overall_pp=float(B[B.level == "overall"].diff_pp.iloc[0]),
                         bias_fails=", ".join(f"{c} {v:+.2f}" for c, v in zip(fails.cell, fails.diff_pp)) or "none",
                         rating=cn, R_es_for=es["R"], R_for_lo=es["lo"], R_for_hi=es["hi"], R_es_against=esa["R"],
                         R_ag_lo=esa["lo"], R_ag_hi=esa["hi"], old_q5q1_for=es["old_q5q1"], old_q5q1_against=esa["old_q5q1"],
                         underpowered=bool(es["underpowered"] or esa["underpowered"]),
                         arena_slope=R["arena_slope"], arena_slope_se=R["arena_slope_se"]))
    S = pd.DataFrame(rows).set_index("arm")
    S["arena_gate"] = [("PASS" if abs(s_) <= 2 * e_ else "FAIL") if a in ARENA_GATE else "n/a (reported)"
                       for a, s_, e_ in zip(S.index, S.arena_slope, S.arena_slope_se)]
    S["resp_gate"] = [("PASS" if (BAND[0] <= f_ <= BAND[1] and BAND[0] <= g_ <= BAND[1]) else "FAIL")
                      for f_, g_ in zip(S.R_es_for, S.R_es_against)]
    S["bias_gate"] = np.where((S.bias_fails == "none") & S.arena_gate.isin(["PASS", "n/a (reported)"]), "PASS", "FAIL")
    S["eligible"] = (S.bias_gate == "PASS") & (S.resp_gate == "PASS") & S.index.isin(ARMS)
    s1, s2 = SEED
    floor = abs(float(pair[(pair.a == h[s1]) & (pair.b == h[s2])].diff_per_game.iloc[0]))
    L = [f"## Fold {fold} ({'selection' if fold == 2 else 'diagnostic'}): {r.season.iloc[0]} test, {int((r.grp <= 2).sum()):,} "
         f"gated attempts ({len(r):,} incl. EN), {G} games", "",
         f"Generated {now()} by `scripts/grade_block_v5.py --fold {fold}` (blind: every label scored before `labels_sealed.json` was "
         f"opened; salt `SB-R5-2026-10-21`).", "", "### Summary", "", md(S.drop(columns=["label"]), ".4f"), "",
         f"- Seed floor |{s1} - {s2}| = {floor:.5f} nats/game. References (never selectable): {list(REFS)}.", ""]
    P = pair.assign(a=pair.a.map(hn), b=pair.b.map(hn))
    order = {a: i for i, a in enumerate(arms)}
    P = P[P.a.map(order) > P.b.map(order)].sort_values(["a", "b"])
    P["z"] = P.diff_per_game / P.se
    L += ["### Pairwise paired per-game LL differences (second row arm minus first; game-block bootstrap SE)", "",
          md(P.set_index(["a", "b"]), ".4f"), ""]
    for a in arms:
        R = res[h[a]]
        L += [f"### {a}", "", "Block share, predicted vs actual:", "", md(R["bias"].set_index(["level", "cell"]), ".3f"), "",
              f"Responsiveness, D32 slope ratio R = 1/b over deciles of the as-of rating ({ARM_CONS[a]} ratings; "
              "gate = ES rows of that construction; 95% game-bootstrap CI; old Q5-Q1 endpoint ratio reported, not gating; decile "
              "block shares in %):", "",
              md(pd.DataFrame({" ".join(k): {kk: (str(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}
                               for k, v in R["resp"].items() if k[0] == ARM_CONS[a]}).T, ".3f"), "",
              f"Arena (n >= {N_ARENA_MIN} attempts powered): slope of (pred - actual block share, pp) on the arena factor "
              f"{R['arena_slope']:+.2f} pp per unit (jackknife SE {R['arena_slope_se']:.2f}).", "", md(R["arena"], ".3f"), "",
              "Segments, strength states, periods (no gate):", "", md(R["segments"].set_index(["level", "cell"]), ".3f"), "",
              "Per shooting team (no gate):", "", md(R["shooting team"], ".3f"), "",
              "Per defending team (no gate):", "", md(R["defending team"], ".3f"), ""]
    sel = None
    S["vs_B0p_ok"] = [True if a == "B0p" else bool(S.loc[a, "ll_game_vs_B0p"] >= -2 * S.loc[a, "se"]) for a in S.index]
    if fold == 1:
        g = S.loc["B1aas"]
        guard = dict(R_in_band=bool(g.resp_gate == "PASS"), not_worse_than_B0p=bool(g.vs_B0p_ok),
                     bias_clean=bool(g.bias_gate == "PASS"))
        guard["pass"] = all(guard.values())
        L += ["### D13 guard (fold 1, D40 form) on B1a-as", "",
              f"- R in [0.8, 1.2]: {g.R_es_for:.3f} / {g.R_es_against:.3f} -> {guard['R_in_band']}",
              f"- not worse than B0' by > 2 SE: {g.ll_game_vs_B0p:+.5f} (SE {g.se:.5f}) -> {guard['not_worse_than_B0p']}",
              f"- bias clean (every bias check + arena slope gate): {guard['bias_clean']}",
              f"- **D13 guard {'PASS' if guard['pass'] else 'FAIL'}**", ""]
        (RES / "d13_guard.json").write_text(json.dumps(guard, indent=1))
    if fold == 2:
        guard = json.loads((RES / "d13_guard.json").read_text())
        el = bool(S.loc["B1aas", "eligible"] and guard["pass"])
        ok = bool(S.loc["B1aas", "vs_B0p_ok"])
        g = S.loc["B1aas"]
        L += ["### Decision (D40 harmonised rule, fold 2)", "",
              f"- B1a-as eligible (every fold-2 bias check, arena slope gate, R for / against in [0.8, 1.2], D13 guard on fold 1): "
              f"bias {g.bias_gate}, arena {g.arena_gate}, R {g.R_es_for:.3f} / {g.R_es_against:.3f} ({g.resp_gate}), "
              f"guard {'PASS' if guard['pass'] else 'FAIL'} -> {'eligible' if el else 'NOT eligible'}",
              f"- not worse than B0' by > 2 SE: {g.ll_game_vs_B0p:+.5f} nats/game (SE {g.se:.5f}) -> {ok}",
              f"- Seed floor |B1aas - B1aas2| = {floor:.6f} nats/game."]
        sel = "B1aas" if (el and ok) else None
        L += [f"- **Selected: {sel}**" if sel else "- **B1a-as not selected; blocks stay on the B0' stand-in.**", ""]
    text = "\n".join(L) + "\n"
    if fold == 1:
        REPORT.write_text("# SB-R5 blind grade (Lane B5, 2026-10-21)\n\nSpec: `docs/models/block/experiments.md` SB-R5. "
                          "Fold 1 (2023-24) carries the D13 guard and is graded first; fold 2 (2024-25) selects.\n\n" + text,
                          encoding="utf-8")
    else:
        with REPORT.open("a", encoding="utf-8") as fh:
            fh.write("\n" + text)
    (RES / f"grade_fold{fold}.json").write_text(json.dumps(dict(fold=fold, selected=sel, seed_floor=floor,
                                                                summary=S.reset_index().to_dict("records"),
                                                                pairs=P.to_dict("records")), indent=1, default=float))
    print(md(S.drop(columns=["label"]), ".4f"))
    print("\n".join(L[-10:]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, default=2, choices=[1, 2])
    write(ap.parse_args().fold)
