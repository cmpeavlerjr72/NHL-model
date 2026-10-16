"""LC-2 step 2 (INV-29 re-measure): PP-opportunities-conferred spread ratios (Q5-Q1, sim / actual) by own taken-rating and
opponent drawn-rating quintile, regular season only and all games, with team-bootstrap 95% CIs (1,000 resamples of
the 32 teams; the grouping team is the rated team: own team for taken, opponent for drawn; quintiles are recomputed
inside every resample). Same tg construction as diag_strength_state_g1_decomp_v5.py.
    diag_strength_state_lc2_spread.py --arm H3"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from nhl_sim.eval import g1 as G1  # noqa: E402
from diag_strength_state_g1_decomp_v3 import quint  # noqa: E402

RES = Path("results/strength_state_lc2")
TEST = 20242025


def build(arm, tag):
    rows = pd.read_parquet(RES / "fold2_rows.parquet")
    real = G1.real_frame(TEST)
    s = pd.read_parquet(Path("results") / tag / "strength_toi.parquet")
    tg = rows.groupby(["game_id", "team"]).agg(taken_own=("taken_own", "first"), drawn_opp=("drawn_opp", "first"),
                                               game_type=("game_type", "first"), team_id=("team_id", "first"),
                                               opp_id=("opp_id", "first")).reset_index()
    sm = s.groupby("game_id")[["ppo_home", "ppo_away"]].mean().add_suffix("_sim")
    rl = real.set_index("game_id")[["ppo_home", "ppo_away"]]
    tg = tg.join(sm, on="game_id").join(rl, on="game_id")
    h = tg.team == 0
    tg["opp_ppo_sim"] = np.where(h, tg.ppo_away_sim, tg.ppo_home_sim)
    tg["opp_ppo_act"] = np.where(h, tg.ppo_away, tg.ppo_home)
    return tg


def ratio(d, col):
    q = quint(d[col])
    g = d.assign(q=q).groupby("q")[["opp_ppo_act", "opp_ppo_sim"]].mean()
    a, s = g.opp_ppo_act.iloc[-1] - g.opp_ppo_act.iloc[0], g.opp_ppo_sim.iloc[-1] - g.opp_ppo_sim.iloc[0]
    return float(a), float(s), float(s / a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="H3")
    A = ap.parse_args()
    tg = build(A.arm, f"ss_lc2_g1_{A.arm}_T2")
    rng = np.random.default_rng(20261016)
    out, L = {}, [f"## INV-29 spread ratios, {A.arm}''-LC2 + T2 (fold 2, 200 seeds); band [0.8, 1.2]", "",
                  "| rating | games | actual Q5-Q1 | sim Q5-Q1 | ratio | 95% CI (team bootstrap) | sim - actual spread, 95% CI | in band |", "|---|---|---:|---:|---:|---|---|---|"]
    for seg, sel in (("regular season", tg.game_type == 2), ("all games", np.ones(len(tg), bool))):
        d = tg[sel].reset_index(drop=True)
        for col, grp, nm in (("taken_own", "team_id", "own taken-rating"), ("drawn_opp", "opp_id", "opponent drawn-rating")):
            a, s, r = ratio(d, col)
            teams = np.sort(d[grp].unique())
            idx = {t: np.flatnonzero(d[grp].to_numpy() == t) for t in teams}
            bs, df = [], []
            for _ in range(1000):
                pick = rng.choice(teams, len(teams))
                aa, ss, rr = ratio(d.iloc[np.concatenate([idx[t] for t in pick])].reset_index(drop=True), col)
                bs.append(rr)
                df.append(ss - aa)
            lo, hi = np.percentile(bs, [2.5, 97.5])
            dlo, dhi = np.percentile(df, [2.5, 97.5])
            out[f"{seg}|{nm}"] = dict(actual=a, sim=s, ratio=r, lo=float(lo), hi=float(hi), diff_lo=float(dlo), diff_hi=float(dhi), n=int(len(d)))
            L.append(f"| {seg}, {nm} | {len(d)} | {a:.3f} | {s:.3f} | {r:.2f} | {lo:.2f} to {hi:.2f} (unstable: the actual spread is near 0 in many resamples) | {s - a:+.3f} ({dlo:+.3f}, {dhi:+.3f}) | "
                     f"{'yes' if 0.8 <= r <= 1.2 else 'NO'} (CI {'inside' if lo >= 0.8 and hi <= 1.2 else 'overlaps edge/outside'}) |")
    (RES / f"spread_{A.arm}.json").write_text(json.dumps(out, indent=1))
    Path(RES / f"spread_{A.arm}.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
