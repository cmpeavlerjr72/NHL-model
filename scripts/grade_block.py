"""SB-R1 blind grader (docs/models/block/experiments.md SB-R1). One code path scores every hash-labelled arm BEFORE
`labels_sealed.json` is opened.

Rows: gated = ES / PP / PK goalie-in attempts (grp 0..2); EN-for / EN-against rows are reported only.
Primary: Bernoulli LL per game vs B0, paired SE from a 1,000-resample game-block bootstrap (multinomial game weights).
Bias checks (fold 2 gates; fold 1 diagnostic): block share pred - actual overall +/-1.0 pp; per strength group +/-1.5 pp
(n >= 2,000); by month +/-2.0 pp (n >= 100 games); per arena reported (UNDERPOWERED < 1,500 attempts); regression of the
arena residual (pred - actual share) on the arena factor, slope with an arena-level jackknife SE (labelled), gating B1 / B2
only: |slope| <= 2 SE.
Responsiveness (ES): quintiles of each rating (shooting team's blocked-against; defending team's blocks-for) over team-games;
predicted Q5-Q1 spread of block share / actual spread in [0.8, 1.2].
References B0n (no level) and B0o (oracle level) are graded blind alongside and are never selectable.

    grade_block.py --fold 2   -> docs/tests/block_sb_r1_grade_2026-10-16.md (selection) + results json
    grade_block.py --fold 1   -> fold-1 diagnostic appended to the same file
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

RES = Path("results/block_sb_r1")
REPORT = Path("docs/tests/block_sb_r1_grade_2026-10-16.md")
ARMS = ("B0", "B1", "B2")
SEED = ("B2", "B2s2")
REFS = ("B0n", "B0o")
NB, BSEED = 1000, 20261016
OV_TOL, GRP_TOL, MON_TOL = 1.0, 1.5, 2.0
N_GRP_MIN, N_MONTH_GAMES, N_ARENA_MIN = 2000, 100, 1500
BAND = (0.8, 1.2)
GN = ("ES", "PP", "PK", "ENF", "ENA")
ARENA_GATE = ("B1", "B2", "B2s2")


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
    # responsiveness
    resp = {}
    for k in range(3):
        m = (r.grp == k).to_numpy()
        x = r[m]
        for col, nm in (("own_r", "for"), ("opp_r", "against")):
            tg = x.groupby(["game_id", "team"])[col].first()
            q = pd.qcut(tg.rank(method="first"), 5, labels=False)
            qq = x.join(q.rename("q"), on=["game_id", "team"]).q.to_numpy().astype(int)
            gpm = gp[m]
            S = {}
            for nm2, v in (("p", p[m]), ("a", y[m]), ("n", np.ones(m.sum()))):
                Z = np.zeros((G, 5))
                np.add.at(Z, (gpm, qq), v)
                S[nm2] = Z

            def ratio(Wt):
                pm = (Wt @ S["p"]) / (Wt @ S["n"])
                am = (Wt @ S["a"]) / (Wt @ S["n"])
                return (pm[..., 4] - pm[..., 0]) / (am[..., 4] - am[..., 0]), pm, am
            rt, pm, am = ratio(np.ones(G))
            br, _, _ = ratio(W)
            lo, hi = np.percentile(br, [2.5, 97.5])
            if k == 0:
                st = "PASS" if BAND[0] <= rt <= BAND[1] else "FAIL"
            else:
                st = "UNDERPOWERED (reported)" if (hi - lo) > (BAND[1] - BAND[0]) else "reported"
            resp[(GN[k], nm)] = dict(ratio=float(rt), lo=float(lo), hi=float(hi), status=st,
                                     pred_q=np.round(pm * 100, 3).tolist(), act_q=np.round(am * 100, 3).tolist())
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
    r, res, pair, name, G = cmd_grade(fold)
    h = {v: k for k, v in name.items()}
    hn = {v: k for k, v in h.items()}
    arms = [a for a in ARMS + (SEED[1],) + REFS if a in h]
    base = ARMS[0]
    rows = []
    for a in arms:
        R = res[h[a]]
        B = R["bias"]
        fails = B[B.status == "FAIL"]
        es = R["resp"][("ES", "for")]
        esa = R["resp"][("ES", "against")]
        q = pair[(pair.a == h[a]) & (pair.b == h[base])]
        rows.append(dict(arm=a, label=h[a], ll_att=R["ll_att"], ll_game_vs_B0=0.0 if a == base else float(q.diff_per_game.iloc[0]),
                         se=np.nan if a == base else float(q.se.iloc[0]),
                         share_overall_pp=float(B[B.level == "overall"].diff_pp.iloc[0]),
                         bias_fails=", ".join(f"{c} {v:+.2f}" for c, v in zip(fails.cell, fails.diff_pp)) or "none",
                         resp_es_for=es["ratio"], resp_es_against=esa["ratio"],
                         arena_slope=R["arena_slope"], arena_slope_se=R["arena_slope_se"]))
    S = pd.DataFrame(rows).set_index("arm")
    S["arena_gate"] = [("PASS" if abs(s_) <= 2 * e_ else "FAIL") if a in ARENA_GATE else "n/a (reported)"
                       for a, s_, e_ in zip(S.index, S.arena_slope, S.arena_slope_se)]
    S["resp_gate"] = [("PASS" if (BAND[0] <= f_ <= BAND[1] and BAND[0] <= g_ <= BAND[1]) else "FAIL")
                      for f_, g_ in zip(S.resp_es_for, S.resp_es_against)]
    S["bias_gate"] = np.where((S.bias_fails == "none") & S.arena_gate.isin(["PASS", "n/a (reported)"]), "PASS", "FAIL")
    S["eligible"] = (S.bias_gate == "PASS") & (S.resp_gate == "PASS") & S.index.isin(ARMS)
    s1, s2 = SEED
    floor = abs(float(pair[(pair.a == h[s1]) & (pair.b == h[s2])].diff_per_game.iloc[0]))
    L = [f"## Fold {fold} ({'selection' if fold == 2 else 'diagnostic'}): {r.season.iloc[0]} test, {int((r.grp <= 2).sum()):,} "
         f"gated attempts ({len(r):,} incl. EN), {G} games", "",
         f"Generated {now()} by `scripts/grade_block.py --fold {fold}` (blind: every label scored before `labels_sealed.json` was "
         f"opened; salt `SB-R1-2026-10-16`).", "", "### Summary", "", md(S.drop(columns=["label"]), ".4f"), "",
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
              "Responsiveness (Q5-Q1 spread of block share, pred / actual; 95% game-bootstrap CI; quintile shares in %):", "",
              md(pd.DataFrame({f"{k[0]} {k[1]}": {kk: (str(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}
                               for k, v in R["resp"].items()}).T, ".3f"), "",
              f"Arena (n >= {N_ARENA_MIN} attempts powered): slope of (pred - actual block share, pp) on the arena factor "
              f"{R['arena_slope']:+.2f} pp per unit (jackknife SE {R['arena_slope_se']:.2f}).", "", md(R["arena"], ".3f"), "",
              "Segments, strength states, periods (no gate):", "", md(R["segments"].set_index(["level", "cell"]), ".3f"), "",
              "Per shooting team (no gate):", "", md(R["shooting team"], ".3f"), "",
              "Per defending team (no gate):", "", md(R["defending team"], ".3f"), ""]
    sel = None
    if fold == 2:
        el = [a for a in ARMS if S.loc[a, "eligible"]]
        L += ["### Decision rule (fold 2)", "", f"- Eligible arms (every bias check, the arena slope gate and the ES responsiveness band): {el or 'none'}.",
              f"- Seed floor {floor:.5f} nats/game."]
        for a in reversed(el):
            simpler = [b for b in el if order[b] < order[a]]
            ok = True
            for b in simpler:
                q = P[(P.a == a) & (P.b == b)]
                dv, se = float(q.diff_per_game.iloc[0]), float(q.se.iloc[0])
                beat = dv > 2 * se and dv > floor
                L.append(f"- {a} vs {b}: {dv:+.5f} (SE {se:.5f}, floor {floor:.5f}) -> {'beats' if beat else 'does not beat'}")
                ok &= beat
            if ok:
                sel = a
                break
        L += [f"- **Selected: {sel}**" if sel else "- **No arm selected.**", ""]
    text = "\n".join(L) + "\n"
    if fold == 2:
        REPORT.write_text("# SB-R1 blind grade (Lane B, 2026-10-16)\n\nSpec: `docs/models/block/experiments.md` SB-R1. "
                          "Bias checks gate on fold 2; fold 1 is a diagnostic.\n\n" + text, encoding="utf-8")
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
