"""SL-R1 step 4: blind grading of the shot location x type arms (docs/models/shot_attribute/experiments.md SL-R1).

Reads hash-labelled probability matrices (n attempts x 78 joint classes) written by train_shot_attribute_v1.py and
scores every label with one code path BEFORE the label map is opened:
  - joint multinomial LL per attempt and per game; every pairwise paired per-game difference with a game-block
    bootstrap SE (1,000 resamples)
  - bias checks: mean xG_ref per attempt pred / actual (overall +/-2%, per strength group n >= 2,000 +/-3%, by month
    n >= 100 games +/-4%); location tier shares (+/-1.5 pp overall and per strength group n >= 2,000); type shares
    (+/-1.5 pp overall); per arena predicted - actual mean distance and its slope on the arena factor
  - responsiveness: Q5 - Q1 spread of mean xG_ref per attempt, predicted / actual, team-game quintiles of the row's
    own shot-quality-for rating and, separately, the opponent's against rating; ES gates [0.8, 1.2]; PP / PK reported
  - segments (no gate): rebound, rush, 3v3 OT, playoffs, per team
Only then is labels_sealed.json opened to apply the decision rule (fold 2) or attach names (fold 1 diagnostic).

    grade_shot_attribute.py --fold 2      -> docs/tests/shot_attribute_sl_r1_grade_2026-10-16.md (+ results json)
    grade_shot_attribute.py --fold 1      -> fold-1 diagnostic section appended to the same file
    grade_shot_attribute.py --round r4 --fold 1|2   SL-R4 (L0s, L3c; seed pair L3c / L3cs2, floor 0 per D26). Fold 1
                                       is the D13 guard (every SL-R1 bias check must pass for L3c) and gets its own
                                       report; fold 2 decision: L3c is selected if eligible and not worse than L0s by
                                       > 2 SE (L0s is flat, never adoptable, D24). Per-state (5v5 / 4v4 / 3v3 split)
                                       xG and tier rows are REPORTED, not gated (not pre-registered as gates).
    grade_shot_attribute.py --round r5 --fold 2   SL-R5 (L0s, L3d; seed pair L3d / L3ds2, floor 0): same decision as
                                       r4 (the D28 guard is computed by train_shot_attribute_v5.py guard, not here)
    grade_shot_attribute.py --round r2 --fold 2|1   SL-R2 (L0m < L1m < L3m, seed pair L3m / L3ms2; references L0 and
                                       L0o (oracle level) graded blind but never selectable; arena reported, not gated, D23)
                                       -> docs/tests/shot_attribute_sl_r2_grade_2026-10-16.md
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.shot_attribute.models import load_rows  # noqa: E402
from nhl_sim.shot_attribute.tables import (GROUP_NAMES, N_CELL, N_CLASS, N_TYPE, TIER_NAMES, TIER_OF_CELL,  # noqa: E402
                                           TYPE_NAMES, cell_distance)

RES = Path("results/shot_attribute_r1")
REPORT = Path("docs/tests/shot_attribute_sl_r1_grade_2026-10-16.md")
TRAIN = {1: [20212022, 20222023], 2: [20212022, 20222023, 20232024]}
NB, BSEED = 1000, 20261016
XG_TOL, XG_GRP_TOL, XG_MONTH_TOL, MIX_PP = 0.02, 0.03, 0.04, 1.5
N_GRP_MIN, N_MONTH_GAMES, N_ARENA_MIN = 2000, 100, 1500
BAND = (0.8, 1.2)
ROUND = "r1"
ROUNDS = {"r1": dict(res="results/shot_attribute_r1", report="docs/tests/shot_attribute_sl_r1_grade_2026-10-16.md",
                     salt="SL-R1-2026-10-16", arms=("L0", "L1", "L2", "L3"), seed=("L3", "L3s2"), refs=(),
                     arena_gate=("L2", "L3", "L3s2"), title="SL-R1 blind grade (Lane A, 2026-10-16)", spec="SL-R1"),
          "r2": dict(res="results/shot_attribute_r2", report="docs/tests/shot_attribute_sl_r2_grade_2026-10-16.md",
                     salt="SL-R2-2026-10-16", arms=("L0m", "L1m", "L3m"), seed=("L3m", "L3ms2"), refs=("L0", "L0o"),
                     arena_gate=(), title="SL-R2 blind grade (Lane A2, 2026-10-16)", spec="SL-R2"),
          "r4": dict(res="results/shot_attribute_r4", report="docs/tests/shot_attribute_sl_r4_grade_2026-10-16.md",
                     report_f1="docs/tests/shot_attribute_sl_r4_grade_fold1_2026-10-16.md",
                     salt="SL-R4-2026-10-16", arms=("L0s", "L3c"), seed=("L3c", "L3cs2"), refs=(),
                     arena_gate=(), title="SL-R4 blind grade (Lane A4, 2026-10-16)", spec="SL-R4", decision="r4",
                     states=True, en_reported=True),
          "r5": dict(res="results/shot_attribute_r5", report="docs/tests/shot_attribute_sl_r5_grade_2026-10-16.md",
                     report_f1="docs/tests/shot_attribute_sl_r5_grade_fold1_2026-10-16.md",
                     salt="SL-R5-2026-10-16", arms=("L0s", "L3d"), seed=("L3d", "L3ds2"), refs=(),
                     arena_gate=(), title="SL-R5 blind grade (Lane A5, 2026-10-16)", spec="SL-R5", decision="r4",
                     states=True, en_reported=True)}
CFG = ROUNDS["r1"]
CELL_TIER = np.repeat(TIER_OF_CELL, N_TYPE)               # class -> tier
CLASS_TYPE = np.tile(np.arange(N_TYPE), N_CELL)           # class -> type
CLASS_CELL = np.repeat(np.arange(N_CELL), N_TYPE)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


def boot_weights(G):
    return np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)


def grade_label(P, r, xg, dcell, W, gp, G):
    cls = r.cls.to_numpy()
    grp = r.grp.to_numpy()
    out = {}
    ll = np.log(np.maximum(P[np.arange(len(cls)), cls], 1e-300))
    out["ll_game"] = np.bincount(gp, weights=ll, minlength=G)
    out["ll_att"] = float(ll.mean())
    xg_cls = xg[:, grp].T                                   # (n, 78) xG_ref of each class in the row's group
    pred_xg = (P * xg_cls).sum(1)
    act_xg = xg[cls, grp]
    rows = []
    rows.append(dict(level="overall", cell="all", n=len(r), pred=pred_xg.mean(), actual=act_xg.mean(), tol=XG_TOL,
                     gate=True))
    for g in range(5):
        m = grp == g
        rows.append(dict(level="group", cell=GROUP_NAMES[g], n=int(m.sum()), pred=pred_xg[m].mean() if m.any() else np.nan,
                         actual=act_xg[m].mean() if m.any() else np.nan, tol=XG_GRP_TOL, gate=m.sum() >= N_GRP_MIN))
    mon = pd.to_datetime(r.game_date_local).dt.to_period("M").astype(str).to_numpy()
    for mo in sorted(set(mon)):
        m = mon == mo
        ng = r.game_id[m].nunique()
        rows.append(dict(level="month", cell=mo, n=int(m.sum()), n_games=ng, pred=pred_xg[m].mean(),
                         actual=act_xg[m].mean(), tol=XG_MONTH_TOL, gate=ng >= N_MONTH_GAMES))
    X = pd.DataFrame(rows)
    X["rel"] = X.pred / X.actual - 1
    X["status"] = np.where(~X.gate, "UNDERPOWERED", np.where(X.rel.abs() <= X.tol, "PASS", "FAIL"))
    if CFG.get("en_reported"):           # D28: EN strata reported with n, gate at stage 8
        X.loc[(X.level == "group") & X.cell.isin(["ENF", "ENA"]), "status"] = "reported (EN, gates at stage 8, D28)"
    out["xg"] = X
    # tier and type shares
    tr = []
    Pt = np.stack([P[:, CELL_TIER == k].sum(1) for k in range(3)], 1)
    At = np.eye(3)[CELL_TIER[cls]]
    for nm, m in [("overall", np.ones(len(r), bool))] + [(GROUP_NAMES[g], grp == g) for g in range(5)]:
        for k in range(3):
            n = int(m.sum())
            d = (Pt[m, k].mean() - At[m, k].mean()) * 100 if n else np.nan
            gate = nm == "overall" or n >= N_GRP_MIN
            tr.append(dict(level=nm, tier=TIER_NAMES[k], n=n, pred_pct=Pt[m, k].mean() * 100 if n else np.nan,
                           actual_pct=At[m, k].mean() * 100 if n else np.nan, diff_pp=d,
                           status="UNDERPOWERED" if not gate else ("PASS" if abs(d) <= MIX_PP else "FAIL")))
    out["tier"] = pd.DataFrame(tr)
    if CFG.get("en_reported"):
        out["tier"].loc[out["tier"].level.isin(["ENF", "ENA"]), "status"] = "reported (EN, gates at stage 8, D28)"
    Py = np.stack([P[:, CLASS_TYPE == k].sum(1) for k in range(N_TYPE)], 1)
    Ay = np.eye(N_TYPE)[CLASS_TYPE[cls]]
    ty = pd.DataFrame({"type": TYPE_NAMES, "pred_pct": Py.mean(0) * 100, "actual_pct": Ay.mean(0) * 100})
    ty["diff_pp"] = ty.pred_pct - ty.actual_pct
    ty["status"] = np.where(ty.diff_pp.abs() <= MIX_PP, "PASS", "FAIL")
    out["type"] = ty
    if CFG.get("states"):
        st = r.st.to_numpy()
        srows = []
        for k, nm in enumerate(("5v5", "PP", "PK", "4v4", "3v3", "ENF", "ENA")):
            m = st == k
            if not m.any():
                continue
            srows.append(dict(state=nm, n=int(m.sum()), xg_pred=pred_xg[m].mean(), xg_act=act_xg[m].mean(),
                              xg_rel=pred_xg[m].mean() / act_xg[m].mean() - 1,
                              **{f"{TIER_NAMES[k2]}_diff_pp": (Pt[m, k2].mean() - At[m, k2].mean()) * 100 for k2 in range(3)},
                              status="reported (not a gate)" + (" UNDERPOWERED" if m.sum() < N_GRP_MIN else "")))
        out["states"] = pd.DataFrame(srows)
    # arena: predicted - actual mean (cell-representative) distance
    pd_ = P @ np.repeat(dcell, N_TYPE)
    ad_ = dcell[CLASS_CELL[cls]]
    A = pd.DataFrame({"arena": r.arena.to_numpy(), "res": pd_ - ad_, "res_raw": pd_ - r.d.to_numpy(),
                      "f": r.arena_f.to_numpy()}).groupby("arena").agg(n=("res", "size"), resid_ft=("res", "mean"),
                                                                        resid_raw_ft=("res_raw", "mean"), arena_f=("f", "mean"))
    A["status"] = np.where(A.n < N_ARENA_MIN, "UNDERPOWERED", "")
    Ap = A[A.n >= N_ARENA_MIN]
    out["arena"] = A
    out["arena_slope"] = float(np.polyfit(Ap.arena_f, Ap.resid_ft, 1)[0])
    # bootstrap of the arena slope over games is costly; arena-level jackknife SE instead (labelled)
    js = [np.polyfit(Ap.arena_f.drop(i), Ap.resid_ft.drop(i), 1)[0] for i in Ap.index]
    out["arena_slope_se"] = float(np.sqrt((len(js) - 1) / len(js) * ((np.array(js) - np.mean(js)) ** 2).sum()))
    # responsiveness
    resp = {}
    for g in range(3):
        m = grp == g
        if not m.any():
            continue
        x = r[m]
        for col, nm in (("own_r", "for"), ("opp_r", "against")):
            tg = x.groupby(["game_id", "team"])[col].first()
            q = pd.qcut(tg.rank(method="first"), 5, labels=False)
            qq = x.join(q.rename("q"), on=["game_id", "team"]).q.to_numpy().astype(int)
            gpm = gp[m]
            S = {}
            for nm2, v in (("p", pred_xg[m]), ("a", act_xg[m]), ("n", np.ones(m.sum()))):
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
            if g == 0:
                st = "PASS" if BAND[0] <= rt <= BAND[1] else "FAIL"
            else:
                st = "UNDERPOWERED (reported)" if (hi - lo) > (BAND[1] - BAND[0]) else "reported"
            resp[(GROUP_NAMES[g], nm)] = dict(ratio=float(rt), lo=float(lo), hi=float(hi), status=st,
                                              pred_q=np.round(pm, 5).tolist(), act_q=np.round(am, 5).tolist())
    out["resp"] = resp
    # segments
    seg = {"rebound": r.rebound.to_numpy(), "rush": r.rush.to_numpy(),
           "3v3 OT": ((r.st == 4) & (r.ptype == 1)).to_numpy(), "playoffs": (r.game_type == 3).to_numpy(),
           "regular season": (r.game_type == 2).to_numpy()}
    sr = []
    for nm, m in seg.items():
        if not m.any():
            continue
        sr.append(dict(segment=nm, n=int(m.sum()), xg_pred=pred_xg[m].mean(), xg_act=act_xg[m].mean(),
                       xg_rel=pred_xg[m].mean() / act_xg[m].mean() - 1,
                       high_pred_pct=Pt[m, 0].mean() * 100, high_act_pct=At[m, 0].mean() * 100,
                       low_pred_pct=Pt[m, 2].mean() * 100, low_act_pct=At[m, 2].mean() * 100))
    out["segments"] = pd.DataFrame(sr)
    t = pd.DataFrame({"team_id": r.team_id.to_numpy(), "p": pred_xg, "a": act_xg}).groupby("team_id").agg(
        n=("p", "size"), xg_pred=("p", "mean"), xg_act=("a", "mean"))
    t["rel"] = t.xg_pred / t.xg_act - 1
    out["teams"] = t
    return out


def cmd_grade(fold):
    d = RES if fold == 2 else RES / "fold1"
    r = pd.read_parquet(d / f"fold{fold}_rows.parquet")
    xg = np.load(Path("data/processed/shot_attribute") / f"xg_ref_v1_f{fold}.npy")
    tr = load_rows(TRAIN[fold])
    tr = tr[~tr.blocked]
    dcell = cell_distance(tr.cell.to_numpy(), tr.sx.to_numpy(), tr.sy.to_numpy())
    games = np.sort(r.game_id.unique())
    gp = np.searchsorted(games, r.game_id.to_numpy())
    G = len(games)
    W = boot_weights(G)
    files = sorted(d.glob(f"fold{fold}_pred_*.npy"))
    res = {}
    for f in files:
        h = f.stem.rsplit("_", 1)[1]
        P = np.load(f).astype(np.float64)
        if P.shape != (len(r), N_CLASS):
            raise ValueError(f"{h}: shape {P.shape}")
        res[h] = grade_label(P, r, xg, dcell, W, gp, G)
        print(now(), "graded", h, f"LL/att {res[h]['ll_att']:.5f}", flush=True)
    hs = sorted(res)
    pair = []
    for i in hs:
        for j in hs:
            if i == j:
                continue
            dv = res[i]["ll_game"] - res[j]["ll_game"]
            pair.append(dict(a=i, b=j, diff_per_game=dv.mean(), se=float(np.std(W @ dv / G))))
    pair = pd.DataFrame(pair)
    # ---------------------------------------------------------------- unseal
    lab = json.loads((d / "labels_sealed.json").read_text())
    name = {v: k for k, v in lab.items()}
    print(now(), "unsealed", name, flush=True)
    return r, res, pair, name, dcell, G


def summary_tables(res, pair, name, fold, G):
    base = CFG["arms"][0]
    arms = [a for a in CFG["arms"] + (CFG["seed"][1],) + CFG["refs"] if a in name.values()]
    h = {v: k for k, v in name.items()}
    L = []
    rows = []
    for a in arms:
        R = res[h[a]]
        X = R["xg"]
        tier = R["tier"]
        ty = R["type"]
        xg_fail = X[X.status == "FAIL"]
        es = R["resp"].get(("ES", "for"), {})
        esa = R["resp"].get(("ES", "against"), {})
        p = pair[(pair.a == h[a]) & (pair.b == h[base])]
        rows.append(dict(arm=a, label=h[a], ll_att=R["ll_att"], **{f"ll_game_vs_{base}": 0.0 if a == base else float(p.diff_per_game.iloc[0])},
                         se=np.nan if a == base else float(p.se.iloc[0]),
                         xg_overall=float(X[X.level == "overall"].rel.iloc[0]),
                         xg_fails=", ".join(f"{c} {v:+.2%}" for c, v in zip(xg_fail.cell, xg_fail.rel)) or "none",
                         tier_fails=", ".join(f"{lv}/{t} {v:+.2f}" for lv, t, v in zip(*[tier[tier.status == 'FAIL'][c] for c in ('level', 'tier', 'diff_pp')])) or "none",
                         type_fails=", ".join(f"{t} {v:+.2f}" for t, v in zip(ty[ty.status == 'FAIL'].type, ty[ty.status == 'FAIL'].diff_pp)) or "none",
                         resp_es_for=es.get("ratio"), resp_es_against=esa.get("ratio"),
                         arena_slope=R["arena_slope"], arena_slope_se=R["arena_slope_se"]))
    S = pd.DataFrame(rows).set_index("arm")
    s0 = S.loc[base, "arena_slope"]
    S[f"arena_slope_ratio_vs_{base}"] = S.arena_slope / s0
    S["arena_gate"] = [("PASS" if abs(v) <= 0.3 else "FAIL") if a in CFG["arena_gate"] else "n/a (reported)"
                       for a, v in S[f"arena_slope_ratio_vs_{base}"].items()]
    S["resp_gate"] = [("PASS" if (BAND[0] <= f_ <= BAND[1] and BAND[0] <= g_ <= BAND[1]) else "FAIL")
                      for f_, g_ in zip(S.resp_es_for, S.resp_es_against)]
    S["bias_gate"] = np.where((S.xg_fails == "none") & (S.tier_fails == "none") & (S.type_fails == "none")
                              & S.arena_gate.isin(["PASS", "n/a (reported)"]), "PASS", "FAIL")
    S["eligible"] = (S.bias_gate == "PASS") & (S.resp_gate == "PASS") & S.index.isin(CFG["arms"])
    return S, arms, h


def write(fold):
    r, res, pair, name, dcell, G = cmd_grade(fold)
    S, arms, h = summary_tables(res, pair, name, fold, G)
    s1, s2 = CFG["seed"]
    floor = abs(float(pair[(pair.a == h[s1]) & (pair.b == h[s2])].diff_per_game.iloc[0])) if s2 in h else np.nan
    L = [f"## Fold {fold} ({'selection' if fold == 2 else 'diagnostic'}): {r.season.iloc[0]} test, {len(r):,} unblocked attempts, {G} games", "",
         f"Generated {now()} by `scripts/grade_shot_attribute.py --round {ROUND} --fold {fold}` (blind: every label scored before "
         f"`labels_sealed.json` was opened; salt `{CFG['salt']}`).", "",
         "### Summary", "", md(S.drop(columns=["label"]), ".4f"), "",
         f"- Seed floor |{s1} - {s2}| = {floor:.4f} nats/game.",
         f"- Not selectable (references, graded blind with the arms): {list(CFG['refs']) or 'none'}.", ""]
    hn = {v: k for k, v in h.items()}
    P = pair.assign(a=pair.a.map(hn), b=pair.b.map(hn))
    order = {a: i for i, a in enumerate(arms)}
    P = P[P.a.map(order) > P.b.map(order)].sort_values(["a", "b"])
    P["z"] = P.diff_per_game / P.se
    L += ["### Pairwise paired per-game LL differences (more complex minus simpler; game-block bootstrap SE)", "",
          md(P.set_index(["a", "b"]), ".4f"), ""]
    for a in arms:
        R = res[h[a]]
        L += [f"### {a}", "", "xG_ref per attempt, predicted / actual:", "", md(R["xg"].set_index(["level", "cell"]), ".4f"), "",
              "Location tier shares (pp):", "", md(R["tier"].set_index(["level", "tier"]), ".3f"), "",
              "Type shares (pp):", "", md(R["type"].set_index("type"), ".3f"), "",
              *(["Per team-view state (5v5 / 4v4 / 3v3 split; REPORTED, not a pre-registered gate):", "",
                 md(R["states"].set_index("state"), ".4f"), ""] if "states" in R else []),
              "Responsiveness (Q5 - Q1 spread of mean xG_ref per attempt, pred / actual; 95% game-bootstrap CI):", "",
              md(pd.DataFrame({f"{k[0]} {k[1]}": {kk: (str(vv) if isinstance(vv, list) else vv) for kk, vv in v.items()}
                               for k, v in R["resp"].items()}).T, ".3f"), "",
              f"Arena (n >= {N_ARENA_MIN} attempts powered): slope of (pred - actual cell-representative distance) on "
              f"the arena factor {R['arena_slope']:+.2f} ft per unit (jackknife SE {R['arena_slope_se']:.2f}).", "",
              md(R["arena"], ".3f"), "", "Segments (no gate):", "", md(R["segments"].set_index("segment"), ".4f"), "",
              "Per team (no gate; xG_ref per attempt):", "", md(R["teams"], ".4f"), ""]
    sel = None
    d13 = None
    if CFG.get("decision") == "r4":
        c, b = CFG["arms"][1], CFG["arms"][0]
        q = P[(P.a == c) & (P.b == b)]
        dv, se = float(q.diff_per_game.iloc[0]), float(q.se.iloc[0])
        bias_ok = S.loc[c, "bias_gate"] == "PASS"
        if fold == 1:
            d13 = bool(bias_ok)
            L += ["### D13 guard (fold 1): every SL-R1 bias check must pass for L3c", "",
                  f"- {c} bias gate on fold 1: **{S.loc[c, 'bias_gate']}** (xG fails: {S.loc[c, 'xg_fails']}; tier fails: "
                  f"{S.loc[c, 'tier_fails']}; type fails: {S.loc[c, 'type_fails']}).",
                  f"- Responsiveness on fold 1 (reported): {S.loc[c, 'resp_es_for']:.3f} / {S.loc[c, 'resp_es_against']:.3f}.",
                  f"- {c} vs {b} LL per game {dv:+.4f} (SE {se:.4f}), reported.",
                  f"- **D13 guard: {'PASS' if d13 else 'FAIL'}**", ""]
        else:
            el = bool(S.loc[c, "eligible"])
            notworse = dv >= -2 * se
            sel = c if (el and notworse) else None
            L += [f"### Decision rule (fold 2, {CFG['spec']})", "",
                  f"- {c} eligible (every bias check and the ES responsiveness band): **{el}** (bias {S.loc[c, 'bias_gate']}, "
                  f"responsiveness {S.loc[c, 'resp_es_for']:.3f} / {S.loc[c, 'resp_es_against']:.3f} {S.loc[c, 'resp_gate']}).",
                  f"- {c} vs {b}: {dv:+.4f} nats/game (SE {se:.4f}); not worse by > 2 SE: **{notworse}**. Seed floor "
                  f"{floor:.4f} (deterministic booster, 0 per D26).",
                  f"- {b} is flat and not adoptable (D24).",
                  f"- **Selected: {sel}**" if sel else "- **No arm selected.**", ""]
    elif fold == 2:
        el = [a for a in CFG["arms"] if S.loc[a, "eligible"]]
        L += ["### Decision rule (fold 2)", "", f"- Eligible arms (every bias check and the ES responsiveness band): {el or 'none'}.",
              f"- Seed floor {floor:.4f} nats/game."]
        for a in reversed(el):
            simpler = [b for b in el if order[b] < order[a]]
            ok = True
            for b in simpler:
                q = P[(P.a == a) & (P.b == b)]
                dv, se = float(q.diff_per_game.iloc[0]), float(q.se.iloc[0])
                beat = dv > 2 * se and dv > floor
                L.append(f"- {a} vs {b}: {dv:+.4f} (SE {se:.4f}, floor {floor:.4f}) -> {'beats' if beat else 'does not beat'}")
                ok &= beat
            if ok:
                sel = a
                break
        L += [f"- **Selected: {sel}**" if sel else "- **No arm selected.**", ""]
    text = "\n".join(L) + "\n"
    if CFG.get("report_f1") and fold == 1:
        Path(CFG["report_f1"]).write_text(f"# {CFG['title']}: fold 1 (D13 guard)\n\nSpec: `docs/models/shot_attribute/"
                                          f"experiments.md` {CFG['spec']}.\n\n" + text, encoding="utf-8")
    elif fold == 2:
        REPORT.write_text(f"# {CFG['title']}\n\nSpec: `docs/models/shot_attribute/experiments.md` {CFG['spec']}. "
                          "Bias checks gate on fold 2; fold 1 is a diagnostic.\n\n" + text, encoding="utf-8")
    else:
        with REPORT.open("a", encoding="utf-8") as fh:
            fh.write("\n" + text)
    summ = dict(fold=fold, selected=sel, seed_floor=floor, d13_guard_pass=d13, summary=S.reset_index().to_dict("records"),
                pairs=P.to_dict("records"))
    (RES / f"grade_fold{fold}.json").write_text(json.dumps(summ, indent=1, default=float))
    print(md(S.drop(columns=["label"]), ".4f"))
    print("\n".join(L[-12:]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, default=2, choices=[1, 2])
    ap.add_argument("--round", default="r1", choices=sorted(ROUNDS))
    a = ap.parse_args()
    ROUND = a.round
    CFG = ROUNDS[a.round]
    RES, REPORT = Path(CFG["res"]), Path(CFG["report"])
    write(a.fold)
