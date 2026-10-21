"""INV-78 (Lane D2, 2026-10-21): recording runner, engine DEFAULT set (goal C1s), goalie pull OFF, shootout stub, ORACLE
GOALIE, on fold 1 (tables rebuilt from the fold-1 artefacts by diag_margin_inv78_tables_v1.py, games 2023-24) or fold 2
(the INV-77 default set exactly as Lane E4's c1s arm: defaults.default_attr + defaults.att_table, stage 1 lc2t2).
DIAGNOSIS ONLY: `sim.py` / `defaults.py` are imported unchanged (HEAD); the hook is a GameState subclass and two
pass-through wrappers on the imported module (Lane D1's form, no random draws, no state change), extended with the
stage-1 penalty process:

  - GameState.goal: (sim, team, second, pre-goal score, skaters) of every goal;
  - GameState.end_second: score snapshots at 20:00 / 40:00 / 55:00 / 60:00;
  - GameState.penalty / coincidental: counts by (period, penalised team, home-view pre-event score sc7, kind);
  - _attempts_second / poisson_k: attempts and exposure seconds by (period, team, team-view state, score sc7).

Fold 2 must reproduce Lane E4's results/engine_defaults_v2_loop/c1s scores exactly (`cmp`).

    diag_margin_inv78_sim_v1.py sim --fold 1 --seed0 0 --nseeds 50   -> results/diag_margin_inv78_v1/f1/rec_0000.npz
    diag_margin_inv78_sim_v1.py cmp                                    (fold 2 vs Lane E4's c1s recording)
"""
import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "diag_margin_inv78_v1"
SNAP_T = (1200, 2400, 3300, 3600)
SEASON = {1: 20232024, 2: 20242025}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_hook(S, N):
    R = dict(g_idx=[], g_team=[], g_t=[], g_pre=[], g_sk=[], snap=np.zeros((len(SNAP_T), N, 2), np.int16),
             att=np.zeros((4, 2, 5, 7), np.int64), expo=np.zeros((4, 5, 7), np.int64),
             pen=np.zeros((4, 2, 7, 3), np.int64), coinc=np.zeros((4, 7), np.int64), ctx=None)
    Base = S._BaseGameState

    def _p_sc(self, idx):
        p = min(int(self.t) // 1200, 3)
        d = self.score[idx, 0].astype(np.int64) - self.score[idx, 1]
        return p, np.clip(d, -3, 3) + 3

    class DiagGS(Base):
        def goal(self, idx, team):
            idx = np.asarray(idx, np.int64)
            if idx.size:
                tm = np.broadcast_to(np.asarray(team, np.int64), idx.shape)
                R["g_idx"].append(idx.copy())
                R["g_team"].append(tm.astype(np.int8).copy())
                R["g_t"].append(np.full(idx.size, self.t, np.int32))
                R["g_pre"].append(self.score[idx].copy())
                R["g_sk"].append(self.skaters()[idx].astype(np.int8))
            return super().goal(idx, team)

        def penalty(self, idx, team, kind, who=None):
            idx = np.asarray(idx, np.int64)
            if idx.size:
                p, sc = _p_sc(self, idx)
                tm = np.broadcast_to(np.asarray(team, np.int64), idx.shape)
                np.add.at(R["pen"][p], (tm, sc, np.full(idx.size, S.KINDS.index(kind))), 1)
            return super().penalty(idx, team, kind, who) if who is not None else super().penalty(idx, team, kind)

        def coincidental(self, idx, single_minor_pair):
            idx = np.asarray(idx, np.int64)
            if idx.size:
                p, sc = _p_sc(self, idx)
                np.add.at(R["coinc"][p], sc, 1)
            return super().coincidental(idx, single_minor_pair)

        def end_second(self):
            super().end_second()
            if self.t in SNAP_T:
                R["snap"][SNAP_T.index(self.t)] = self.score

    def att_wrap(gs, a, t, g_a, st_h, st_a, diff, *rest):
        p = min(t // 1200, 3)
        sc_h = np.clip(diff, -3, 3) + 3
        R["ctx"] = [p, st_h, st_a, sc_h, 6 - sc_h, 0]
        np.add.at(R["expo"][p], (st_h, sc_h), 1)
        out = S._orig_att(gs, a, t, g_a, st_h, st_a, diff, *rest)
        R["ctx"] = None
        return out

    def pk_wrap(u, lam):
        k = S._orig_pk(u, lam)
        c = R["ctx"]
        if c is not None and c[5] < 2:
            tm = c[5]
            st, sc = (c[1], c[3]) if tm == 0 else (c[2], c[4])
            np.add.at(R["att"][c[0], tm], (st, sc), k)
            c[5] += 1
        return k

    S.GameState = DiagGS
    S._attempts_second = att_wrap
    S.poisson_k = pk_wrap
    return R


def build(fold):
    from nhl_sim.engine import defaults as DF
    from nhl_sim.shot_attempt.lookup import goal_stub
    if fold == 1:
        TB = load_mod("inv78_tables", "diag_margin_inv78_tables_v1.py")
        tables, games, info = TB.build_all()
        if info["bad"]:
            raise RuntimeError(f"fold-1 parity failed: {info['bad']}")
        return tables, games
    E2 = load_mod("e2run", "run_engine_c1s_v1.py")
    G2 = E2.g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["p_goal"] = goal_stub(20232024)
    tables["attr"], _ = DF.default_attr(games)
    tables["att_lam"], _ = DF.att_table(games)          # 3v3 OT level ON (default)
    return tables, games


def cmd_sim(a):
    from nhl_sim.data.load import load_games
    from nhl_sim.engine import sim as S
    from nhl_sim.engine.rules import era_for_season
    out = OUT / f"f{a.fold}"
    out.mkdir(parents=True, exist_ok=True)
    season = SEASON[a.fold]
    print(now(), "start fold", a.fold, a.seed0, a.nseeds, flush=True)
    S._BaseGameState, S._orig_att, S._orig_pk = S.GameState, S._attempts_second, S.poisson_k
    tables, games = build(a.fold)
    gt = load_games([season], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        R = install_hook(S, len(games) * n)
        o = S.simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(season), seed0=s0, per_team_types=True,
                       seasons=np.full(len(games), season))
        if int(o["unfinished"]):
            raise RuntimeError("unfinished sims")
        if "block_model" not in o or any(str(m).startswith("block:") for m in o["stand_in"]):
            raise RuntimeError("block is not served as B1a-as")

        def cat(k):
            return np.concatenate(R[k]) if R[k] else np.zeros(0)
        np.savez_compressed(out / f"rec_{s0:04d}.npz", game_id=np.asarray(games, np.int64), seed0=s0, n_seeds=n,
                            game_idx=o["game_idx"], seed=o["seed"], score=o["score"], end_state=o["end_state"],
                            so_home_win=o["so_home_win"], played_s=o["played_s"], snap=R["snap"],
                            g_idx=cat("g_idx"), g_team=cat("g_team"), g_t=cat("g_t"), g_pre=cat("g_pre"),
                            g_sk=cat("g_sk"), att=R["att"], expo=R["expo"], pen=R["pen"], coinc=R["coinc"],
                            n_type=o["n_type"].sum(0), toi_st_sc=o["toi_st_sc"].sum(0), goal_model=str(o["goal_model"][0]),
                            block_model=str(o["block_model"][0]), fold=a.fold)
        print(now(), f"fold {a.fold} seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    print(now(), "done", flush=True)


def cmd_cmp(_a):
    ref_dir = ROOT / "results/engine_defaults_v2_loop/c1s"
    ok, n = True, 0
    for f in sorted((OUT / "f2").glob("rec_*.npz")):
        z = np.load(f)
        r = ref_dir / f.name
        if not r.exists():
            print(f.name, "no E4 file with this seed0")
            ok = False
            continue
        q = np.load(r)
        same = all(np.array_equal(z[k], q[k]) for k in ("game_id", "game_idx", "seed", "score", "end_state", "snap",
                                                          "g_idx", "g_team", "g_t", "g_pre"))
        gi = z["g_idx"]
        fh = np.bincount(gi[z["g_team"] == 0], minlength=len(z["seed"]))
        fa = np.bincount(gi[z["g_team"] == 1], minlength=len(z["seed"]))
        cons = bool((fh == z["score"][:, 0]).all() and (fa == z["score"][:, 1]).all())
        print(f.name, "rows", len(z["seed"]), "identical to E4 c1s", same, "goal log == score", cons)
        ok &= same and cons
        n += len(z["seed"])
    print("ALL IDENTICAL" if ok else "DIFFERENT", n)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "cmp"])
    ap.add_argument("--fold", type=int, choices=[1, 2], default=1)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=25)
    ap.add_argument("--chunk", type=int, default=25)
    a = ap.parse_args()
    {"sim": cmd_sim, "cmp": cmd_cmp}[a.cmd](a)
