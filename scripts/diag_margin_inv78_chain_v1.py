"""INV-78 (Lane D2, 2026-10-21): offline conversion chain by period x pre-event score bucket, both folds, for the
CURRENT default set (L1x-as, block B1a-as, miss S0t, goal C1s; Lane D1's chain_v1 used block B0). DIAGNOSIS ONLY.

On every actual non-EN attempt of the test season (attempt_attr_v1_<season>), the served tables (fold 2:
defaults.default_attr; fold 1: diag_margin_inv78_tables_v1.build_all) give per row:
  block   sim.block_prob (B1a-as, score bucket and period type)       vs actual blocked
  stage 4 class row -> E[xG_ref] per unblocked attempt                 vs xG_ref of the actual class
  miss    S0t p_miss[g, group, ptype, actual class]                    vs actual miss (unblocked rows)
  goal    C1s p_goal[actual class, st, sc] per shot on goal            vs actual goal (SOG rows)
  chain   (1 - p_block) x sum_c pi(c) (1 - p_miss(c)) p_goal(c)        vs actual goal per attempt
reported as served / actual by bucket and by period, plus a parametric redraw SD of the full-chain ratio per cell
(goals ~ Bernoulli(served chain prob), 500 draws; L39).

    diag_margin_inv78_chain_v1.py --fold 1|2   -> results/diag_margin_inv78_v1/chain_f<fold>.json
"""
import argparse
import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
OUT = ROOT / "results" / "diag_margin_inv78_v1"
B_OF_SC7 = np.array([0, 0, 1, 2, 3, 4, 4])
BUCK = ["trail2+", "trail1", "tied", "lead1", "lead2+"]
ST_RGRP = np.array([0, 1, 2, 0, 0])
SEASON = {1: 20232024, 2: 20242025}


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(fold):
    from nhl_sim.engine import sim as S
    if fold == 1:
        TB = load_mod("inv78_tables", "diag_margin_inv78_tables_v1.py")
        tables, games, info = TB.build_all()
        assert not info["bad"]
        attr = tables["attr"]
        xg = np.load(ROOT / "data/processed/shot_attribute/xg_ref_v1_f1.npy")[:, :3]
    else:
        from nhl_sim.engine import defaults as DF
        games = np.load(sorted((OUT / "f2").glob("rec_*.npz"))[0])["game_id"]
        attr, _ = DF.default_attr(games)
        xg = np.load(ROOT / "data/processed/shot_attribute/xg_ref_v1_f2.npy")[:, :3]
    a = pd.read_parquet(ROOT / f"data/processed/shot_attribute/attempt_attr_v1_{SEASON[fold]}.parquet",
                        columns=["game_id", "team", "st", "sc", "ptype", "period", "event", "blocked", "is_goal", "cls", "t"]
                        if False else ["game_id", "team", "st", "sc", "ptype", "period", "event", "blocked", "is_goal", "cls"])
    a = a[(a.st <= 4) & a.game_id.isin(games)].reset_index(drop=True)
    gi = pd.Series(np.arange(len(games)), index=games).loc[a.game_id].to_numpy()
    team, st, sc, pt = (a[c].to_numpy().astype(np.int64) for c in ("team", "st", "sc", "ptype"))
    rg = ST_RGRP[st]
    pbg = np.asarray(attr["p_block_game"], np.float64)
    bx = attr["block_b1aas"]
    ASb = dict(p_block_game=pbg, b1aas_base=np.log(pbg) - np.log1p(-pbg), b1aas_game=bx["game_logit"], b1aas_sc=bx["sc_logit"])
    pb = np.zeros(len(a))
    for tm in (0, 1):
        for p_ in (0, 1):
            k = (team == tm) & (pt == p_)
            pb[k] = S.block_prob(ASb, gi[k], st[k], 3600 * p_, tm, sc[k])
    AS = dict(goal_cls=attr["goal"]["cls_logit"], goal_game=attr["goal"]["game_logit"], goal_sc=attr["goal"]["sc_logit"],
              state_pdf=attr["state_pdf"], game_mult=attr["game_mult"], l1x_base=np.log(attr["state_pdf"]),
              l1x_lgm=np.log(attr["game_mult"]), l1x_game=attr["l1x"]["game_logit"], l1x_sc=attr["l1x"]["sc_logit"])
    C = AS["goal_cls"].shape[0]
    pi = np.zeros((len(a), C))
    for p_ in (0, 1):
        for tm in (0, 1):
            k = np.flatnonzero((pt == p_) & (team == tm))
            for ch in np.array_split(k, max(1, len(k) // 20000)):
                row = S.class_cdf(AS, None, gi[ch], tm, st[ch], sc[ch], 0, 3600 * p_)
                pi[ch] = np.diff(np.c_[np.zeros(len(ch)), row], axis=1)
    pm_all = attr["p_miss_game"][gi, rg, pt]
    pg_all = np.zeros((len(a), C))
    for c in range(C):
        pg_all[:, c] = S.goal_prob(AS, gi, team, st, sc, np.full(len(a), c))
    cls = np.maximum(a.cls.to_numpy().astype(np.int64), 0)
    ub = ~a.blocked.to_numpy()
    sog = ub & a.event.isin(["SHOT", "GOAL"]).to_numpy()
    miss = ub & (a.event == "MISS").to_numpy()
    goal = a.is_goal.to_numpy().astype(float)
    r = np.arange(len(a))
    conv_s = (1 - pb) * (pi * (1 - pm_all) * pg_all).sum(1)
    D = pd.DataFrame(dict(b=B_OF_SC7[sc], st=st, period=np.minimum(a.period.to_numpy(), 4),
                          blk_a=a.blocked.to_numpy().astype(float), blk_s=pb,
                          ub=ub.astype(float), xg_a=np.where(ub, xg[cls, rg], 0.0), xg_s=np.where(ub, (pi * xg.T[rg]).sum(1), 0.0),
                          miss_a=miss.astype(float), miss_s=np.where(ub, pm_all[r, cls], 0.0),
                          sog=sog.astype(float), g_sog_a=np.where(sog, goal, 0.0), g_sog_s=np.where(sog, pg_all[r, cls], 0.0),
                          conv_a=goal, conv_s=conv_s))
    rng = np.random.default_rng(20261021)
    res = {}

    def table(name, m):
        Dm = D[m]
        g = Dm.groupby("b").sum()
        n = Dm.groupby("b").size()
        t = pd.DataFrame(index=g.index)
        t["n_att"] = n
        t["goals"] = g.conv_a
        t["block s/a"] = g.blk_s / g.blk_a
        t["unblocked s/a"] = (n - g.blk_s) / (n - g.blk_a)
        t["xG/unb s/a"] = g.xg_s / g.xg_a
        t["miss s/a"] = g.miss_s / g.miss_a
        t["SOG|unb s/a"] = (g.ub - g.miss_s) / (g.ub - g.miss_a)
        t["goal|SOG s/a"] = g.g_sog_s / g.g_sog_a
        t["full chain s/a"] = g.conv_s / g.conv_a
        # parametric redraw SD of the full-chain ratio (actual goals redrawn from the served probability)
        sd = []
        for b in g.index:
            p = Dm.conv_s.to_numpy()[Dm.b.to_numpy() == b]
            sims = rng.binomial(1, np.broadcast_to(p, (300, len(p)))).sum(1) if len(p) < 60000 else \
                rng.poisson(p.sum(), 300)
            sd.append(float(np.std(p.sum() / sims)))
        t["full chain redraw SD"] = sd
        t.index = [BUCK[i] for i in t.index]
        print(f"\n-- fold {fold} {name}")
        print(t.round(4).T.to_string())
        res[name] = t.round(5).to_dict()

    table("all non-EN states, regulation", (D.period <= 3).to_numpy())
    for p in (1, 2, 3):
        table(f"all non-EN states, P{p}", (D.period == p).to_numpy())
    table("5v5, P2", ((D.period == 2) & (D.st == 0)).to_numpy())
    table("5v5, P3", ((D.period == 3) & (D.st == 0)).to_numpy())
    (OUT / f"chain_f{fold}.json").write_text(json.dumps(res, indent=1, default=float))
    print("wrote", OUT / f"chain_f{fold}.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fold", type=int, choices=[1, 2], required=True)
    main(ap.parse_args().fold)
