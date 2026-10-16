"""Blind grader for SS-R1 fold 2 (INV-22). Scores every hazard arm (and type arm) from hash-labelled prediction
files; labels stay hashed until the table is final, then are revealed and the pre-registered decision rule is
applied literally (docs/models/strength_state/experiments.md SS-R1).

    grade_strength_state.py [--out docs/tests/strength_state_ss_r1_grade_2026-10-15.md]
    grade_strength_state.py --res results/strength_state_r2 --round SS-R2 --out docs/tests/strength_state_ss_r2_grade_2026-10-15.md
SS-R2 (INV-26) extension, backward-compatible: --res picks the results directory, --round labels the report (SS-R2
arms are shown primed, H0'..H3'), and the type section is skipped when the round has no type predictions (T1 is not
re-raced in SS-R2).
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.strength_state.models import STRENGTH_NAMES, TYPE_CLASSES, pois_ll  # noqa: E402

RES = Path("results/strength_state_r1")
ORDER = ["H0", "H1", "H2", "H3"]
NB, SEED = 1000, 20261015
MIN_N = int(yaml.safe_load(Path("docs/gates.yaml").read_text())["min_cell_n"])


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


def boot(per_game: np.ndarray, idx: np.ndarray):
    m = per_game[idx].mean(1)
    return float(per_game.mean()), float(m.std(ddof=1))


def seg_table(rows, mu, by, label_fn=None):
    d = rows.assign(mu=mu).groupby(by).agg(pred=("mu", "sum"), actual=("y", "sum"), expo_h=("exposure_s", "sum"))
    d["expo_h"] /= 3600
    d["pred_per60"] = d.pred / d.expo_h
    d["actual_per60"] = d.actual / d.expo_h
    d["n_events"] = d.actual.astype(int)
    d["status"] = np.where(d.n_events < MIN_N, "UNDERPOWERED", "")
    if label_fn is not None:
        d.index = [label_fn(i) for i in d.index]
    return d[["pred", "actual", "pred_per60", "actual_per60", "n_events", "status"]]


def secondary(rows, mu, arm):
    L = [f"### Secondary metrics: {arm}", ""]
    tg = rows.assign(mu=mu).groupby(["game_id", "team"]).agg(pred=("mu", "sum"), actual=("y", "sum"),
                                                              taken=("taken_own", "first"),
                                                              drawn_opp=("drawn_opp", "first"),
                                                              team_id=("team_id", "first"),
                                                              expo=("exposure_s", "sum")).reset_index()
    tg["dec"] = pd.qcut(tg.pred.rank(method="first"), 10, labels=False) + 1
    c = tg.groupby("dec").agg(pred=("pred", "mean"), actual=("actual", "mean"), n=("pred", "size"))
    L += ["Calibration, penalties per team-game by decile of predicted:", "", md(c, ".3f"), ""]
    for col, nm in (("taken", "team taken-rating"), ("drawn_opp", "opponent drawn-rating")):
        tg["q"] = pd.qcut(tg[col].rank(method="first"), 5, labels=False) + 1
        q = tg.groupby("q").agg(pred=("pred", "sum"), actual=("actual", "sum"), expo=("expo", "sum"),
                                rating_mean=(col, "mean"), n_team_games=("pred", "size"))
        q["pred_per60"] = q.pred / q.expo * 3600
        q["actual_per60"] = q.actual / q.expo * 3600
        sl = np.polyfit(q.pred_per60, q.actual_per60, 1)[0]
        L += [f"Responsiveness by {nm} quintile (slope of actual on predicted per-60 across quintiles: {sl:.2f}):",
              "", md(q[["rating_mean", "pred_per60", "actual_per60", "n_team_games"]], ".3f"), ""]
    L += ["By strength state (team view):", "",
          md(seg_table(rows, mu, "st", lambda i: STRENGTH_NAMES[i]), ".3f"), ""]
    sc = ["<=-2", "-1", "0", "+1", ">=+2"]
    L += ["By pre-event score diff bucket (team view):", "", md(seg_table(rows, mu, "sc", lambda i: sc[i]), ".3f"), ""]
    L += ["By pre-event penalty differential bucket (own minus opponent):", "",
          md(seg_table(rows, mu, "pdiff", lambda i: sc[i]), ".3f"), ""]
    L += ["By period (4 = OT):", "", md(seg_table(rows, mu, "period"), ".3f"), ""]
    L += ["Home vs away:", "", md(seg_table(rows, mu, "is_home", lambda i: "home" if i else "away"), ".3f"), ""]
    t = tg.groupby("team_id").agg(pred=("pred", "sum"), actual=("actual", "sum"), n_team_games=("pred", "size"))
    t["pred_per_game"] = t.pred / t.n_team_games
    t["actual_per_game"] = t.actual / t.n_team_games
    t["status"] = np.where(t.n_team_games < MIN_N, "UNDERPOWERED", "")
    corr = np.corrcoef(t.pred_per_game, t.actual_per_game)[0, 1]
    L += [f"Per team (32 rows; n = team-games, all below min_cell_n={MIN_N} -> UNDERPOWERED; correlation of "
          f"predicted and actual per-game rates across teams {corr:.2f}):", "",
          md(t[["pred_per_game", "actual_per_game", "n_team_games", "status"]], ".3f"), ""]
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/tests/strength_state_ss_r1_grade_2026-10-15.md")
    ap.add_argument("--res", default=str(RES))
    ap.add_argument("--round", default="SS-R1")
    a = ap.parse_args()
    res_dir = Path(a.res)
    pr = "''" if a.round == "SS-R3" else ("'" if a.round != "SS-R1" else "")
    rows = pd.read_parquet(res_dir / "fold2_rows.parquet")
    haz = {f.stem.split("_")[2]: np.load(f) for f in sorted(res_dir.glob("fold2_haz_*.npy"))}
    typ = {f.stem.split("_")[2]: np.load(f) for f in sorted(res_dir.glob("fold2_type_*.npy"))}
    types = pd.read_parquet(res_dir / "fold2_types.parquet") if typ else pd.DataFrame({"game_id": [], "k": []})
    games = np.sort(rows.game_id.unique())
    gpos = np.searchsorted(games, rows.game_id.to_numpy())
    G = len(games)
    idx = np.random.default_rng(SEED).integers(0, G, size=(NB, G))
    y = rows.y.to_numpy(float)
    pg = {h: np.bincount(gpos, weights=pois_ll(y, mu), minlength=G) for h, mu in haz.items()}
    hs = sorted(pg)
    T = pd.DataFrame({"mean_LL_per_game": [pg[h].mean() for h in hs],
                      "pred_events": [haz[h].sum() for h in hs]}, index=hs)
    T.index.name = "arm(hash)"
    D = pd.DataFrame(index=hs, columns=hs, dtype=object)
    for h1 in hs:
        for h2 in hs:
            m, se = boot(pg[h1] - pg[h2], idx)
            D.loc[h1, h2] = f"{m:+.4f} ({se:.4f})"
    # type arms: multinomial LL per penalty, summed per game
    tpos = np.searchsorted(games, types.game_id.to_numpy())
    k = types.k.to_numpy()
    tpg = {h: np.bincount(tpos, weights=np.log(p[np.arange(len(k)), k]), minlength=G) for h, p in typ.items()}
    ths = sorted(tpg)
    TT = pd.DataFrame({"mean_LL_per_penalty": [np.log(typ[h][np.arange(len(k)), k]).mean() for h in ths],
                       "mean_LL_per_game": [tpg[h].mean() for h in ths]}, index=ths)
    TT.index.name = "arm(hash)"
    td = {}
    for h1 in ths:
        for h2 in ths:
            if h1 < h2:
                td[(h1, h2)] = boot(tpg[h1] - tpg[h2], idx)
    L = [f"# {a.round} fold-2 grade (train through 2023-24, test 2024-25; {G} games, {len(rows)} hazard rows, "
         f"{int(y.sum())} penalty-taking events, {len(types)} typed events)", "",
         "Generated by `scripts/grade_strength_state.py`. Primary metric: held-out Poisson log-likelihood per game "
         "of penalty-taking counts over all hazard rows (higher is better). SE = game-block bootstrap "
         f"({NB} resamples of fold-2 games) of the paired per-game difference.", "",
         "## Blind table, hazard arms (labels hashed)", "", md(T, ".5f"), "",
         "Paired difference row minus column, mean per game (bootstrap SE):", "", D.to_markdown(), "",
         ]
    if typ:
        L += ["## Blind table, type arms (labels hashed)", "", md(TT, ".5f"), ""]
    for (h1, h2), (m, se) in td.items():
        L.append(f"- {h1} minus {h2}: {m:+.5f} per game (SE {se:.5f})")
    L += ["", "TABLE FINAL -- labels revealed below; nothing after this point changes a number above.", ""]
    lab = json.loads((res_dir / "labels_sealed.json").read_text())
    inv = {v: k_ for k_, v in lab.items()}
    L += ["## Label reveal", "", md(pd.DataFrame({"hash": list(lab.values())}, index=[k_ + pr for k_ in lab])), ""]
    P = {inv[h]: pg[h] for h in hs}
    seed_floor = abs(P["H3"].mean() - P["H3s2"].mean())
    res = {}
    L += ["## Decision rule (hazard)", "",
          f"H3 seed-retrain |difference| (seed floor) = {seed_floor:.6f} nats/game.", "",
          "| comparison | diff (nats/game) | SE | > 2 SE | > seed floor | beats |", "|---|---|---|---|---|---|"]
    beats = {}
    for i, a_ in enumerate(ORDER):
        for b_ in ORDER[:i]:
            m, se = boot(P[a_] - P[b_], idx)
            c1 = m > 2 * se
            c2 = (m > seed_floor) if "H3" in (a_, b_) else True
            beats[(a_, b_)] = bool(c1 and c2)
            res[f"{a_}-{b_}"] = dict(diff=m, se=se)
            L.append(f"| {a_}{pr} vs {b_}{pr} | {m:+.4f} | {se:.4f} | {c1} | {c2 if 'H3' in (a_, b_) else 'n/a'} | "
                     f"{beats[(a_, b_)]} |")
    elig = [a_ for i, a_ in enumerate(ORDER) if all(beats[(a_, b_)] for b_ in ORDER[:i])]
    winner = max(elig, key=lambda a_: P[a_].mean())
    ranked = sorted(ORDER, key=lambda a_: -P[a_].mean())
    runner = [a_ for a_ in ranked if a_ != winner][0]
    L += ["", f"Arms that beat every simpler arm: {elig}. **Offline winner: {winner}** (provisional until G1). "
          f"Runner-up by primary metric: {runner}.", "",
          "Primary metric vs H0 (nats/game): " + ", ".join(f"{a_} {P[a_].mean() - P['H0'].mean():+.4f}"
                                                         for a_ in ORDER), ""]
    t_win = "T1 (carried over, not re-raced)"
    if typ:
        t_win = _type_section(L, inv, tpg, ths, typ, types, k, idx)
    hz = {inv[h]: haz[h] for h in hs}
    L += ["## Secondary metrics (winner and runner-up)", ""]
    L += secondary(rows, hz[winner], winner + pr)
    L += secondary(rows, hz[runner], runner + pr)
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    (res_dir / "winner.json").write_text(json.dumps({"hazard_winner": winner, "runner_up": runner, "type_winner": t_win,
                                                     "seed_floor": seed_floor, "comparisons": res,
                                                     "ll_per_game": {a_: float(P[a_].mean()) for a_ in P}}, indent=1))
    print(f"wrote {a.out}; hazard winner {winner}{pr}, runner-up {runner}{pr}, type winner {t_win}")


def _type_section(L, inv, tpg, ths, typ, types, k, idx):
    TP = {inv[h]: tpg[h] for h in ths}
    m, se = boot(TP["T1"] - TP["T0"], idx)
    t_win = "T1" if m > 2 * se else "T0"
    L += ["## Decision rule (type)", "", f"T1 minus T0: {m:+.5f} nats/game (SE {se:.5f}); T1 beats T0: {m > 2 * se}. "
          f"**Type winner: {t_win}.**", ""]
    pt = {inv[h]: typ[h] for h in ths}
    cal = pd.DataFrame({"actual_share": np.bincount(k, minlength=4) / len(k),
                        "T0_pred": pt["T0"].mean(0), "T1_pred": pt["T1"].mean(0)}, index=TYPE_CLASSES)
    L += ["Type calibration (share of penalty-taking events):", "", md(cal, ".4f"), ""]
    by = []
    for s_ in range(6):
        mm = types.st.to_numpy() == s_
        if mm.sum() == 0:
            continue
        by.append(pd.Series({"n": int(mm.sum()), **{f"actual_{c}": (k[mm] == i).mean() for i, c in enumerate(TYPE_CLASSES)},
                             **{f"T1_{c}": pt["T1"][mm, i].mean() for i, c in enumerate(TYPE_CLASSES)}},
                            name=STRENGTH_NAMES[s_]))
    L += ["Type mix by strength state (team view):", "", md(pd.DataFrame(by), ".3f"), ""]
    return t_win


if __name__ == "__main__":
    main()
