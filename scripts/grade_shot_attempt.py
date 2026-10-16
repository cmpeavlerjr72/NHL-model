"""Blind grader for SA-R1 (INV-30), docs/models/shot_attempt/experiments.md SA-R1.

    grade_shot_attempt.py [--res results/shot_attempt_r1] [--out docs/tests/shot_attempt_sa_r1_grade_2026-10-15.md]

Scores every arm from hash-labelled prediction files (fold2_haz_<hash>.npy + fold2_meta_<hash>.json; a meta
latent_v > 0 means the arm is graded by the exact per-game shared-gamma (negative-multinomial) marginal). The blind
table is written first; labels are then revealed and the pre-registered rule is applied literally:
  - noise floor: game-block bootstrap (1,000) of paired per-game differences + the A3 seed-retrain |difference|;
  - an arm beats a simpler arm only if it wins by > 2 SE AND by > the seed floor;
  - eligibility: every fold-2 bias check passes AND the offline responsiveness band passes (both ratings);
  - selection: the most complex eligible arm that beats every simpler eligible arm.
Fold-1 bias checks are reported as a diagnostic (results/shot_attempt_r1/fold1).

SA-R2 (INV-31) extension, backward-compatible: --round SA-R2 adds the group-level arms (order A0 < A1 < A2 < A2g <
A5 < A4 < A3 < A3g) and the twin rule: a g arm is preferred over its twin only if it passes a bias check the twin
fails, or beats it by > 2 SE, and is not worse on any other check (no check FAIL where the twin passes; responsiveness
not failing where the twin passes). A g arm that is not preferred is not selectable (labelled reading).

SA-R3 (INV-32) extension: --round SA-R3 (results/shot_attempt_r3; arms A2g-c < A3g < A3g-c < A3g-s, noise floor =
|A3g - A3gs2|). Decision rule of SA-R3 applied literally (`main_r3`):
  - thin-state gate (fold 2): 4v4 and 3v3 attempts per 60 pred / actual - 1 within gates.yaml g2_rate_rel; cell SE
    by game-block bootstrap; UNDERPOWERED label where SE > tolerance, but the cell still gates (D17);
  - D13 guard (fold 1): each thin cell's |fold-1 bias| must be smaller than A3g's (strict reading, labelled);
  - every SA-R2 check (bias checks + responsiveness band) still passes;
  - select the simplest arm passing all of the above whose LL is not worse than A3g by > 2 SE; else none.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.shot_attempt.models import per_game_ll  # noqa: E402
from nhl_sim.shot_attempt.tables import SC_NAMES, ST_NAMES  # noqa: E402

ORDER = ["A0", "A1", "A2", "A5", "A4", "A3"]          # complexity, simplest first
NB, SEED = 1000, 20261015
MIN_N = int(yaml.safe_load(Path("docs/gates.yaml").read_text())["min_cell_n"])
TOL = dict(level=0.02, month=0.05, state=0.03, score=0.04, home=0.02)
MONTH_MIN_GAMES, SCORE_MIN_EXPO_H = 100, 300
GATING_STATES = (0, 1, 2)


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


def boot_se(x, idx):
    return float(x.mean()), float(x[idx].mean(1).std(ddof=1))


def bias_checks(rows, mu, months):
    """-> list of dicts (check, cell, pred, actual, ratio-1, n, status) and the overall pass flag."""
    out = []
    r = rows.assign(mu=mu)

    def add(check, cell, d, n, n_label, gating, tol, min_n=None):
        rel = d.mu / d.y - 1 if d.y > 0 else np.nan
        if min_n is not None and n < min_n:
            st = "UNDERPOWERED"
        elif not gating:
            st = "REPORTED"
        else:
            st = "PASS" if abs(rel) <= tol else "FAIL"
        out.append(dict(check=check, cell=cell, pred=float(d.mu), actual=float(d.y), rel_err=float(rel),
                        n=f"{n:.0f} {n_label}", tol=tol, status=st))
    add("level, overall", "all", r[["mu", "y"]].sum(), rows.game_id.nunique(), "games", True, TOL["level"])
    r["month"] = r.game_id.map(months)
    for m, d in r.groupby("month"):
        add("month", m, d[["mu", "y"]].sum(), d.game_id.nunique(), "games", True, TOL["month"], MONTH_MIN_GAMES)
    for s, d in r.groupby("st"):
        add("strength state", ST_NAMES[s], d[["mu", "y"]].sum(), d.exposure_s.sum() / 3600, "team-hours",
            s in GATING_STATES, TOL["state"])
    for s, d in r.groupby("sc"):
        add("score diff bucket", SC_NAMES[s], d[["mu", "y"]].sum(), d.exposure_s.sum() / 3600, "team-hours", True,
            TOL["score"], SCORE_MIN_EXPO_H)
    for h, d in r.groupby("is_home"):
        add("home/away", "home" if h else "away", d[["mu", "y"]].sum(), d.game_id.nunique(), "games", True,
            TOL["home"])
    ok = all(c["status"] != "FAIL" for c in out)
    return out, ok


def responsiveness(rows, mu, nb=NB, seed=SEED):
    """Offline 5v5 spread ratio by own ES-for and opponent ES-against rating quintile (team-games), with a
    game-block bootstrap 95% CI."""
    m = rows.st.to_numpy() == 0
    d = pd.DataFrame({"g": rows.game_id.to_numpy()[m], "t": rows.team.to_numpy()[m],
                      "own": rows.own_rf_es.to_numpy()[m], "opp": rows.opp_ra_es.to_numpy()[m], "mu": mu[m],
                      "y": rows.y.to_numpy()[m], "e": rows.exposure_s.to_numpy()[m]})
    tg = d.groupby(["g", "t"]).agg(own=("own", "first"), opp=("opp", "first"), mu=("mu", "sum"), y=("y", "sum"),
                                   e=("e", "sum")).reset_index()
    games = np.sort(tg.g.unique())
    gp = np.searchsorted(games, tg.g.to_numpy())
    G = len(games)
    cnt = np.random.default_rng(seed).multinomial(G, np.full(G, 1.0 / G), size=nb).astype(float)  # (nb, G)
    res = {}
    for c in ("own", "opp"):
        q = pd.qcut(tg[c].rank(method="first"), 5, labels=False).to_numpy()
        tab = []
        mats = {}
        for v in ("mu", "y", "e"):
            Mx = np.zeros((G, 5))
            np.add.at(Mx, (gp, q), tg[v].to_numpy())
            mats[v] = Mx
        p60 = mats["mu"].sum(0) / mats["e"].sum(0) * 3600
        a60 = mats["y"].sum(0) / mats["e"].sum(0) * 3600
        ratio = (p60[4] - p60[0]) / (a60[4] - a60[0])
        bm = cnt @ mats["mu"]
        by = cnt @ mats["y"]
        be = cnt @ mats["e"]
        bp, ba = bm / be * 3600, by / be * 3600
        br = (bp[:, 4] - bp[:, 0]) / (ba[:, 4] - ba[:, 0])
        lo, hi = np.percentile(br, [2.5, 97.5])
        for k in range(5):
            tab.append(dict(quintile=k + 1, rating_mean=float(tg[c][q == k].mean()), pred_per60=float(p60[k]),
                            actual_per60=float(a60[k]), n_team_games=int((q == k).sum())))
        res[c] = dict(ratio=float(ratio), ci=(float(lo), float(hi)), pass_=bool(0.8 <= ratio <= 1.2),
                      table=pd.DataFrame(tab).set_index("quintile"))
    return res


def per_team(rows, mu):
    tg = rows.assign(mu=mu).groupby(["team_id"]).agg(pred=("mu", "sum"), actual=("y", "sum"),
                                                     n_team_games=("game_id", "nunique"))
    tg["pred_per_game"] = tg.pred / tg.n_team_games
    tg["actual_per_game"] = tg.actual / tg.n_team_games
    tg["status"] = np.where(tg.n_team_games < MIN_N, "UNDERPOWERED", "")
    return tg


THIN = ((3, "4v4"), (4, "3v3"))
ORDER_R3 = ["A2g-c", "A3g", "A3g-c", "A3g-s"]


def thin_bias(rows, mu, idx, games_pos, G):
    """Per thin state: pred / actual - 1 with a game-block bootstrap SE (same resample index as the LL SEs)."""
    out = {}
    st = rows.st.to_numpy()
    for s_, nm in THIN:
        m = st == s_
        pm = np.bincount(games_pos[m], weights=mu[m], minlength=G)
        ym = np.bincount(games_pos[m], weights=rows.y.to_numpy(float)[m], minlength=G)
        rel = pm.sum() / ym.sum() - 1
        b = pm[idx].sum(1) / ym[idx].sum(1) - 1
        out[nm] = dict(rel=float(rel), se=float(b.std(ddof=1)), actual=float(ym.sum()),
                       team_hours=float(rows.exposure_s.to_numpy()[m].sum() / 3600))
    return out


def main_r3(a):
    tol = float(yaml.safe_load(Path("docs/gates.yaml").read_text())["g2_rate_rel"])
    res = Path(a.res)
    rows = pd.read_parquet(res / "fold2_rows.parquet")
    hs = sorted(f.stem.split("_")[2] for f in res.glob("fold2_haz_*.npy"))
    haz = {h: np.load(res / f"fold2_haz_{h}.npy") for h in hs}
    pg = {h: per_game_ll(rows, haz[h]) for h in hs}
    games = np.sort(rows.game_id.unique())
    gpos = np.searchsorted(games, rows.game_id.to_numpy())
    G = len(games)
    idx = np.random.default_rng(SEED).integers(0, G, size=(NB, G))
    y = rows.y.to_numpy(float)
    T = pd.DataFrame({"mean_LL_per_game": [pg[h].mean() for h in hs], "pred_attempts": [haz[h].sum() for h in hs]},
                     index=hs)
    T.index.name = "arm(hash)"
    TB = pd.DataFrame({nm: [f"{100 * thin_bias(rows, haz[h], idx, gpos, G)[nm]['rel']:+.2f}%" for h in hs]
                       for _, nm in THIN}, index=hs)
    D = pd.DataFrame(index=hs, columns=hs, dtype=object)
    for h1 in hs:
        for h2 in hs:
            m, se = boot_se(pg[h1] - pg[h2], idx)
            D.loc[h1, h2] = f"{m:+.4f} ({se:.4f})"
    L = [f"# SA-R3 fold-2 grade (train through 2023-24, test 2024-25; {G} games, {len(rows)} rows, {int(y.sum())} "
         "attempts)", "",
         "Generated by `scripts/grade_shot_attempt.py --round SA-R3`. Primary metric: per-game joint Poisson "
         f"log-likelihood of all row counts of both teams. SE = game-block bootstrap ({NB} resamples) of the paired "
         "per-game difference.", "", "## Blind table (labels hashed)", "", md(T, ".5f"), "",
         "Thin-state offline bias (pred / actual - 1), blind:", "", TB.to_markdown(), "",
         "Paired difference, row minus column, nats per game (SE):", "", D.to_markdown(), "",
         "TABLE FINAL -- labels revealed below; nothing after this point changes a number above.", ""]
    lab = json.loads((res / "labels_sealed.json").read_text())
    inv = {v: k for k, v in lab.items()}
    L += ["## Label reveal", "", md(pd.DataFrame({"hash": list(lab.values())}, index=list(lab))), ""]
    P = {inv[h]: pg[h] for h in hs}
    MU = {inv[h]: haz[h] for h in hs}
    floor = abs(P["A3g"].mean() - P["A3gs2"].mean())
    rows_s = []
    for k in ORDER_R3 + ["A3gs2"]:
        m, se = boot_se(P[k] - P["A3g"], idx)
        rows_s.append(dict(arm=k, LL_per_game=P[k].mean(), vs_A3g=m, SE=se, worse_than_A3g_by_gt_2SE=bool(m < -2 * se),
                           beats_A3g=bool(m > 2 * se and m > floor), pred_over_actual=MU[k].sum() / y.sum()))
    SL = pd.DataFrame(rows_s).set_index("arm")
    L += ["## Arms (revealed), LL vs A3g", "", md(SL, ".4f"), "",
          f"Noise floor |A3g - A3gs2| = {floor:.6f} nats/game.", ""]
    # thin-state gate (fold 2)
    thin = {k: thin_bias(rows, MU[k], idx, gpos, G) for k in ORDER_R3 + ["A3gs2"]}
    tr_ = []
    for k, d in thin.items():
        for nm, v in d.items():
            st_ = "PASS" if abs(v["rel"]) <= tol else "FAIL"
            tr_.append(dict(arm=k, state=nm, pred_over_actual_m1=v["rel"], cell_SE=v["se"], tol=tol,
                            actual_attempts=v["actual"], team_hours=v["team_hours"], status=st_,
                            power="UNDERPOWERED (SE > tol; still gates, D17)" if v["se"] > tol else "powered"))
    TT = pd.DataFrame(tr_).set_index(["arm", "state"])
    L += ["## Thin-state gate, fold 2 (gating; tolerance = gates.yaml g2_rate_rel)", "", md(TT, ".4f"), ""]
    # multi-level breakdown of the thin cells
    gm = load_games([20242025, 20232024], columns=["game_id", "game_date_local"])
    months = pd.Series(pd.to_datetime(gm.game_date_local).dt.strftime("%Y-%m").to_numpy(), index=gm.game_id)
    seg = []
    for k in ORDER_R3:
        r = rows.assign(mu=MU[k])
        for s_, nm in THIN:
            x = r[r.st == s_]
            for col, lab_ in (("game_type", {2: "RS", 3: "PO"}), ("ptype", {0: "regulation", 1: "OT"}),
                              ("is_home", {1: "home", 0: "away"})):
                for v, d in x.groupby(col):
                    seg.append(dict(arm=k, state=nm, segment=f"{col}={lab_.get(v, v)}", pred=d.mu.sum(),
                                    actual=d.y.sum(), rel=d.mu.sum() / max(d.y.sum(), 1e-9) - 1,
                                    team_hours=d.exposure_s.sum() / 3600))
            for v, d in x.assign(month=x.game_id.map(months)).groupby("month"):
                seg.append(dict(arm=k, state=nm, segment=f"month={v}", pred=d.mu.sum(), actual=d.y.sum(),
                                rel=d.mu.sum() / max(d.y.sum(), 1e-9) - 1, team_hours=d.exposure_s.sum() / 3600))
    SG = pd.DataFrame(seg)
    SG["label"] = np.where(SG.actual < 300, "UNDERPOWERED (< 300 attempts)", "")
    L += ["## Thin cells by segment, fold 2 (multi-level evidence; not gating)", "",
          md(SG.set_index(["arm", "state", "segment"]), ".4f"), ""]
    # fold-1 D13 guard
    f1 = res / "fold1"
    r1 = pd.read_parquet(f1 / "rows.parquet")
    g1 = np.sort(r1.game_id.unique())
    gp1 = np.searchsorted(g1, r1.game_id.to_numpy())
    idx1 = np.random.default_rng(SEED).integers(0, len(g1), size=(NB, len(g1)))
    f1b = {k: thin_bias(r1, np.load(f1 / f"pred_{k}.npy"), idx1, gp1, len(g1)) for k in ORDER_R3 + ["A3gs2"]}
    guard, gr = {}, []
    for k in ORDER_R3:
        ok = all(abs(f1b[k][nm]["rel"]) < abs(f1b["A3g"][nm]["rel"]) for _, nm in THIN) if k != "A3g" else None
        guard[k] = ok
        row = dict(arm=k)
        for _, nm in THIN:
            row[f"{nm} fold-1 bias"] = f"{100 * f1b[k][nm]['rel']:+.2f}% (SE {100 * f1b[k][nm]['se']:.2f})"
            row[f"{nm} |bias| < A3g"] = (abs(f1b[k][nm]["rel"]) < abs(f1b["A3g"][nm]["rel"])) if k != "A3g" \
                else "reference"
        row["D13_guard"] = "reference" if ok is None else ("PASS" if ok else "FAIL")
        gr.append(row)
    L += ["## D13 guard: fold-1 thin-state bias (2023-24 test, train 2021-23)", "",
          "Strict reading (labelled): BOTH thin cells' |fold-1 bias| must be smaller than A3g's.", "",
          md(pd.DataFrame(gr).set_index("arm")), ""]
    # SA-R2 checks
    summ, ok_all = [], {}
    L += ["## SA-R2 checks, fold 2 (bias checks + responsiveness band)", ""]
    for k in ORDER_R3:
        chk, ok = bias_checks(rows, MU[k], months)
        rp = responsiveness(rows, MU[k])
        rpok = rp["own"]["pass_"] and rp["opp"]["pass_"]
        fails = [f"{c['check']} {c['cell']} {100 * c['rel_err']:+.2f}%" for c in chk if c["status"] == "FAIL"]
        thin_ok = all(abs(thin[k][nm]["rel"]) <= tol for _, nm in THIN)
        ok_all[k] = dict(sa_r2_checks=bool(ok and rpok), thin_gate=thin_ok, d13=guard[k],
                         ll_ok=not bool(SL.loc[k, "worse_than_A3g_by_gt_2SE"]))
        summ.append(dict(arm=k, bias_pass=ok, fails="; ".join(fails) or "-", resp_own=rp["own"]["ratio"],
                         resp_opp=rp["opp"]["ratio"], resp_pass=rpok, thin_gate=thin_ok,
                         D13_guard=("reference" if guard[k] is None else guard[k]),
                         LL_not_worse_2SE=ok_all[k]["ll_ok"]))
        L += [f"### {k}", "", md(pd.DataFrame(chk).set_index(["check", "cell"]), ".4f"), ""]
    SUM = pd.DataFrame(summ).set_index("arm")
    passing = [k for k in ORDER_R3 if ok_all[k]["sa_r2_checks"] and ok_all[k]["thin_gate"] and ok_all[k]["ll_ok"]
               and (ok_all[k]["d13"] is not False)]
    sel = passing[0] if passing else None
    L += ["## Decision rule (applied literally)", "", md(SUM, ".3f"), "",
          "A3g is the reference: the D13 guard is not applicable to it (labelled).", "",
          f"Arms passing every condition: {passing or 'none'}.",
          f"**Selected arm: {sel or 'NONE (no arm passes; the PM rules, no SA-R4 pre-authorised)'}**", ""]
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    out = dict(selected=sel, passing=passing, noise_floor=floor, conditions=ok_all,
               ll_vs_A3g={k: dict(diff=float(SL.loc[k, "vs_A3g"]), se=float(SL.loc[k, "SE"])) for k in SL.index},
               thin_fold2=thin, thin_fold1=f1b)
    (res / "decision.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {a.out}")
    print(SL.to_string())
    print(TT.to_string())
    print(SUM.to_string())
    print("selected", sel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--res", default="results/shot_attempt_r1")
    ap.add_argument("--out", default="docs/tests/shot_attempt_sa_r1_grade_2026-10-15.md")
    ap.add_argument("--round", default="SA-R1")
    a = ap.parse_args()
    if a.round == "SA-R3":
        return main_r3(a)
    global ORDER
    if a.round == "SA-R2":
        ORDER = ["A0", "A1", "A2", "A2g", "A5", "A4", "A3", "A3g"]
    res = Path(a.res)
    rows = pd.read_parquet(res / "fold2_rows.parquet")
    hs = sorted(f.stem.split("_")[2] for f in res.glob("fold2_haz_*.npy"))
    haz = {h: np.load(res / f"fold2_haz_{h}.npy") for h in hs}
    lat = {h: json.loads((res / f"fold2_meta_{h}.json").read_text())["latent_v"] for h in hs}
    pg = {h: per_game_ll(rows, haz[h], lat[h]) for h in hs}
    G = len(next(iter(pg.values())))
    idx = np.random.default_rng(SEED).integers(0, G, size=(NB, G))
    y = rows.y.to_numpy(float)
    T = pd.DataFrame({"mean_LL_per_game": [pg[h].mean() for h in hs], "pred_attempts": [haz[h].sum() for h in hs],
                      "graded_by": ["shared-gamma marginal" if lat[h] > 0 else "independent Poisson" for h in hs]},
                     index=hs)
    T.index.name = "arm(hash)"
    D = pd.DataFrame(index=hs, columns=hs, dtype=object)
    for h1 in hs:
        for h2 in hs:
            m, se = boot_se(pg[h1] - pg[h2], idx)
            D.loc[h1, h2] = f"{m:+.4f} ({se:.4f})"
    L = [f"# {a.round} fold-2 grade (train through 2023-24, test 2024-25; {G} games, {len(rows)} rows, "
         f"{int(y.sum())} attempts)", "",
         "Generated by `scripts/grade_shot_attempt.py`. Primary metric: per-game joint log-likelihood of all row "
         "counts of both teams (independent Poisson; the shared-latent arm by its exact negative-multinomial "
         f"marginal). SE = game-block bootstrap ({NB} resamples) of the paired per-game difference.", "",
         "## Blind table (labels hashed)", "", md(T, ".5f"), "",
         "Paired difference, row minus column, nats per game (SE):", "", D.to_markdown(), "",
         "TABLE FINAL -- labels revealed below; nothing after this point changes a number above.", ""]
    lab = json.loads((res / "labels_sealed.json").read_text())
    inv = {v: k for k, v in lab.items()}
    L += ["## Label reveal", "", md(pd.DataFrame({"hash": list(lab.values())}, index=list(lab))), ""]
    P = {inv[h]: pg[h] for h in hs}
    MU = {inv[h]: haz[h] for h in hs}
    seed_floor = abs(P["A3"].mean() - P["A3s2"].mean())
    S = pd.DataFrame({"LL/game": {k: P[k].mean() for k in ORDER},
                      "vs A0": {k: boot_se(P[k] - P["A0"], idx)[0] for k in ORDER},
                      "SE vs A0": {k: boot_se(P[k] - P["A0"], idx)[1] for k in ORDER},
                      "pred/actual": {k: MU[k].sum() / y.sum() for k in ORDER}})
    L += ["## Arms (revealed)", "", md(S, ".4f"), "",
          f"A3 seed-retrain |difference| (seed floor) = {seed_floor:.6f} nats/game "
          f"(A3 {P['A3'].mean():.5f}, A3s2 {P['A3s2'].mean():.5f}).", ""]
    beats = {}
    L += ["## Pairwise (more complex vs simpler)", "",
          "| comparison | diff (nats/game) | SE | > 2 SE | > seed floor | beats |", "|---|---|---|---|---|---|"]
    comps = {}
    for i, x in enumerate(ORDER):
        for z in ORDER[:i]:
            m, se = boot_se(P[x] - P[z], idx)
            c1, c2 = m > 2 * se, m > seed_floor
            beats[(x, z)] = bool(c1 and c2)
            comps[f"{x}-{z}"] = dict(diff=m, se=se)
            L.append(f"| {x} vs {z} | {m:+.4f} | {se:.4f} | {c1} | {c2} | {beats[(x, z)]} |")
    # ---- bias checks
    gm = load_games([20242025, 20232024], columns=["game_id", "game_date_local"])
    months = pd.Series(pd.to_datetime(gm.game_date_local).dt.strftime("%Y-%m").to_numpy(), index=gm.game_id)
    elig, bias_ok, resp, chks = {}, {}, {}, {}
    L += ["", "## Bias checks, fold 2 (gating)", ""]
    summ = []
    for arm in ORDER:
        chk, ok = bias_checks(rows, MU[arm], months)
        chks[arm] = chk
        bias_ok[arm] = ok
        resp[arm] = responsiveness(rows, MU[arm])
        rp = resp[arm]["own"]["pass_"] and resp[arm]["opp"]["pass_"]
        elig[arm] = ok and rp
        fails = [f"{c['check']} {c['cell']} {100 * c['rel_err']:+.2f}%" for c in chk if c["status"] == "FAIL"]
        summ.append(dict(arm=arm, bias_pass=ok, n_fail=len(fails), fails="; ".join(fails) or "-",
                         resp_own=resp[arm]["own"]["ratio"], resp_own_ci=str(tuple(round(v, 3) for v in resp[arm]["own"]["ci"])),
                         resp_opp=resp[arm]["opp"]["ratio"], resp_opp_ci=str(tuple(round(v, 3) for v in resp[arm]["opp"]["ci"])),
                         resp_pass=rp, eligible=elig[arm]))
        L += [f"### {arm}", "", md(pd.DataFrame(chk).set_index(["check", "cell"]), ".4f"), ""]
    SUM = pd.DataFrame(summ).set_index("arm")
    L += ["## Eligibility summary (fold-2 bias checks + offline responsiveness band [0.8, 1.2])", "", md(SUM, ".3f"), ""]
    # ---- responsiveness tables
    L += ["## Responsiveness tables (fold 2, 5v5 rows, team-game quintiles; Q1 low .. Q5 high)", ""]
    for arm in ORDER:
        for c, nm in (("own", "own ES attempts-for rating"), ("opp", "opponent ES attempts-against rating")):
            rr = resp[arm][c]
            L += [f"### {arm}, by {nm}: spread ratio {rr['ratio']:.3f} (95% CI {rr['ci'][0]:.3f}..{rr['ci'][1]:.3f})",
                  "", md(rr["table"], ".3f"), ""]
    # ---- fold-1 diagnostic
    f1 = res / "fold1"
    if (f1 / "rows.parquet").exists():
        r1 = pd.read_parquet(f1 / "rows.parquet")
        L += ["## Bias checks, fold 1 (diagnostic only; train 2021-23, test 2023-24)", ""]
        s1 = []
        for arm in [x for x in ORDER]:
            p = f1 / f"pred_{arm}.npy"
            if not p.exists():
                continue
            chk, ok = bias_checks(r1, np.load(p), months)
            rr = responsiveness(r1, np.load(p))
            fails = [f"{c['check']} {c['cell']} {100 * c['rel_err']:+.2f}%" for c in chk if c["status"] == "FAIL"]
            s1.append(dict(arm=arm, bias_pass=ok, level=f"{100 * chk[0]['rel_err']:+.2f}%", fails="; ".join(fails) or "-",
                           resp_own=rr["own"]["ratio"], resp_opp=rr["opp"]["ratio"]))
        L += [md(pd.DataFrame(s1).set_index("arm"), ".3f"), ""]
    # ---- twin rule for the group-level arms (SA-R2)
    twin_note = []
    for g_arm, tw in (("A2g", "A2"), ("A3g", "A3")):
        if g_arm not in ORDER:
            continue
        sg = {(c["check"], c["cell"]): c["status"] for c in chks[g_arm]}
        st_ = {(c["check"], c["cell"]): c["status"] for c in chks[tw]}
        fixes = [k for k in sg if sg[k] == "PASS" and st_.get(k) == "FAIL"]
        worse = [k for k in sg if sg[k] == "FAIL" and st_.get(k) == "PASS"]
        for c in ("own", "opp"):
            if resp[tw][c]["pass_"] and not resp[g_arm][c]["pass_"]:
                worse.append(("responsiveness", c))
        m, se = boot_se(P[g_arm] - P[tw], idx)
        pref = bool((fixes or m > 2 * se) and not worse)
        twin_note.append(f"- {g_arm} vs {tw}: LL diff {m:+.4f} (SE {se:.4f}); checks fixed {fixes or 'none'}; "
                         f"checks worse {worse or 'none'}; **preferred: {pref}**")
        if not pref:
            elig[g_arm] = False
    if twin_note:
        L += ["## Group-level twin rule (SA-R2)", "", *twin_note, ""]
    # ---- decision
    E = [x for x in ORDER if elig[x]]
    sel = None
    for x in reversed(E):
        if all(beats[(x, z)] for z in E if ORDER.index(z) < ORDER.index(x)):
            sel = x
            break
    nxt = None
    if sel is not None:
        simpler = [z for z in E if ORDER.index(z) < ORDER.index(sel)]
        nxt = simpler[-1] if simpler else None
    L += ["## Decision rule (applied literally)", "",
          f"Eligible arms: {E or 'none'}.",
          f"**Selected arm: {sel or 'NONE (no arm is eligible)'}**; next simpler eligible arm: {nxt or 'none'}.", ""]
    # ---- multi-level evidence for the best two arms by LL
    ranked = sorted(ORDER, key=lambda k: -P[k].mean())
    for arm in ranked[:2]:
        t = per_team(rows, MU[arm])
        corr = np.corrcoef(t.pred_per_game, t.actual_per_game)[0, 1]
        tgm = rows.assign(mu=MU[arm]).groupby(["game_id", "team"]).agg(pred=("mu", "sum"), actual=("y", "sum"))
        tgm["dec"] = pd.qcut(tgm.pred.rank(method="first"), 10, labels=False) + 1
        dec = tgm.groupby("dec").agg(pred=("pred", "mean"), actual=("actual", "mean"), n=("pred", "size"))
        L += [f"## Multi-level evidence: {arm} (rank {ranked.index(arm) + 1} by LL)", "",
              "Calibration, attempts per team-game by decile of predicted:", "", md(dec, ".2f"), "",
              f"Per team (n = team-games, all below min_cell_n={MIN_N}: UNDERPOWERED; corr pred/actual {corr:.2f}):",
              "", md(t[["pred_per_game", "actual_per_game", "n_team_games", "status"]], ".2f"), ""]
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    out = dict(selected=sel, next_simpler_eligible=nxt, eligible=E, seed_floor=seed_floor, comparisons=comps,
               ll_per_game={k: float(P[k].mean()) for k in P}, bias_pass=bias_ok,
               responsiveness={k: {c: dict(ratio=resp[k][c]["ratio"], ci=resp[k][c]["ci"]) for c in ("own", "opp")}
                               for k in ORDER})
    (res / "decision.json").write_text(json.dumps(out, indent=1))
    print(f"wrote {a.out}")
    print(SUM.to_string())
    print(S.to_string())
    print("selected", sel, "next", nxt, "seed floor", seed_floor)


if __name__ == "__main__":
    main()
