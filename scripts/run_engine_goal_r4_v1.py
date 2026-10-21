"""G-R4 (Lane G4): paired-seed closed loop, fold 2 (2024-25), goalie pull OFF, ORACLE GOALIE, for the goal arms
  c1s : the engine DEFAULT table set (`defaults.default_attr`; goal C1s)
  sap : the same table set with attr["goal"] replaced by C1s-sap (`goal_r4_tables.goal_r4_tables`, the default-off
        sc_game flag); every other table identical, so every RNG stream is aligned (seed, game, family)
A recording hook (Lane D1's form, `diag_margin_inv71_sim_v1.py`: a GameState subclass, no random draws, no state change)
logs every goal's pre-goal score and snapshots the score at 20:00 / 40:00 / 55:00 / 60:00.

    run_engine_goal_r4_v1.py sim --arm sap --seed0 0 --nseeds 50     -> results/goal_r4_loop_v1/<arm>/rec_<seed0>.npz
    run_engine_goal_r4_v1.py grade                                     -> results/goal_r4_loop_v1/grade.json,
                                                                          docs/tests/goal_g_r4_loop_2026-10-21.md
Gates (G-R4 spec): G5b (docs/gates.yaml: at 55:00, pull off, vs actual with goalie-out goals removed; tie share and
|margin| cells 0 / 1 / 2 / 3+ within 1.5 pp; regular season), team-standardised goal O/E by bucket within 1 SE of real,
G4 unchanged within noise (save % by state, sap vs c1s, paired seed-block SE).
"""
import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "2")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "goal_r4_loop_v1"
REPORT = ROOT / "docs/tests/goal_g_r4_loop_2026-10-21.md"
TEST, LAST_TRAIN = 20242025, 20232024
SNAP_T = (1200, 2400, 3300, 3600)
SNAP_L = ("20:00", "40:00", "55:00", "60:00")
B_OF_SC7 = np.array([0, 0, 1, 2, 3, 4, 4])
BUCK = ["trail2+", "trail1", "tied", "lead1", "lead2+"]
ST = ("5v5", "PP", "PK", "4v4", "3v3")


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def install_hook(S, N):
    R = dict(g_idx=[], g_team=[], g_t=[], g_pre=[], snap=np.zeros((len(SNAP_T), N, 2), np.int16))
    Base = S._BaseGameState

    class RecGS(Base):
        def goal(self, idx, team):
            idx = np.asarray(idx, np.int64)
            if idx.size:
                tm = np.broadcast_to(np.asarray(team, np.int64), idx.shape)
                R["g_idx"].append(idx.copy())
                R["g_team"].append(tm.astype(np.int8).copy())
                R["g_t"].append(np.full(idx.size, self.t, np.int32))
                R["g_pre"].append(self.score[idx].copy())
            return super().goal(idx, team)

        def end_second(self):
            super().end_second()
            if self.t in SNAP_T:
                R["snap"][SNAP_T.index(self.t)] = self.score

    S.GameState = RecGS
    return R


def build(arm):
    from nhl_sim.engine import defaults as DF
    from nhl_sim.engine import goal_r4_tables as GR
    from nhl_sim.shot_attempt.lookup import goal_stub
    E2 = load_mod("e2run", "run_engine_c1s_v1.py")
    G2 = E2.g2mod()
    tables, games, _ = G2.stage1_tables("lc2t2")
    tables["att_lam"] = np.load(ROOT / "results/shot_attempt_r3/att_lam_A3g-c_fold2.npy")
    tables["p_goal"] = goal_stub(LAST_TRAIN)
    attr, info = DF.default_attr(games)
    if arm == "sap":
        from nhl_sim.engine import c1s_tables as CT
        P = CT._goal_parts(games)
        goal, ginfo = GR.goal_r4_tables(games, P=P)
        par = GR.goal_r4_parity(games, goal, P, use_engine=True)
        print(now(), f"C1s-sap served vs offline: max |diff| {par['max_abs_diff']:.3e} over {par['n_rows']:,} rows", flush=True)
        if not par["max_abs_diff"] <= 1e-6:
            raise RuntimeError(f"served != offline: {par['max_abs_diff']}")
        attr["goal"] = goal
    tables["attr"] = attr
    return tables, games


def cmd_sim(a):
    from nhl_sim.data.load import load_games
    from nhl_sim.engine import sim as S
    from nhl_sim.engine.rules import era_for_season
    out = OUT / a.arm
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", a.arm, a.seed0, a.nseeds, flush=True)
    S._BaseGameState = S.GameState
    tables, games = build(a.arm)
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
        np.savez_compressed(out / f"rec_{s0:04d}.npz", game_id=np.asarray(games, np.int64), seed0=s0, n_seeds=n,
                            game_idx=o["game_idx"], seed=o["seed"], score=o["score"], end_state=o["end_state"],
                            snap=R["snap"], g_idx=cat("g_idx"), g_team=cat("g_team"), g_t=cat("g_t"), g_pre=cat("g_pre"),
                            toi_sc=o["toi_st_sc"].sum(1).astype(np.int32), sog=o["attr_sog"], goals=o["attr_goals"],
                            goal_model=str(o["goal_model"][0]))
        print(now(), f"{a.arm} seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    print(now(), "done", flush=True)


# ------------------------------------------------------------------------------------------------------- grade
def load_arm(arm):
    fs = sorted((OUT / arm).glob("rec_*.npz"))
    games, parts = None, []
    for f in fs:
        z = np.load(f)
        games = z["game_id"] if games is None else games
        assert (z["game_id"] == games).all()
        n = len(z["seed"])
        th = z["g_team"] == 0
        pre = z["g_pre"].astype(int)
        dd = np.where(th, pre[:, 0] - pre[:, 1], pre[:, 1] - pre[:, 0])
        sc7 = np.clip(dd, -3, 3) + 3
        gl = np.zeros((n, 2, 7))
        np.add.at(gl, (z["g_idx"], z["g_team"].astype(int), sc7), 1)
        parts.append(dict(gi=z["game_idx"], seed=z["seed"], score=z["score"].astype(int), es=z["end_state"],
                          snap=z["snap"].astype(int), toi=z["toi_sc"].astype(float), gl=gl, sog=z["sog"].astype(float),
                          goals=z["goals"].astype(float)))
    cat = {k: np.concatenate([p[k] for p in parts], axis=1 if k == "snap" else 0) for k in parts[0]}
    o = np.lexsort((cat["gi"], cat["seed"]))
    cat = {k: (v[:, o] if k == "snap" else v[o]) for k, v in cat.items()}
    return games, cat


def oe_sim(C, home_t, away_t):
    """Team-standardised goal O/E by bucket, tied = 1 (Lane D1 item 2b): E = exposure x the team's own season rate."""
    Eh, Ea = C["toi"], C["toi"][:, ::-1]
    Yh, Ya = C["gl"][:, 0], C["gl"][:, 1]
    tm = np.concatenate([home_t, away_t])
    E_ = np.vstack([Eh, Ea])
    Y_ = np.vstack([Yh, Ya])
    rate = pd.Series(Y_.sum(1)).groupby(tm).sum() / pd.Series(E_.sum(1)).groupby(tm).sum()
    E = (E_ * rate.loc[tm].to_numpy()[:, None]).sum(0)
    O = Y_.sum(0)
    o5 = np.array([O[B_OF_SC7 == b].sum() for b in range(5)])
    e5 = np.array([E[B_OF_SC7 == b].sum() for b in range(5)])
    r = o5 / e5
    return r / r[2]


def cmd_grade(a):
    D1 = load_mod("d1grade", "diag_margin_inv71_grade_v1.py")
    gates = {}
    for line in (ROOT / "docs/gates.yaml").read_text().splitlines():
        if line.startswith("g5b_"):
            k, v = line.split(":")[0], float(line.split(":")[1].split("#")[0])
            gates[k] = v
    arms = [x for x in ("c1s", "sap") if (OUT / x).exists()]
    data = {x: load_arm(x) for x in arms}
    games = data[arms[0]][0]
    F, g, e = D1.load_real(games)
    rs = (F.gtype == 2).to_numpy() & F.pbp_ok.to_numpy()
    allg = F.pbp_ok.to_numpy()
    home_t, away_t = F.home.to_numpy(), F.away.to_numpy()
    res = dict(arms=arms, gates=gates)
    L = ["# G-R4 closed loop: C1s vs C1s-sap, paired seeds (Lane G4, 2026-10-21)", "",
         f"Generated {now()} by `scripts/run_engine_goal_r4_v1.py grade`. Fold 2 (2024-25), goalie pull OFF, ORACLE GOALIE "
         "(D8), engine DEFAULT table set (block B0 and miss S0t STAND-INS, stage 4 L1x-as); only attr['goal'] differs "
         "between arms, so every RNG stream is aligned. Real = verified finals / pbp with goalie-out goals removed (Lane D1's "
         "construction, `diag_margin_inv71_grade_v1.load_real`).", ""]
    # ---- G5b at 55:00 (and the other snapshots, reported)
    for scope, gm in (("regular season (gate)", rs), ("all games", allg)):
        n = int(gm.sum())
        rows = []
        for T, lab in zip(SNAP_T, SNAP_L):
            h, a_ = D1.score_at(g, games, T, "g_out")
            ra = D1.dist_margin((h - a_)[gm])[0]
            se = [float(np.sqrt(p * (1 - p) / n)) for p in ra]
            rec = dict(time=lab, **{f"real_{k}": ra[k] for k in range(4)}, real_tie_se=se[0])
            for x in arms:
                _, C = data[x]
                sm = gm[C["gi"]]
                ds = (C["snap"][SNAP_T.index(T), :, 0] - C["snap"][SNAP_T.index(T), :, 1])[sm]
                sa = D1.dist_margin(ds)[0]
                for k in range(4):
                    rec[f"{x}_{k}"] = sa[k]
            rows.append(rec)
        Tb = pd.DataFrame(rows).set_index("time")
        res[f"margin_{'rs' if gm is rs else 'all'}"] = Tb.reset_index().to_dict("records")
        L += [f"## |margin| distribution by time, {scope} (n real = {n}; cells 0 / 1 / 2 / 3+)", "",
              Tb.to_markdown(floatfmt=".4f"), ""]
        if gm is rs:
            r55 = Tb.loc["55:00"]
            for x in arms:
                d = [100 * (r55[f"{x}_{k}"] - r55[f"real_{k}"]) for k in range(4)]
                ok = abs(d[0]) <= gates["g5b_tie_pp"] and all(abs(v) <= gates["g5b_margin_cell_pp"] for v in d)
                res[f"g5b_{x}"] = dict(diff_pp=d, status="PASS" if ok else "FAIL")
                L.append(f"- **G5b {x}** (55:00, RS): sim - real (pp) tie {d[0]:+.2f}, |1| {d[1]:+.2f}, |2| {d[2]:+.2f}, "
                         f"3+ {d[3]:+.2f}; real tie SE {100 * r55['real_tie_se']:.2f} pp -> **{'PASS' if ok else 'FAIL'}**")
            L.append("")
    # ---- team-standardised goal O/E by bucket
    ar = pd.read_parquet(ROOT / f"data/processed/shot_attempt/attempt_rows_v1_{TEST}.parquet",
                         columns=["game_id", "st", "sc", "exposure_s", "y_goal", "is_home"])
    ar = ar[(ar.st <= 4) & ar.game_id.isin(games)]
    fi = F.set_index("game_id")
    ar["tm"] = np.where(ar.is_home == 1, fi.home.loc[ar.game_id].to_numpy(), fi.away.loc[ar.game_id].to_numpy())
    rate = ar.groupby("tm").y_goal.sum() / ar.groupby("tm").exposure_s.sum()
    E = (ar.exposure_s * rate.loc[ar.tm].to_numpy()).groupby(ar.sc).sum().reindex(range(7), fill_value=0).to_numpy()
    O = ar.groupby("sc").y_goal.sum().reindex(range(7), fill_value=0).to_numpy()
    o5 = np.array([O[B_OF_SC7 == b].sum() for b in range(5)])
    e5 = np.array([E[B_OF_SC7 == b].sum() for b in range(5)])
    rr = (o5 / e5) / (o5[2] / e5[2])
    rse = np.sqrt(1 / np.maximum(o5, 1) + 1 / o5[2]) * rr
    rows = [dict(series="real", **dict(zip(BUCK, rr))), dict(series="real SE", **dict(zip(BUCK, rse)))]
    for x in arms:
        _, C = data[x]
        so = oe_sim(C, home_t[C["gi"]], away_t[C["gi"]])
        z = (so - rr) / np.where(rse > 0, rse, np.nan)
        rows.append(dict(series=f"sim {x}", **dict(zip(BUCK, so))))
        rows.append(dict(series=f"z {x}", **dict(zip(BUCK, z))))
        ok = bool(np.nanmax(np.abs(z)) <= 1.0)
        res[f"oe_{x}"] = dict(ratio=so.tolist(), z=z.tolist(), status="PASS" if ok else "FAIL")
    OEt = pd.DataFrame(rows).set_index("series")
    res["oe_real"] = dict(ratio=rr.tolist(), se=rse.tolist(), n=o5.tolist())
    L += ["## Team-standardised goal O/E by pre-goal score bucket (tied = 1), all games, non-EN states", "",
          "E = exposure x the team's own season goal rate (Lane D1 item 2b). Gate: |sim - real| <= 1 real SE per bucket.", "",
          OEt.to_markdown(floatfmt=".4f"), ""]
    for x in arms:
        L.append(f"- **O/E {x}**: max |z| {np.nanmax(np.abs(res[f'oe_{x}']['z'])):.2f} -> **{res[f'oe_{x}']['status']}**")
    L.append("")
    # ---- G4: save % by state, and sap vs c1s paired
    e2 = e[e.type_desc_key.isin(["shot-on-goal", "goal"])]
    rows = []
    for x in arms:
        _, C = data[x]
        sog, gl = C["sog"].sum(1), C["goals"].sum(1)
        for k, nm in enumerate(ST):
            rows.append(dict(arm=x, state=nm, sog_per_game=sog[:, k].sum() / len(sog) * 1.0,
                             sv_pct=100 * (1 - gl[:, k].sum() / sog[:, k].sum())))
        rows.append(dict(arm=x, state="all", sog_per_game=sog.sum() / len(sog), sv_pct=100 * (1 - gl.sum() / sog.sum())))
    G4 = pd.DataFrame(rows).pivot(index="state", columns="arm", values="sv_pct")
    if len(arms) == 2:
        _, A = data["c1s"]
        _, B = data["sap"]
        assert (A["gi"] == B["gi"]).all() and (A["seed"] == B["seed"]).all()
        seeds = np.unique(A["seed"])
        rng = np.random.default_rng(20261021)
        W = rng.multinomial(len(seeds), np.full(len(seeds), 1 / len(seeds)), size=500)
        sp = np.searchsorted(seeds, A["seed"])
        se = {}
        for k, nm in list(enumerate(ST)) + [(None, "all")]:
            def tot(C):
                s_ = C["sog"].sum(1)
                g_ = C["goals"].sum(1)
                s_ = s_.sum(1) if k is None else s_[:, k]
                g_ = g_.sum(1) if k is None else g_[:, k]
                return np.bincount(sp, weights=s_, minlength=len(seeds)), np.bincount(sp, weights=g_, minlength=len(seeds))
            sa_, ga_ = tot(A)
            sb_, gb_ = tot(B)
            dv = 100 * ((1 - (W @ gb_) / (W @ sb_)) - (1 - (W @ ga_) / (W @ sa_)))
            se[nm] = float(dv.std())
        G4["sap_minus_c1s_pp"] = G4["sap"] - G4["c1s"]
        G4["paired_seed_se_pp"] = pd.Series(se)
        # real sv% by state is reported for reference (the in-loop G4 grid lives in the INV-60 doc)
    res["g4"] = G4.reset_index().to_dict("records")
    L += ["## G4: save % by state in the loop (sap vs c1s; paired seed-block SE, 500 resamples)", "",
          G4.to_markdown(floatfmt=".4f"), "",
          "Reading: G4 'unchanged within noise' = |sap - c1s| <= 2 paired SE in every gated state, and the overall sv % "
          "of each arm within the g4_sv_pp 0.5 pp of actual (actual from the stage-6 rows, below).", ""]
    rows6 = pd.read_parquet(ROOT / "results/goal_g_r4/fold2/fold2_rows.parquet", columns=["sg", "y"])
    act = {nm: 100 * (1 - rows6.y[rows6.sg == k].mean()) for k, nm in enumerate(ST)}
    act["all"] = 100 * (1 - rows6.y[rows6.sg <= 4].mean())
    G4a = pd.DataFrame({"actual_sv_pct": pd.Series(act)})
    for x in arms:
        G4a[f"{x}_minus_actual_pp"] = G4[x] - G4a.actual_sv_pct
    res["g4_actual"] = G4a.reset_index().to_dict("records")
    L += [G4a.to_markdown(floatfmt=".4f"), ""]
    (OUT / "grade.json").write_text(json.dumps(res, indent=1, default=float))
    REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--arm", choices=["c1s", "sap"], default="sap")
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    a = ap.parse_args()
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
