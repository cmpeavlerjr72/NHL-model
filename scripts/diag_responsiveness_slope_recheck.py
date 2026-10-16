"""Lane R (D32): re-check the stage-1 and stage-3 incumbents under the slope-based responsiveness gate R = 1/b.
Reads existing sim outputs only (no new sim run). Writes results/responsiveness_slope_recheck.json and prints markdown.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from nhl_sim.eval import g1 as G1  # noqa: E402
from nhl_sim.eval import g2 as G2  # noqa: E402
from nhl_sim.eval.responsiveness import slope_ratio  # noqa: E402

TEST = 20242025
LC2D = Path("results/strength_state_lc2")
OUT = {}
LINES = []


def fmt(r):
    return (f"R={r['R']:.3f} (CI {r['ci'][0]:.3f}..{r['ci'][1]:.3f}) b={r['b']:.3f} old Q5-Q1={r['old_q5q1']:.3f} "
            f"{r['status']}{' UNDERPOWERED' if r['underpowered'] else ''}")


def stage1():
    rows = pd.read_parquet(LC2D / "fold2_rows.parquet")
    real = G1.real_frame(TEST)
    s = pd.read_parquet(Path("results/ss_lc2_g1_H3_T2/strength_toi.parquet"))
    tg = rows.groupby(["game_id", "team"]).agg(taken_own=("taken_own", "first"), drawn_opp=("drawn_opp", "first"),
                                               game_type=("game_type", "first")).reset_index()
    sm = s.groupby("game_id")[["ppo_home", "ppo_away"]].mean().add_suffix("_sim")
    rl = real.set_index("game_id")[["ppo_home", "ppo_away"]]
    tg = tg.join(sm, on="game_id").join(rl, on="game_id")
    h = tg.team == 0
    tg["pred"] = np.where(h, tg.ppo_away_sim, tg.ppo_home_sim)       # opponent PP opps conferred, sim
    tg["act"] = np.where(h, tg.ppo_away, tg.ppo_home)
    LINES.append("## Stage 1 H3''-LC2 + T2: PP opportunities conferred (200 seeds, sim = mean over seeds per team-game)")
    LINES.append("")
    for seg, m in (("regular season", tg.game_type == 2), ("all games", tg.game_type > 0)):
        d = tg[m]
        for col, nm in (("taken_own", "own taken-rating"), ("drawn_opp", "opponent drawn-rating")):
            r = slope_ratio(d.pred, d.act, d[col], np.ones(len(d)), d.game_id, seed=0)
            OUT[f"stage1|{seg}|{nm}"] = {k: v for k, v in r.items() if k != "table"}
            LINES.extend([f"### {seg}, by {nm} (n team-games {len(d)}, games {r['n_games']}): {fmt(r)}", "",
                      r["table"].round(3).to_markdown(floatfmt=".3f"), ""])


def stage3():
    import run_shot_attempt_g2 as S3
    from nhl_sim.shot_attempt import models as S
    tag = "sa_r3_g2_A3gc_lc2t2"
    S3.RES = Path("results/shot_attempt_r3")
    out = Path("results") / tag
    s = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    from nhl_sim.data.load import load_games
    gt = load_games([TEST], columns=["game_id", "game_type"])
    s = s.merge(gt, on="game_id")
    rows = pd.read_parquet(S3.RES / "fold2_rows.parquet")
    R = G2.real_team_arrays(S.load_rows([TEST]))
    Sm = G2.sim_team_arrays(s)
    tg = rows.groupby(["game_id", "team"]).agg(own=("own_rf_es", "first"), opp=("opp_ra_es", "first")).reset_index()
    def per_tg(d):
        a5 = G2.marginals(d)[0][:, 0]
        t5 = d["T"][:, 0].sum(1)
        f = pd.DataFrame({"game_id": d["game_id"], "team": d["team"], "a": a5, "t": t5, "gtp": d["game_type"]})
        return f.groupby(["game_id", "team"]).mean()
    j = tg.join(per_tg(Sm).add_suffix("_sim"), on=["game_id", "team"]).join(per_tg(R).add_suffix("_act"),
                                                                            on=["game_id", "team"])
    j = j[(j.t_sim > 0) & (j.t_act > 0)].copy()
    j["rate_sim"] = j.a_sim / j.t_sim * 3600
    j["rate_act"] = j.a_act / j.t_act * 3600
    LINES.append("## Stage 3 A3g-c on H3''-LC2 + T2: closed-loop 5v5 attempts per 60 (200 seeds, overall RS+PO)")
    LINES.append("")
    for seg, m in (("overall (RS+PO)", j.gtp_act > 0), ("regular season", j.gtp_act == 2)):
        d = j[m]
        for col, nm in (("own", "own ES attempts-for rating"), ("opp", "opponent ES attempts-against rating")):
            r = slope_ratio(d.rate_sim, d.rate_act, d[col], d.t_act, d.game_id, seed=0, pred_weights=d.t_sim)
            OUT[f"stage3|{seg}|{nm}"] = {k: v for k, v in r.items() if k != "table"}
            LINES.extend([f"### {seg}, by {nm} (n team-games {len(d)}, games {r['n_games']}): {fmt(r)}", "",
                      r["table"].round(3).to_markdown(floatfmt=".3f"), ""])


if __name__ == "__main__":
    print(time.strftime("%Y-%m-%d %H:%M:%S %z"), flush=True)
    stage1()
    stage3()
    Path("results/responsiveness_slope_recheck.json").write_text(json.dumps(OUT, indent=1, default=float))
    Path("results/responsiveness_slope_recheck.md").write_text("\n".join(LINES) + "\n", encoding="utf-8")
    print("\n".join(LINES))
    print(time.strftime("%Y-%m-%d %H:%M:%S %z"))
