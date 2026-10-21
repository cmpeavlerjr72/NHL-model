"""INV-71 (Lane D1, 2026-10-21): diagnostic recording runner for the regulation margin compression. DIAGNOSIS ONLY.

Drives the engine's DEFAULT table set with the goalie pull OFF (Lane E3's loop, `run_engine_defaults_v1.py`; fold 2,
ORACLE GOALIE, B0 / S0t STAND-INS) and adds a recording hook. No engine file is edited: `sim.py` and `defaults.py` are
loaded PINNED from git commit PIN (the D46 HEAD; the working-tree copies are Lane H8b's in-progress edits), and the hook
is a GameState subclass plus two thin wrappers installed on the pinned module only:

  - GameState.goal: records (sim, team, second, pre-goal score, penalty-derived skaters) of every goal;
  - GameState.end_second: snapshots the score after 20:00, 40:00, 55:00 and 60:00 of play;
  - _attempts_second / poisson_k: aggregate attempts and exposure seconds by (period, team, team-view state,
    team-view pre-event score bucket sc7) over all sims (the wrappers return the original values unchanged).

The hook draws no random numbers and changes no state, so the games output must be identical to results/
engine_defaults_v1 for the same seeds (checked by `cmp`).

    diag_margin_inv71_sim_v1.py sim --seed0 0 --nseeds 25    -> results/diag_margin_inv71_v1/rec_0000.npz
    diag_margin_inv71_sim_v1.py cmp                          (games vs results/engine_defaults_v1)
"""
import argparse
import importlib.util
import os
import subprocess
import sys
import time
import types
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
PIN = "8464696"
OUT = ROOT / "results" / "diag_margin_inv71_v1"
TEST, LAST_TRAIN = 20242025, 20232024
SNAP_T = (1200, 2400, 3300, 3600)


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def pinned(modname, relpath):
    src = subprocess.run(["git", "show", f"{PIN}:{relpath}"], cwd=ROOT, capture_output=True, check=True).stdout.decode()
    m = types.ModuleType(modname)
    m.__file__ = str(ROOT / relpath)
    sys.modules[modname] = m
    exec(compile(src, f"{PIN}:{relpath}", "exec"), m.__dict__)
    return m


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_hook(S, N):
    R = dict(g_idx=[], g_team=[], g_t=[], g_pre=[], g_sk=[], snap=np.zeros((len(SNAP_T), N, 2), np.int16),
             att=np.zeros((4, 2, 5, 7), np.int64), expo=np.zeros((4, 5, 7), np.int64), ctx=None)
    Base = S._BaseGameState

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


def cmd_sim(a):
    OUT.mkdir(parents=True, exist_ok=True)
    print(now(), "start", a.seed0, a.nseeds, "pinned", PIN, flush=True)
    S = pinned("nhl_sim.engine.sim", "src/nhl_sim/engine/sim.py")
    S._BaseGameState, S._orig_att, S._orig_pk = S.GameState, S._attempts_second, S.poisson_k
    DF = pinned("nhl_sim.engine.defaults", "src/nhl_sim/engine/defaults.py")
    from nhl_sim.data.load import load_games
    from nhl_sim.engine.rules import era_for_season
    from nhl_sim.shot_attempt.lookup import goal_stub
    E2 = load_mod("e2run", "run_engine_c1s_v1.py")
    G2 = E2.g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"] = np.load(ROOT / "results/shot_attempt_r3/att_lam_A3g-c_fold2.npy")
    tables["p_goal"] = goal_stub(LAST_TRAIN)
    tables["attr"], _info = DF.default_attr(games)
    gt = load_games([TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        R = install_hook(S, len(games) * n)
        o = S.simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(TEST), seed0=s0, per_team_types=True,
                       seasons=np.full(len(games), TEST))
        if int(o["unfinished"]):
            raise RuntimeError("unfinished sims")

        def cat(k):
            return np.concatenate(R[k]) if R[k] else np.zeros(0)
        np.savez_compressed(OUT / f"rec_{s0:04d}.npz", game_id=np.asarray(games, np.int64), seed0=s0, n_seeds=n,
                            game_idx=o["game_idx"], seed=o["seed"], score=o["score"], end_state=o["end_state"],
                            so_home_win=o["so_home_win"], played_s=o["played_s"], snap=R["snap"],
                            g_idx=cat("g_idx"), g_team=cat("g_team"), g_t=cat("g_t"), g_pre=cat("g_pre"),
                            g_sk=cat("g_sk"), att=R["att"], expo=R["expo"], toi_st_sc=o["toi_st_sc"].sum(0),
                            att_sc=o["att_sc"].sum(0), att_st=o["att_st"].sum(0), pin=PIN)
        print(now(), f"seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    print(now(), "done", flush=True)


def cmd_cmp(a):
    ref = pd.read_parquet(ROOT / "results/engine_defaults_v1/games.parquet").set_index(["game_id", "seed"])
    ok, n = True, 0
    for f in sorted(OUT.glob("rec_*.npz")):
        z = np.load(f)
        gid = z["game_id"][z["game_idx"]]
        d = pd.DataFrame({"game_id": gid, "seed": z["seed"], "h": z["score"][:, 0], "a": z["score"][:, 1],
                          "es": np.array(["", "REG", "OT", "SO"])[z["end_state"]]}).set_index(["game_id", "seed"])
        r = ref.loc[d.index]
        same = (r.home_goals.to_numpy() == d.h.to_numpy()) & (r.away_goals.to_numpy() == d.a.to_numpy()) & \
               (r.end_state.to_numpy() == d.es.to_numpy())
        gi = z["g_idx"]
        fh = np.bincount(gi[z["g_team"] == 0], minlength=len(d))
        fa = np.bincount(gi[z["g_team"] == 1], minlength=len(d))
        cons = bool((fh == z["score"][:, 0]).all() and (fa == z["score"][:, 1]).all())
        print(f.name, "rows", len(d), "identical to E3", bool(same.all()), "goal log == score", cons)
        ok &= bool(same.all()) and cons
        n += len(d)
    print("ALL IDENTICAL" if ok else "DIFFERENT", n)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "cmp"])
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=25)
    ap.add_argument("--chunk", type=int, default=25)
    a = ap.parse_args()
    {"sim": cmd_sim, "cmp": cmd_cmp}[a.cmd](a)
