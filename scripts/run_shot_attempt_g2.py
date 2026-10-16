"""SA-R1 step 3: closed-loop G2 for a shot-attempt arm (docs/models/shot_attempt/experiments.md SA-R1).

Engine: the stage-1 incumbent (H3'' + T1, D15; tables from `run_strength_state_g1_v3.build_tables`) drives the
strength-state timeline; attempts come from the arm under test (`shot_attempt.lookup.attempt_table`, engine variant
"att_lam"); goals come from a LABELLED STUB (league goals per attempt by strength state, 2023-24 = the last fold-2
training season, no team terms, not graded). No goalie pull (EN unreachable), shootout skipped.

    run_shot_attempt_g2.py sim   --arm A3 --seed0 0 --nseeds 50 [--tag sa_r1_g2_A3]   (one seed block; run blocks
                                                                                       as parallel processes)
    SA-R2 (INV-31): add --round SA-R2 (results/shot_attempt_r2, LC-1 tables v2, g arms on group levels);
    --stage1 r3c uses the SS-R3c re-levelled stage-1 incumbent (results/strength_state_r3c) instead of D15's H3''.
    SA-R3 (INV-32): --round SA-R3 (results/shot_attempt_r3; arms A3g, A3g-c, A2g-c, A3g-s with level "lc1s");
    --stage1 r3t2 = H3'' + T2 (the incumbent at SA-R3 launch): the cached H3'' hazard table and the T2 per-team type
    table of results/strength_state_r5 (SS-R5), run through engine.sim with per_team_types=True (the merged T2 flag).
    run_shot_attempt_g2.py grade --arm A3 [--tag sa_r1_g2_A3]   (merge blocks; G2 RS / PO / overall, 100 vs 200
                                                                 seeds, D14 decomposition, closed-loop responsiveness)
"""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from nhl_sim.data.load import load_games  # noqa: E402
from nhl_sim.engine.rules import era_for_season  # noqa: E402
from nhl_sim.engine.sim import simulate  # noqa: E402
from nhl_sim.eval import g2 as G2  # noqa: E402
from nhl_sim.shot_attempt import models as S  # noqa: E402
from nhl_sim.shot_attempt.lookup import attempt_table, goal_stub  # noqa: E402
from nhl_sim.shot_attempt.tables import SC_NAMES, ST_NAMES  # noqa: E402

RES = Path("results/shot_attempt_r1")
FROZEN = Path("docs/models/shot_attempt/sa_r1_frozen_params.json")
TEST, LAST_TRAIN = 20242025, 20232024
NB, BSEED = 1000, 20261015


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


ROUND = dict(TV="v1", LEVEL=None)
S1_LABEL = {"r3": "H3'' + T1 (D15)", "r3c": "H3''c + T1 (SS-R3c)", "r3t2": "H3'' + T2 (SS-R5 ruling; merged T2 flag)"}


def stage1_tables_t2():
    """H3'' + T2 from the SS-R5 cache (lam_H3_fold2.npy, types_T2_fold2.npy), read-only; same game order and stub /
    coincidental tables as run_strength_state_g1_v5.build_tables."""
    from nhl_sim.strength_state import lookup as LK
    r5, r1 = Path("results/strength_state_r5"), Path("results/strength_state_r1")
    rows = pd.read_parquet("results/strength_state_r3/fold2_rows.parquet", columns=["game_id"])
    games = np.sort(rows.game_id.unique())
    lam = np.load(r5 / "lam_H3_fold2.npy", mmap_mode="r")
    types = np.load(r5 / "types_T2_fold2.npy")
    if lam.shape[0] != len(games) or types.shape[:2] != (len(games), 2):
        raise ValueError("stage-1 cache does not match the fold-2 game list")
    smp, pim = LK.coinc_table(LAST_TRAIN)
    stub = json.loads((r1 / f"stub_tables_{LAST_TRAIN}.json").read_text())
    return dict(lam=lam, types=types, coinc_smp=smp, coinc_pim=pim, goal_rate=np.asarray(stub["goal_rate"]),
                stop_rate_ot=float(stub["stop_rate_ot"])), games, stub


def stage1_tables(stage1="r3"):
    if stage1 == "r3t2":
        return stage1_tables_t2()
    spec = importlib.util.spec_from_file_location("g1v3", ROOT / "scripts" / "run_strength_state_g1_v3.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if stage1 == "r3c":
        mod.RES = Path("results/strength_state_r3c")
    return mod.build_tables("H3", "T1")


def arm_level(arm):
    if ROUND["LEVEL"] is None:
        return "r3"
    if ROUND["LEVEL"] == "sa_r3":
        return "lc1s" if arm == "A3g-s" else "lc1g"
    return "lc1g" if arm.endswith("g") else "lc1"


def load_arm(arm):
    if arm.endswith("-c"):
        m = json.loads((RES / "models" / f"{arm}.json").read_text())
        return {"base": load_arm(m["base_model"].rsplit(".", 1)[0]), "cell": m["cell"]}
    if arm.startswith("A3"):
        import lightgbm as lgb
        return lgb.Booster(model_file=str(RES / "models" / f"{arm}.txt"))
    return json.loads((RES / "models" / f"{arm}.json").read_text())


def cmd_sim(a):
    out = Path("results") / a.tag
    out.mkdir(parents=True, exist_ok=True)
    print(now(), "start", a.tag, a.seed0, a.nseeds, flush=True)
    tables, games, _ = stage1_tables(a.stage1)
    fz = json.loads(FROZEN.read_text())
    gdf = pd.DataFrame({"game_id": games, "season": TEST})
    t0 = time.time()
    cache = RES / f"att_lam_{a.arm}_fold2.npy"       # SA-R3: the attempt table is built once and shared by blocks
    if a.round == "SA-R3" and cache.exists():
        tables["att_lam"] = np.load(cache)
    else:
        tables["att_lam"] = attempt_table(a.arm, load_arm(a.arm), gdf, fz, fold=2, tv=ROUND["TV"],
                                          level=arm_level(a.arm))
        if a.round == "SA-R3":
            np.save(cache, tables["att_lam"])
    tables["p_goal"] = goal_stub(LAST_TRAIN)
    print(now(), f"attempt table {tables['att_lam'].shape} ({time.time() - t0:.0f}s); p_goal {np.round(tables['p_goal'], 4)}",
          flush=True)
    gt = load_games([TEST], columns=["game_id", "game_type"]).set_index("game_id").loc[games]
    parts = []
    for s0 in range(a.seed0, a.seed0 + a.nseeds, a.chunk):
        t1 = time.time()
        n = min(a.chunk, a.seed0 + a.nseeds - s0)
        o = simulate(tables, games, gt.game_type.to_numpy(), n, era_for_season(TEST), seed0=s0,
                     per_team_types=(a.stage1 == "r3t2"))
        es = np.array(["", "REG", "OT", "SO"])[o["end_state"]]
        if (es == "").any():
            raise RuntimeError("unfinished sims")
        d = pd.DataFrame({"game_id": games[o["game_idx"]], "seed": o["seed"].astype(np.int32),
                          "home_goals": o["score"][:, 0], "away_goals": o["score"][:, 1], "end_state": es,
                          "home_win": np.where(es == "SO", o["so_home_win"], o["score"][:, 0] > o["score"][:, 1]),
                          "played_s": o["played_s"]})
        for p, ti in (("h", 0), ("a", 1)):
            for k in range(5):
                d[f"att_{p}_st{k}"] = o["att_st"][:, ti, k]
            for k in range(7):
                d[f"att_{p}_sc{k}"] = o["att_sc"][:, ti, k]
        for s_ in range(5):
            for c in range(7):
                d[f"toi_{s_}_{c}"] = o["toi_st_sc"][:, s_, c]
        parts.append(d)
        print(now(), f"seeds {s0}-{s0 + n - 1}: {time.time() - t1:.0f}s", flush=True)
    pd.concat(parts, ignore_index=True).to_parquet(out / f"part_{a.seed0:04d}.parquet", index=False)
    (out / f"meta_{a.seed0:04d}.json").write_text(json.dumps(dict(
        arm=a.arm, round=a.round, stage1=S1_LABEL[a.stage1], goals=f"STUB: league goals per attempt by strength state, {LAST_TRAIN}",
        p_goal=tables["p_goal"].tolist(), goalie_pull="none (EN unreachable)", shootout="skipped",
        fold=2, season=TEST, sealed_touched=False, seed0=a.seed0, nseeds=a.nseeds)))
    print(now(), "done", flush=True)


# --------------------------------------------------------------------------- grading
def offline(arm):
    rows = pd.read_parquet(RES / "fold2_rows.parquet")
    lab = json.loads((RES / "labels_sealed.json").read_text())
    return rows, np.load(RES / f"fold2_haz_{lab[arm]}.npy")


def decompose(rows, mu, sim, real, tol_rel):
    """D14-style split of sim - actual attempts per team-game, and of per-60 by state (see the report text)."""
    ntg = len(real["game_id"])
    st, sc = rows.st.to_numpy(), rows.sc.to_numpy()
    reach = st <= 4
    eh = rows.exposure_s.to_numpy() / 3600.0
    y = rows.y.to_numpy()
    E_pred, E_ar, E_ao = mu[reach].sum() / ntg, y[reach].sum() / ntg, y[~reach].sum() / ntg
    A_a = marg_total(real).mean()
    A_s = marg_total(sim).mean()
    lam_st = np.array([mu[reach & (st == k)].sum() / max(eh[reach & (st == k)].sum(), 1e-9) for k in range(5)])
    lam_sc = np.array([mu[reach & (sc == c)].sum() / max(eh[reach & (sc == c)].sum(), 1e-9) for c in range(7)])
    lam_bar = mu[reach].sum() / eh[reach].sum()
    Ts_st = sim["T"].sum(2)[:, :5].mean(0) / 3600
    Ta_st = real["T"].sum(2)[:, :5].mean(0) / 3600
    Ts_sc = sim["T"][:, :5].sum(1).mean(0) / 3600
    Ta_sc = real["T"][:, :5].sum(1).mean(0) / 3600
    b = float(((Ts_st - Ta_st) * lam_st).sum())
    s_ = float(((Ts_sc - Ta_sc) * (lam_sc - lam_bar)).sum())
    comp = {"(a) hazard level, reachable states (offline pred - actual)": E_pred - E_ar,
            "(a') actual EN-state attempts (unreachable in the sim)": -E_ao,
            "(b) strength-state visits x offline rate": b,
            "(s) score-state visits x (bucket rate - mean rate)": s_,
            "(d) remainder (sim-path hazard mix: clock / joint state)": (A_s - E_pred) - b - s_}
    tot = A_s - A_a
    assert abs(sum(comp.values()) - tot) < 1e-6 * max(1, abs(tot))
    tol = tol_rel * A_a
    over = [(k, v) for k, v in comp.items() if abs(v) > tol]
    comp_flag = any(any(np.sign(v2) == -np.sign(v) and v2 != 0 for k2, v2 in comp.items() if k2 != k) for k, v in over)
    verdict = "FAIL" if abs(tot) > tol else ("COMPENSATED" if comp_flag else "CLEAN")
    # per 60 by state: hazard level within the state + within-state score mix + remainder
    per = []
    for k in range(5):
        Ta, Tsim = real["T"][:, k].sum(0), sim["T"][:, k].sum(0)        # seconds by bucket
        Ra = marginals_st(real)[:, k].sum() / Ta.sum() * 3600
        Rs = marginals_st(sim)[:, k].sum() / Tsim.sum() * 3600
        lam = lam_st[k]
        lsc = np.array([mu[(st == k) & (sc == c)].sum() / max(eh[(st == k) & (sc == c)].sum(), 1e-9) for c in range(7)])
        mix = float(((Tsim / Tsim.sum() - Ta / Ta.sum()) * lsc).sum())
        c3 = {"hazard level": lam - Ra, "score mix within state": mix, "remainder": Rs - lam - mix}
        t3 = Rs - Ra
        tl = tol_rel * Ra
        o3 = [(kk, v) for kk, v in c3.items() if abs(v) > tl]
        cf = any(any(np.sign(v2) == -np.sign(v) and v2 != 0 for k2, v2 in c3.items() if k2 != kk) for kk, v in o3)
        per.append(dict(state=ST_NAMES[k], actual=Ra, sim=Rs, total=t3, **c3, tol=tl,
                        verdict="FAIL" if abs(t3) > tl else ("COMPENSATED" if cf else "CLEAN")))
    ev = dict(A_a=A_a, A_s=A_s, E_pred_reach=E_pred, E_a_reach=E_ar, E_a_en=E_ao, total=tot, tol=tol, verdict=verdict)
    return comp, ev, pd.DataFrame(per).set_index("state")


def marg_total(d):
    return G2.marginals(d)[0].sum(1)


def marginals_st(d):
    return G2.marginals(d)[0]


def responsiveness(rows, sim, real):
    """Closed-loop 5v5 spread ratio by own ES-for / opponent ES-against rating quintile (team-games)."""
    tg = rows.groupby(["game_id", "team"]).agg(own=("own_rf_es", "first"), opp=("opp_ra_es", "first")).reset_index()
    def per_tg(d):
        a5 = marginals_st(d)[:, 0]
        t5 = d["T"][:, 0].sum(1)
        f = pd.DataFrame({"game_id": d["game_id"], "team": d["team"], "a": a5, "t": t5})
        return f.groupby(["game_id", "team"]).mean()
    j = tg.join(per_tg(sim).add_suffix("_sim"), on=["game_id", "team"]).join(per_tg(real).add_suffix("_act"),
                                                                            on=["game_id", "team"])
    games = np.sort(j.game_id.unique())
    gp = np.searchsorted(games, j.game_id.to_numpy())
    G = len(games)
    cnt = np.random.default_rng(BSEED).multinomial(G, np.full(G, 1.0 / G), size=NB).astype(float)
    out = {}
    for c in ("own", "opp"):
        q = pd.qcut(j[c].rank(method="first"), 5, labels=False).to_numpy()
        M = {}
        for v in ("a_sim", "t_sim", "a_act", "t_act"):
            X = np.zeros((G, 5))
            np.add.at(X, (gp, q), j[v].to_numpy())
            M[v] = X
        def ratio(W):
            s = (W @ M["a_sim"]) / (W @ M["t_sim"]) * 3600
            r = (W @ M["a_act"]) / (W @ M["t_act"]) * 3600
            return (s[..., 4] - s[..., 0]) / (r[..., 4] - r[..., 0]), s, r
        rt, s, r = ratio(np.ones(G))
        br, _, _ = ratio(cnt)
        lo, hi = np.percentile(br, [2.5, 97.5])
        out[c] = dict(ratio=float(rt), ci=(float(lo), float(hi)), status="PASS" if 0.8 <= rt <= 1.2 else "FAIL",
                      table=pd.DataFrame({"sim_per60": s, "actual_per60": r,
                                          "n_team_games": np.bincount(q, minlength=5)}, index=range(1, 6)))
    return out


def cmd_grade(a):
    out = Path("results") / a.tag
    s = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("part_*.parquet"))], ignore_index=True)
    gt = load_games([TEST], columns=["game_id", "game_type", "home_id", "away_id"])
    s = s.merge(gt[["game_id", "game_type"]], on="game_id")
    nseed = s.seed.nunique()
    g = s[["game_id", "seed", "home_goals", "away_goals", "end_state", "home_win"]].assign(
        home_en_goals=np.int16(0), away_en_goals=np.int16(0))
    g.to_parquet(out / "games.parquet", index=False)     # sim_output_schema.md (stub goals; G5-G9 not meaningful)
    metas = [json.loads(p.read_text()) for p in sorted(out.glob("meta_*.json"))]
    (out / "run_meta.json").write_text(json.dumps({**metas[0], "n_seeds": int(nseed), "seed0": 0,
                                                   "engine_tag": "event_engine_stage3_sa_r1"}, indent=1))
    tol = yaml.safe_load(Path("docs/gates.yaml").read_text())
    rel, min_n = float(tol["g2_rate_rel"]), int(tol["min_cell_n"])
    rows, mu = offline(a.arm)
    rows_all = S.load_rows([TEST])
    R = G2.real_team_arrays(rows_all)
    Sm = G2.sim_team_arrays(s)
    L = [f"# G2 closed loop ({a.round}): {a.tag}, arm {a.arm}, fold 2 (2024-25), {s.game_id.nunique()} games x {nseed} seeds", "",
         f"Generated {now()} by `scripts/run_shot_attempt_g2.py`. Stage 1 = {S1_LABEL[a.stage1]}; attempts from {a.arm}; "
         "goals from a LABELLED STUB (league goals per attempt by strength state, 2023-24; not graded); no goalie pull "
         "(EN states UNREACHABLE); shootout skipped. Tolerance `g2_rate_rel` on rate-type quantities.", ""]
    res = {}
    for nm, f in (("regular season", 2), ("playoffs", 3), ("overall", None)):
        mR = (R["game_type"] == f) if f else np.ones(len(R["game_type"]), bool)
        mS = (Sm["game_type"] == f) if f else np.ones(len(Sm["game_type"]), bool)
        rr, ss = G2.select(R, mR), G2.select(Sm, mS)
        T200 = G2.evaluate(ss, rr, rel, min_n)
        T100 = G2.evaluate(G2.select(ss, ss["seed"] < 100), rr, rel, min_n)
        T200["sim_100"], T200["status_100"] = T100.sim.to_numpy(), T100.status.to_numpy()
        T200["|200-100|"] = (T200.sim - T200.sim_100).abs()
        mrow = (rows.game_type == f).to_numpy() if f else np.ones(len(rows), bool)
        comp, ev, per = decompose(rows[mrow], mu[mrow], ss, rr, rel)
        L += [f"## {nm} (actual team-games n = {len(rr['game_id'])})", "", md(T200.set_index(["group", "cell"]), ".4f"), "",
              f"### Decomposition, attempts per team-game: actual {ev['A_a']:.3f}, sim {ev['A_s']:.3f}, sim - actual "
              f"{ev['total']:+.3f} (tolerance {ev['tol']:.3f} = g2_rate_rel x actual)", "",
              pd.Series(comp, name="attempts / team-game").to_frame().to_markdown(floatfmt="+.4f"), "",
              f"- **Verdict ({nm}, per team-game): {ev['verdict']}**", "",
              "### Decomposition, attempts per 60 by state (tolerance g2_rate_rel x actual)", "", md(per, ".4f"), ""]
        res[nm] = dict(table=T200.to_dict("records"), decomposition=comp, ev=ev, per_state=per.to_dict("index"))
    rp = responsiveness(rows, Sm, R)
    L += ["## Closed-loop responsiveness (overall, 5v5, team-game quintiles; band [0.8, 1.2])", ""]
    for c, nm in (("own", "own ES attempts-for rating"), ("opp", "opponent ES attempts-against rating")):
        L += [f"### by {nm}: spread ratio {rp[c]['ratio']:.3f} (95% CI {rp[c]['ci'][0]:.3f}..{rp[c]['ci'][1]:.3f}) "
              f"**{rp[c]['status']}**", "", md(rp[c]["table"], ".3f"), ""]
    tid_r = np.where(R["team"] == 0, gt.set_index("game_id").home_id.reindex(R["game_id"]).to_numpy(),
                     gt.set_index("game_id").away_id.reindex(R["game_id"]).to_numpy())
    tid_s = np.where(Sm["team"] == 0, gt.set_index("game_id").home_id.reindex(Sm["game_id"]).to_numpy(),
                     gt.set_index("game_id").away_id.reindex(Sm["game_id"]).to_numpy())
    PT = G2.per_team(R, tid_r).join(G2.per_team(Sm, tid_s)[["for_pg", "against_pg"]], rsuffix="_sim")
    PT["status"] = np.where(PT.n_team_games < min_n, "UNDERPOWERED", "")
    L += [f"## Per team (n = team-games, all UNDERPOWERED; corr for {np.corrcoef(PT.for_pg, PT.for_pg_sim)[0, 1]:.2f}, "
          f"against {np.corrcoef(PT.against_pg, PT.against_pg_sim)[0, 1]:.2f})", "", md(PT, ".2f"), ""]
    rep = Path(a.report or f"docs/tests/gates_g2_{a.tag}_2026-10-15.md")
    rep.write_text("\n".join(L) + "\n", encoding="utf-8")
    res["responsiveness"] = {c: dict(ratio=rp[c]["ratio"], ci=rp[c]["ci"], status=rp[c]["status"]) for c in rp}
    (out / "g2_summary.json").write_text(json.dumps(res, indent=1, default=float))
    print(now(), "wrote", rep, flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sim", "grade"])
    ap.add_argument("--arm", required=True)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--nseeds", type=int, default=50)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--report", default=None)
    ap.add_argument("--round", default="SA-R1", choices=["SA-R1", "SA-R2", "SA-R3"])
    ap.add_argument("--stage1", default="r3", choices=["r3", "r3c", "r3t2"])
    a = ap.parse_args()
    if a.round == "SA-R2":
        RES = Path("results/shot_attempt_r2")
        FROZEN = Path("docs/models/shot_attempt/sa_r2_frozen_params.json")
        ROUND.update(TV="v2", LEVEL="lc1")
    if a.round == "SA-R3":
        RES = Path("results/shot_attempt_r3")
        FROZEN = Path("docs/models/shot_attempt/sa_r3_frozen_params.json")
        ROUND.update(TV="v2", LEVEL="sa_r3")
    a.tag = a.tag or (f"sa_r1_g2_{a.arm}" if a.round == "SA-R1" else f"sa_r2_g2_{a.arm}_{a.stage1}")
    {"sim": cmd_sim, "grade": cmd_grade}[a.cmd](a)
