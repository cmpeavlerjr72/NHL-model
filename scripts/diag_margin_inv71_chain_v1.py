"""INV-71 (Lane D1, 2026-10-21): offline conversion chain by pre-event score bucket. DIAGNOSIS ONLY.

On every actual fold-2 non-EN attempt (data/processed/shot_attribute/attempt_attr_v1_20242025.parquet; team-view state
st 0..4 and score bucket sc7), the engine's DEFAULT served tables (pinned `defaults.py` / `sim.py` at 8464696, the same
tables the closed loop used) give, per row:
  block   B0 stand-in p_block[g, st, ptype]                       vs actual blocked
  stage 4 L1x-as class row -> E[xG_ref] per unblocked attempt      vs xG_ref of the actual class
  miss    S0t stand-in p_miss[g, group, ptype, actual class]      vs actual miss (unblocked rows)
  goal    C1s p_goal[actual class, st, sc] per shot on goal        vs actual goal (SOG rows)
  chain   (1 - p_block) x sum_c pi(c) (1 - p_miss(c)) p_goal(c)    vs actual goal per attempt
reported as served / actual by bucket (trail2+, trail1, tied, lead1, lead2+), overall, 5v5, and by period, plus the
same normalised to tied = 1 (the score-effect shape, comparable with the closed-loop team-standardised O/E).

    diag_margin_inv71_chain_v1.py   -> results/diag_margin_inv71_v1/chain.json
"""
import json
import subprocess
import sys
import types
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
PIN = "8464696"
OUT = ROOT / "results" / "diag_margin_inv71_v1"
B_OF_SC7 = np.array([0, 0, 1, 2, 3, 4, 4])
BUCK = ["trail2+", "trail1", "tied", "lead1", "lead2+"]
ST_RGRP = np.array([0, 1, 2, 0, 0])


def pinned(modname, relpath):
    src = subprocess.run(["git", "show", f"{PIN}:{relpath}"], cwd=ROOT, capture_output=True, check=True).stdout.decode()
    m = types.ModuleType(modname)
    m.__file__ = str(ROOT / relpath)
    sys.modules[modname] = m
    exec(compile(src, f"{PIN}:{relpath}", "exec"), m.__dict__)
    return m


def main():
    S = pinned("nhl_sim.engine.sim", "src/nhl_sim/engine/sim.py")
    DF = pinned("nhl_sim.engine.defaults", "src/nhl_sim/engine/defaults.py")
    games = np.load(sorted(OUT.glob("rec_*.npz"))[0])["game_id"]
    attr, _ = DF.default_attr(games)
    xg = np.load(ROOT / "data/processed/shot_attribute/xg_ref_v1_f2.npy")[:, :3]
    a = pd.read_parquet(ROOT / "data/processed/shot_attribute/attempt_attr_v1_20242025.parquet",
                        columns=["game_id", "team", "st", "sc", "ptype", "period", "event", "blocked", "is_goal", "cls"])
    a = a[(a.st <= 4) & a.game_id.isin(games)].reset_index(drop=True)
    gi = pd.Series(np.arange(len(games)), index=games).loc[a.game_id].to_numpy()
    team, st, sc, pt = (a[c].to_numpy().astype(np.int64) for c in ("team", "st", "sc", "ptype"))
    rg = ST_RGRP[st]
    pb = attr["p_block_game"][gi, st, pt]
    AS = dict(goal_cls=attr["goal"]["cls_logit"], goal_game=attr["goal"]["game_logit"], goal_sc=attr["goal"]["sc_logit"],
              state_pdf=attr["state_pdf"], game_mult=attr["game_mult"], l1x_base=np.log(attr["state_pdf"]),
              l1x_lgm=np.log(attr["game_mult"]), l1x_game=attr["l1x"]["game_logit"], l1x_sc=attr["l1x"]["sc_logit"])
    C = AS["goal_cls"].shape[0]
    pi = np.zeros((len(a), C))
    for p in (0, 1):
        for tm in (0, 1):
            k = np.flatnonzero((pt == p) & (team == tm))
            for ch in np.array_split(k, max(1, len(k) // 20000)):
                row = S.class_cdf(AS, None, gi[ch], tm, st[ch], sc[ch], 0, 3600 * p)
                pi[ch] = np.diff(np.c_[np.zeros(len(ch)), row], axis=1)
    pm_all = attr["p_miss_game"][gi, rg, pt]                       # (n, C)
    pg_all = np.zeros((len(a), C))
    for c in range(C):
        pg_all[:, c] = S.goal_prob(AS, gi, team, st, sc, np.full(len(a), c))
    cls = np.maximum(a.cls.to_numpy().astype(np.int64), 0)
    ub = ~a.blocked.to_numpy()
    sog = ub & a.event.isin(["SHOT", "GOAL"]).to_numpy()
    miss = ub & (a.event == "MISS").to_numpy()
    goal = a.is_goal.to_numpy().astype(float)
    r = np.arange(len(a))
    D = pd.DataFrame(dict(b=B_OF_SC7[sc], st=st, period=np.minimum(a.period.to_numpy(), 4),
                          blk_a=a.blocked.to_numpy().astype(float), blk_s=pb,
                          ub=ub.astype(float), xg_a=np.where(ub, xg[cls, rg], 0.0), xg_s=np.where(ub, (pi * xg.T[rg]).sum(1), 0.0),
                          miss_a=miss.astype(float), miss_s=np.where(ub, pm_all[r, cls], 0.0),
                          sog=sog.astype(float), g_sog_a=np.where(sog, goal, 0.0), g_sog_s=np.where(sog, pg_all[r, cls], 0.0),
                          conv_a=goal, conv_s=(1 - pb) * (pi * (1 - pm_all) * pg_all).sum(1),
                          conv_s_ub_act=np.where(ub, (1 - pm_all[r, cls]) * pg_all[r, cls], 0.0)))
    res = {}

    def table(name, m):
        g = D[m].groupby("b").sum()
        n = D[m].groupby("b").size()
        t = pd.DataFrame(index=g.index)
        t["n_att"] = n
        t["goals"] = g.conv_a
        t["block s/a"] = g.blk_s / g.blk_a
        t["xG/unb s/a (stage 4)"] = g.xg_s / g.xg_a
        t["miss s/a (S0t)"] = g.miss_s / g.miss_a
        t["goal|SOG s/a (C1s)"] = g.g_sog_s / g.g_sog_a
        t["unb->goal s/a (S0t x C1s, actual class)"] = g.conv_s_ub_act / g.conv_a
        t["goal/attempt s/a (full chain)"] = g.conv_s / g.conv_a
        t["actual block %"] = g.blk_a / n * 100
        t["actual miss|unb %"] = g.miss_a / g.ub * 100
        t["actual goal|SOG %"] = g.g_sog_a / g.sog * 100
        t["actual goal/att %"] = g.conv_a / n * 100
        t["served goal/att %"] = g.conv_s / n * 100
        t.index = [BUCK[i] for i in t.index]
        print(f"\n-- {name}")
        print(t.round(4).T.to_string())
        rel = t[["goal/attempt s/a (full chain)", "block s/a", "miss s/a (S0t)", "goal|SOG s/a (C1s)", "xG/unb s/a (stage 4)"]]
        res[name] = dict(table=t.round(5).to_dict(), goals_se=(1 / np.sqrt(t.goals)).round(4).tolist())
        return t

    table("all non-EN states, all periods", np.ones(len(D), bool))
    table("5v5, all periods", (D.st == 0).to_numpy())
    for p in (1, 2, 3):
        table(f"all non-EN states, P{p}", (D.period == p).to_numpy())
    table("all non-EN states, P1+P2 (before 40:00)", (D.period <= 2).to_numpy())
    (OUT / "chain.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote", OUT / "chain.json")


if __name__ == "__main__":
    main()
