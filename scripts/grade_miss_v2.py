"""SM-R2 blind grader (docs/models/miss/experiments.md SM-R2; adapted from grade_miss.py of SM-R1). One code path scores every
hash-labelled arm BEFORE `labels_sealed.json` is opened.

Rows: gated = ES / PP / PK goalie-in unblocked attempts (grp 0..2); EN-for / EN-against rows are reported only. 4v4 / 3v3 are
reported by strength state with n (3v3 gates at stage 8, INV-35). y = miss (post / crossbar included, reported separately).
Primary: Bernoulli LL per game vs S0 on gated rows, paired SE from a 1,000-resample game-block bootstrap.
Bias checks (fold 2 gates; fold 1 diagnostic): miss share pred - actual overall +/-1.0 pp; per strength group +/-1.5 pp
(n >= 2,000); per location tier (high / medium / low danger) +/-1.5 pp (n >= 2,000); by month +/-2.0 pp (n >= 100 games);
per arena reported (UNDERPOWERED < 1,500 attempts) with the residual-on-factor slope (arena-level jackknife SE, labelled)
gating S1 / S2: |slope| <= 2 SE.
Responsiveness (ES, D32): decile slope ratio R = 1/b over the shooting team's road-only as-of miss rating, band [0.8, 1.2],
game-block bootstrap CI (underpowered flag; the point estimate gates). PP / PK R and the old Q5-Q1 ratio are reported only.
S0 is flat for teams and is never adoptable (D24); it is the stand-in if nothing else is eligible.

    grade_miss.py --fold 2   -> docs/tests/miss_sm_r2_grade_2026-10-16.md (selection) + results json
    grade_miss.py --fold 1   -> fold-1 diagnostic / D13 guard appended to the same file
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
from nhl_sim.shot_attribute.tables import TIER_NAMES, TIER_OF_CELL  # noqa: E402

RES = Path("results/miss_sm_r2")
REPORT = Path("docs/tests/miss_sm_r2_grade_2026-10-16.md")
ARMS = ("S0t", "S1t")           # complexity order: S0t < S1t (no booster, D31)
NB, BSEED = 1000, 20261016
OV_TOL, GRP_TOL, TIER_TOL, MON_TOL = 1.0, 1.5, 1.5, 2.0
N_GRP_MIN, N_MONTH_GAMES, N_ARENA_MIN = 2000, 100, 1500
BAND = (0.8, 1.2)
GN = ("ES", "PP", "PK", "ENF", "ENA")
ARENA_GATE = ("S1t",)


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
    tier = TIER_OF_CELL[r.cell.to_numpy()]
    for k, nm in enumerate(TIER_NAMES):
        m = (tier == k) & g
        rows.append(pp_row(p[m], y[m], "location tier", nm, TIER_TOL, m.sum() >= N_GRP_MIN))
    mon = pd.to_datetime(r.date).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = (mon == mo) & g
        ng = r.game_id[m].nunique()
        rows.append(pp_row(p[m], y[m], "month", mo, MON_TOL, ng >= N_MONTH_GAMES, ng))
    out["bias"] = pd.DataFrame(rows)
    A = pd.DataFrame({"arena": r.arena.to_numpy()[g], "res": (p - y)[g], "f": r.arena_f.to_numpy()[g]}).groupby("arena").agg(
        n=("res", "size"), resid_pp=("res", "mean"), arena_f=("f", "mean"))
    A["resid_pp"] *= 100
    A["status"] = np.where(A.n < N_ARENA_MIN, "UNDERPOWERED", "")
    Ap = A[A.n >= N_ARENA_MIN]
    sl = float(np.polyfit(Ap.arena_f, Ap.resid_pp, 1)[0])
    js = [np.polyfit(Ap.arena_f.drop(i), Ap.resid_pp.drop(i), 1)[0] for i in Ap.index]
    se = float(np.sqrt((len(js) - 1) / len(js) * ((np.array(js) - np.mean(js)) ** 2).sum()))
    out.update(arena=A, arena_slope=sl, arena_slope_se=se)
    resp = {}
    for k in range(3):
        m = (r.grp == k).to_numpy()
        x = r[m]
        col = "own_rf_es" if k == 0 else "own_r"
        rr = slope_ratio(p[m], y[m], x[col].to_numpy(float), np.ones(m.sum()), x.game_id.to_numpy(), n_buckets=10,
                         n_boot=NB if k == 0 else 200)
        tb = rr["table"]
        resp[GN[k]] = dict(R=rr["R"], lo=rr["ci"][0], hi=rr["ci"][1], b=rr["b"], old_q5q1=rr["old_q5q1"],
                           underpowered=rr["underpowered"], point=rr["status"],
                           pred_d=np.round(tb.pred.to_numpy() * 100, 3).tolist(),
                           act_d=np.round(tb.actual.to_numpy() * 100, 3).tolist())
    out["resp"] = resp
    seg = []
    pb_note = r.event.to_numpy() == "MISS"
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
    r, res, pair, name, G = cmd_grade(fold)
    h = {v: k for k, v in name.items()}
    hn = {v: k for k, v in h.items()}
    arms = [a for a in ARMS if a in h]
    base = ARMS[0]  # S0t
    rows = []
    for a in arms:
        R = res[h[a]]
        B = R["bias"]
        fails = B[B.status == "FAIL"]
        es = R["resp"]["ES"]
        q = pair[(pair.a == h[a]) & (pair.b == h[base])]
        rows.append(dict(arm=a, label=h[a], ll_att=R["ll_att"], ll_game_vs_S0=0.0 if a == base else float(q.diff_per_game.iloc[0]),
                         se=np.nan if a == base else float(q.se.iloc[0]),
                         share_overall_pp=float(B[B.level == "overall"].diff_pp.iloc[0]),
                         bias_fails=", ".join(f"{c} {v:+.2f}" for c, v in zip(fails.cell, fails.diff_pp)) or "none",
                         R_es=es["R"], R_lo=es["lo"], R_hi=es["hi"], old_q5q1=es["old_q5q1"], underpowered=bool(es["underpowered"]),
                         arena_slope=R["arena_slope"], arena_slope_se=R["arena_slope_se"]))
    S = pd.DataFrame(rows).set_index("arm")
    S["arena_gate"] = [("PASS" if abs(s_) <= 2 * e_ else "FAIL") if a in ARENA_GATE else "n/a (reported)"
                       for a, s_, e_ in zip(S.index, S.arena_slope, S.arena_slope_se)]
    S["resp_gate"] = ["PASS" if BAND[0] <= x <= BAND[1] else "FAIL" for x in S.R_es]
    S["bias_gate"] = np.where((S.bias_fails == "none") & S.arena_gate.isin(["PASS", "n/a (reported)"]), "PASS", "FAIL")
    S["eligible"] = (S.bias_gate == "PASS") & (S.resp_gate == "PASS") & S.index.isin(ARMS)
    S["adoptable"] = S.eligible & (S.index != base)
    floor = 0.0          # no seed-dependent arm: S0t and S1t are deterministic (D26)
    L = [f"## Fold {fold} ({'selection' if fold == 2 else 'diagnostic / D13 guard'}): {r.season.iloc[0]} test, "
         f"{int((r.grp <= 2).sum()):,} gated attempts ({len(r):,} incl. EN), {G} games", "",
         f"Generated {now()} by `scripts/grade_miss_v2.py --fold {fold}` (blind: every label scored before `labels_sealed.json` was "
         f"opened; salt `SM-R2-2026-10-16`). EN rows: S1t takes S0t (S1t is fit and applied on gated rows only; L33).", "",
         "### Summary", "", md(S.drop(columns=["label"]), ".4f"), "",
         "- Floor 0 (D26): no seed-dependent arm (logistic fits are deterministic)." , ""]
    P = pair.assign(a=pair.a.map(hn), b=pair.b.map(hn))
    order = {a: i for i, a in enumerate(arms)}
    P = P[P.a.map(order) > P.b.map(order)].sort_values(["a", "b"])
    P["z"] = P.diff_per_game / P.se
    L += ["### Pairwise paired per-game LL differences (first arm minus second; game-block bootstrap SE)", "",
          md(P.set_index(["a", "b"]), ".5f"), ""]
    for a in arms:
        R = res[h[a]]
        L += [f"### {a}", "", "Miss share, predicted vs actual:", "", md(R["bias"].set_index(["level", "cell"]), ".3f"), "",
              "Responsiveness, D32 slope ratio R = 1/b over deciles of the shooting team's road-only as-of miss rating (ES gates; "
              "PP / PK reported; 95% game-bootstrap CI; old Q5-Q1 endpoint ratio reported, not gating; decile miss shares in %):", "",
              md(pd.DataFrame({k: {kk: (str(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}
                               for k, v in R["resp"].items()}).T, ".3f"), "",
              f"Arena (n >= {N_ARENA_MIN} attempts powered): slope of (pred - actual miss share, pp) on the arena factor "
              f"{R['arena_slope']:+.2f} pp per unit (jackknife SE {R['arena_slope_se']:.2f}).", "", md(R["arena"], ".3f"), "",
              "Segments, strength states, periods (no gate):", "", md(R["segments"].set_index(["level", "cell"]), ".3f"), "",
              "Per shooting team (no gate):", "", md(R["shooting team"], ".3f"), "",
              "Per defending team (no gate):", "", md(R["defending team"], ".3f"), ""]
    sel = None
    if fold == 2:
        el = [a for a in ARMS if S.loc[a, "eligible"]]
        L += ["### Decision rule (fold 2)", "",
              f"- Eligible arms (every bias check, the arena slope gate and the ES responsiveness band R in [0.8, 1.2]): {el or 'none'}. "
              "S0t is flat for teams and is never adoptable (D24); it is the stand-in if nothing else is selected.",
              f"- Floor {floor:.5f}."]

        def pd_(a, b):
            q = pair[(pair.a == h[a]) & (pair.b == h[b])]
            return float(q.diff_per_game.iloc[0]), float(q.se.iloc[0])

        def beats(a, b):
            dv, se = pd_(a, b)
            ok = dv > 2 * se and dv > floor
            L.append(f"- {a} vs {b}: {dv:+.5f} (SE {se:.5f}, floor {floor:.5f}) -> {'beats' if ok else 'does not beat'}")
            return ok
        d, se = pd_("S1t", "S0t")
        L.append(f"- (reported) S1t - S0t = {d:+.5f} (SE {se:.5f}).")
        guard = None
        g1 = RES / "grade_fold1.json"
        if g1.exists():
            gs = {r_["arm"]: r_ for r_ in json.loads(g1.read_text())["summary"]}
            sv = gs["S1t"]
            q1 = [p_ for p_ in json.loads(g1.read_text())["pairs"] if p_["a"] == "S1t" and p_["b"] == "S0t"][0]
            gR = BAND[0] <= sv["R_es"] <= BAND[1]
            gA = sv["arena_gate"] == "PASS"
            gL = q1["diff_per_game"] >= -2 * q1["se"]
            guard = gR and gA and gL
            L.append(f"- D13 guard (fold 1): S1t R {sv['R_es']:.3f} in band {gR}; arena gate {sv['arena_gate']}; LL vs S0t "
                     f"{q1['diff_per_game']:+.5f} (SE {q1['se']:.5f}) not worse by > 2 SE {gL} -> **guard {'PASS' if guard else 'FAIL'}**.")
        else:
            L.append("- D13 guard: fold-1 grade not found.")
        if "S1t" in el and guard and d >= -2 * se:
            sel = "S1t"
        L += [f"- **Selected: {sel}**" if sel else "- **No adoptable arm selected; S0t replaces S0 as the stand-in (flat, not adoptable).**", ""]
    text = "\n".join(L) + "\n"
    if fold == 2:
        REPORT.write_text("# SM-R2 blind grade (Lane M, 2026-10-16)\n\nSpec: `docs/models/miss/experiments.md` SM-R2. "
                          "Bias checks gate on fold 2; fold 1 is a diagnostic and the D13 guard.\n\n" + text, encoding="utf-8")
    else:
        Path("docs/tests/miss_sm_r2_grade_fold1_2026-10-16.md").write_text(
            "# SM-R2 fold-1 grade (diagnostic / D13 guard; Lane M2, 2026-10-16)\n\n" + text, encoding="utf-8")
    (RES / f"grade_fold{fold}.json").write_text(json.dumps(dict(fold=fold, selected=sel, seed_floor=floor,
                                                                summary=S.reset_index().to_dict("records"),
                                                                pairs=P.to_dict("records")), indent=1, default=float))
    print(md(S.drop(columns=["label"]), ".4f"))
    print("\n".join(L[-12:]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, default=2, choices=[1, 2])
    write(ap.parse_args().fold)
