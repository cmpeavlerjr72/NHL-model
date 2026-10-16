"""SS-R3 pre-registered bias checks (experiments.md SS-R2 checks, reused by SS-R3), plus the twin-preference rule:
  fold 2 (2024-25, GATES): H0''-H3'' and the SS-R2 twins H0'-H3' (reported, fail per SS-R2);
  fold 1 (2023-24, diagnostic): H0''-H3'' and the SS-R2 twins refit on fold 1.
Checks per arm: season level |pred/actual - 1| <= 3% overall; <= 8% in every month with n >= 100 games (smaller
months UNDERPOWERED); state 'other' net shortfall <= 1.5% (rows re-labelled 5v5, an approximation, as SS-R2).
Twin preference (fold 2): an SS-R3 arm is preferred over its SS-R2 twin only if it passes the checks the twin
failed and its fold-2 LL/game is not worse than the twin's by more than 2 bootstrap SE (game-block, 1,000 resamples).
Profile arms and twins in fold 2 use identical rows and exposure, so the paired LL difference is exact.
"""
import argparse
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.strength_state import models_r2 as R  # noqa: E402
from nhl_sim.strength_state.models import pois_ll  # noqa: E402

R3 = Path("results/strength_state_r3")
R2 = Path("results/strength_state_r2")
ARMS = ["H0", "H1", "H2", "H3"]
TOL_ALL, TOL_MONTH, MIN_GAMES, TOL_OTHER = 0.03, 0.08, 100, 0.015


def load_model(prefix_dir, arm, suffix):
    if arm.startswith("H3"):
        return lgb.Booster(model_file=str(prefix_dir / "models" / f"{arm}_{suffix}.txt"))
    return json.loads((prefix_dir / "models" / f"{arm}_{suffix}.json").read_text())


def predict(arm, m, r):
    return R.predict_lgb(m, r) if arm.startswith("H3") else R.predict_glm(m, r)


def check(rows, mus, models, season, title):
    """mus: arm label -> predictions on rows; models: arm label -> model (for the 'other' re-label)."""
    rows = rows.copy()
    rows["clock"] = (rows.t0 // 60).astype(np.int32)
    rows["cell"] = rows.st.astype(np.int64) * 10 + rows.ptype
    g = load_games([season], columns=["game_id", "game_date_local"])
    month = pd.to_datetime(rows.game_id.map(g.set_index("game_id").game_date_local)).dt.to_period("M").astype(str)
    gmonth = pd.Series(month.to_numpy(), index=rows.game_id.to_numpy()).groupby(level=0).first()
    n_games_m = gmonth.value_counts().sort_index()
    y = rows.y.to_numpy(float)
    total = y.sum()
    other = rows.st.to_numpy() == 5
    alt = rows[other].assign(st=0, cell=lambda d: d.ptype.astype(np.int64))
    L = [f"## {title}", "",
         f"Events {int(total)}; in state 'other' {int(y[other].sum())} ({y[other].sum() / total:.2%}).", ""]
    summ, bymonth = [], {}
    for arm, mu in mus.items():
        base = arm.rstrip("'")
        ratio = mu.sum() / total
        bym = pd.DataFrame({"pred": pd.Series(mu).groupby(month.to_numpy()).sum(),
                            "actual": pd.Series(y).groupby(month.to_numpy()).sum()})
        bym["n_games"] = n_games_m.reindex(bym.index).to_numpy()
        bym["ratio"] = bym.pred / bym.actual
        bym["status"] = np.where(bym.n_games < MIN_GAMES, "UNDERPOWERED",
                                 np.where((bym.ratio - 1).abs() <= TOL_MONTH, "PASS", "FAIL"))
        bymonth[arm] = bym
        m_ok = (bym.status != "FAIL").all()
        net = (y[other].sum() - predict(base, models[arm], alt).sum()) / total
        s_all = "PASS" if abs(ratio - 1) <= TOL_ALL else "FAIL"
        s_oth = "PASS" if net <= TOL_OTHER else "FAIL"
        big = bym[bym.n_games >= MIN_GAMES]
        worst = big.ratio.sub(1).abs().idxmax()
        summ.append(dict(arm=arm, ratio=ratio, overall=s_all, months_fail=int((bym.status == "FAIL").sum()),
                         worst_month=f"{worst} {big.ratio[worst] - 1:+.1%}", other_net=net, other=s_oth,
                         all_pass=bool(s_all == "PASS" and m_ok and s_oth == "PASS")))
    S = pd.DataFrame(summ).set_index("arm")
    L += [S.to_markdown(floatfmt=".4f"), ""]
    mt = pd.DataFrame({a: b.ratio for a, b in bymonth.items()})
    mt.insert(0, "n_games", next(iter(bymonth.values())).n_games)
    L += ["Predicted / actual by month (UNDERPOWERED where n_games < 100):", "", mt.to_markdown(floatfmt=".3f"), ""]
    return S, mt, L


def fold2():
    rows = pd.read_parquet(R3 / "fold2_rows.parquet")
    lab3 = json.loads((R3 / "labels_sealed.json").read_text())
    lab2 = json.loads((R2 / "labels_sealed.json").read_text())
    r2rows = pd.read_parquet(R2 / "fold2_rows.parquet")
    mus3 = {a + "''": np.load(R3 / f"fold2_haz_{lab3[a]}.npy") for a in ARMS}
    mus2 = {a + "'": np.load(R2 / f"fold2_haz_{lab2[a]}.npy") for a in ARMS}
    m3 = {a + "''": load_model(R3, a, "fold2") for a in ARMS}
    m2 = {a + "'": load_model(R2, a, "fold2") for a in ARMS}
    assert (rows.game_id.to_numpy() == r2rows.game_id.to_numpy()).all()
    assert (rows.t0.to_numpy() == r2rows.t0.to_numpy()).all()
    S3, mt3, L3 = check(rows, mus3, m3, 20242025, "Fold 2 (2024-25), SS-R3 arms (GATES)")
    S2, mt2, L2 = check(r2rows, mus2, m2, 20242025, "Fold 2 (2024-25), SS-R2 twins (no profile; reported)")
    games = np.sort(rows.game_id.unique())
    gpos = np.searchsorted(games, rows.game_id.to_numpy())
    idx = np.random.default_rng(20261015).integers(0, len(games), size=(1000, len(games)))
    y = rows.y.to_numpy(float)
    tw = []
    for a in ARMS:
        d = (np.bincount(gpos, weights=pois_ll(y, mus3[a + "''"]), minlength=len(games))
             - np.bincount(gpos, weights=pois_ll(y, mus2[a + "'"]), minlength=len(games)))
        se = float(d[idx].mean(1).std(ddof=1))
        diff = float(d.mean())
        passes = bool(S3.loc[a + "''", "all_pass"])
        tw.append(dict(arm=a + "''", twin=a + "'", ll_diff=diff, se=se, not_worse_2se=bool(diff >= -2 * se),
                       twin_failed_checks=not bool(S2.loc[a + "'", "all_pass"]), passes_checks=passes,
                       preferred_over_twin=bool(passes and diff >= -2 * se)))
    T = pd.DataFrame(tw).set_index("arm")
    return S3, mt3, L3, S2, L2, T


def fold1():
    d = R3 / "fold1"
    out = {}
    for tag, pre in (("SS-R3 arms", "r3"), ("SS-R2 twins (refit on fold 1)", "r2")):
        rows = pd.read_parquet(d / f"rows_{pre}.parquet")
        pr = "''" if pre == "r3" else "'"
        mus = {a + pr: np.load(d / f"pred_{pre}_{a}.npy") for a in ARMS}
        ms = {a + pr: load_model(d / pre, a, "fold") for a in ARMS}
        out[pre] = check(rows, mus, ms, 20232024, f"Fold 1 (2023-24, diagnostic), {tag}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/tests/strength_state_ss_r3_bias_2026-10-15.md")
    a = ap.parse_args()
    S3, mt3, L3, S2, L2, T = fold2()
    f1 = fold1()
    L = ["# SS-R3 pre-registered bias checks", "",
         "Generated by `scripts/diag_strength_state_bias_r3.py`. Fold-2 checks gate; fold-1 checks are diagnostic "
         "(D13 forking-paths guard).", ""]
    L += L3 + L2 + ["## Twin-preference rule (fold 2)", "", T.to_markdown(floatfmt=".4f"), ""]
    for pre in ("r3", "r2"):
        L += f1[pre][2]
    Path(a.out).write_text("\n".join(L) + "\n", encoding="utf-8")
    S3.to_csv(R3 / "bias_checks_fold2.csv")
    T.to_csv(R3 / "twin_preference.csv")
    for pre in ("r3", "r2"):
        f1[pre][0].to_csv(R3 / f"bias_checks_fold1_{pre}.csv")
    pd.set_option("display.width", 250)
    print(S3.to_string())
    print(S2.to_string())
    print(T.to_string())
    for pre in ("r3", "r2"):
        print(f1[pre][0].to_string())
        print(f1[pre][1].to_string())
    print(mt3.to_string())


if __name__ == "__main__":
    main()
