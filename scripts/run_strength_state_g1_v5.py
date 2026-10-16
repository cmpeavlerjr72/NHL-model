"""SS-R3 (Lane H4, INV-28): closed-loop G1 run for H3''/H2'' (versioned sibling of run_strength_state_g1.py; the
SS-R1 script is unchanged). Hazard lookup = `hazard_table_v3` (per-game level + profile offsets). SS-R1 docstring follows.

SS-R1 step 5: closed-loop G1 run. Wires a fitted hazard arm + type arm + rulebook mechanics + LABELLED STUB goals
into the GameState engine over fold-2 (2024-25) games and writes results/<tag>/ per docs/ops/sim_output_schema.md
(games.parquet with stub goals, strength_toi.parquet, run_meta.json), then grades G1 (seeds 0-99 vs 0-199).

    run_strength_state_g1.py --arm H3 --type-arm T1 --seeds 200 [--tag ss_r1_g1_H3] [--chunk 50]
"""
import argparse
import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_games, load_reference  # noqa: E402
from nhl_sim.engine.rules import era_for_season  # noqa: E402
from nhl_sim.engine.sim_ss_r5 import TOI_COLS, simulate  # noqa: E402   (SS-R5 variant: per-team type table)
from nhl_sim.eval import g1 as G1  # noqa: E402
from nhl_sim.strength_state import lookup as LK  # noqa: E402
from nhl_sim.strength_state import models_r5 as R5  # noqa: E402
from concurrent.futures import ProcessPoolExecutor  # noqa: E402

RES = Path("results/strength_state_r3")
R5D = Path("results/strength_state_r5")
R1 = Path("results/strength_state_r1")
TEST, LAST_TRAIN = 20242025, 20232024


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def load_model(arm):
    if arm.startswith("H3"):
        return lgb.Booster(model_file=str(RES / "models" / f"{arm}_fold2.txt"))
    return json.loads((RES / "models" / f"{arm}_fold2.json").read_text())


def build_tables(arm, type_arm):
    R5D.mkdir(parents=True, exist_ok=True)
    rows = pd.read_parquet(RES / "fold2_rows.parquet")
    tr = rows.groupby(["game_id", "team"]).agg(season=("season", "first"), taken_own=("taken_own", "first"),
                                               drawn_opp=("drawn_opp", "first"), is_home=("is_home", "first"),
                                               b2b_own=("b2b_own", "first"), b2b_opp=("b2b_opp", "first"),
                                               level=("level", "first")).reset_index()
    tr["season_f"] = np.minimum(tr.season, LAST_TRAIN)
    t0 = time.time()
    R5D.mkdir(parents=True, exist_ok=True)
    lam_path = R5D / f"lam_{arm}_fold2.npy"      # cached: the hazard table is independent of the type arm
    if lam_path.exists():
        lam = np.load(lam_path, mmap_mode="r")
    else:
        lam = LK.hazard_table_v3(arm, load_model(arm), tr)
        np.save(lam_path, lam)
    print(now(), f"hazard table {lam.shape} ({time.time() - t0:.0f}s)", flush=True)
    tm = json.loads((R5D / f"{type_arm}_fold2.json").read_text())
    types = R5.team_type_table(tm, tr, tm["k_off"], LAST_TRAIN)
    np.save(R5D / f"types_{type_arm}_fold2.npy", types)
    smp, pim = LK.coinc_table(LAST_TRAIN)
    stub_path = R1 / f"stub_tables_{LAST_TRAIN}.json"
    if stub_path.exists():
        stub = json.loads(stub_path.read_text())
    else:
        st = LK.stub_tables(LAST_TRAIN)
        stub = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in st.items()}
        stub_path.write_text(json.dumps(stub, indent=1))
    games = np.sort(tr.game_id.unique())
    return dict(lam=lam, types=types, coinc_smp=smp, coinc_pim=pim, goal_rate=np.asarray(stub["goal_rate"]),
                stop_rate_ot=float(stub["stop_rate_ot"])), games, stub


_W = {}


def _init(tables, games, gtypes, era):
    _W.update(tables=tables, games=games, gtypes=gtypes, era=era)


def _work(job):
    s0, ns = job
    t0 = time.time()
    o = simulate(_W["tables"], _W["games"], _W["gtypes"], ns, _W["era"], seed0=s0)
    return o, time.time() - t0


def to_frames(out, games):
    gid = games[out["game_idx"]]
    es = np.array(["", "REG", "OT", "SO"])[out["end_state"]]
    if (es == "").any():
        raise RuntimeError(f"{int((es == '').sum())} sims did not finish")
    hg, ag = out["score"][:, 0], out["score"][:, 1]
    hw = np.where(es == "SO", out["so_home_win"], hg > ag)
    g = pd.DataFrame({"game_id": gid, "seed": out["seed"].astype(np.int32), "home_goals": hg.astype(np.int16),
                      "away_goals": ag.astype(np.int16), "end_state": es, "home_win": hw.astype(bool)})
    s = pd.DataFrame({"game_id": gid, "seed": out["seed"].astype(np.int32)})
    for i, c in enumerate(TOI_COLS):
        s[c] = out["toi"][:, i]
    s["toi_en_s"] = 0
    s["played_s"] = out["played_s"]
    s["ppo_home"], s["ppo_away"] = out["ppo"][:, 0], out["ppo"][:, 1]
    s["pen_home"], s["pen_away"] = out["pen_count"][:, 0], out["pen_count"][:, 1]
    s["pim"] = out["pim"]
    for j, c in enumerate(("minor", "double", "major", "coinc")):
        s[f"n_{c}_home"], s[f"n_{c}_away"] = out["n_type"][:, 0, j], out["n_type"][:, 1, j]
    s["minors_home"], s["minors_away"] = out["n_minor"][:, 0], out["n_minor"][:, 1]
    s["minors_pp_ended_home"], s["minors_pp_ended_away"] = out["n_minor_pp_ended"][:, 0], out["n_minor_pp_ended"][:, 1]
    s["coinc_4v4"] = out["coinc_4v4"]
    return g, s


def md(df, fmt=".4f"):
    return df.to_markdown(floatfmt=fmt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="H3")
    ap.add_argument("--type-arm", default="T1")
    ap.add_argument("--seeds", type=int, default=200)
    ap.add_argument("--chunk", type=int, default=50)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    tag = a.tag or f"ss_r5_g1_{a.arm}_{a.type_arm}"
    out_dir = Path("results") / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    print(now(), "start", tag, flush=True)
    tables, games, stub = build_tables(a.arm, a.type_arm)
    gt = load_games([TEST], columns=["game_id", "game_type", "home_id", "away_id"]).set_index("game_id").loc[games]
    era = era_for_season(TEST)
    G_parts, S_parts, timing = [], [], []
    jobs = [(s0, min(a.chunk, a.seeds - s0)) for s0 in range(0, a.seeds, a.chunk)]
    with ProcessPoolExecutor(max_workers=a.workers, initializer=_init, initargs=(tables, games, gt.game_type.to_numpy(),
                                                                                 era)) as ex:
        for (s0, ns), (o, dt) in zip(jobs, ex.map(_work, jobs)):    # chunks are independent (RNG keyed on seed, game)
            g, s = to_frames(o, games)
            G_parts.append(g)
            S_parts.append(s)
            timing.append(dt)
            print(now(), f"seeds {s0}-{s0 + ns - 1}: {dt:.0f}s, unfinished {o['unfinished']}", flush=True)
    g = pd.concat(G_parts, ignore_index=True)
    s = pd.concat(S_parts, ignore_index=True)
    g["home_en_goals"] = np.int16(0)
    g["away_en_goals"] = np.int16(0)
    g.to_parquet(out_dir / "games.parquet", index=False)
    s.to_parquet(out_dir / "strength_toi.parquet", index=False)
    meta = dict(engine_tag="event_engine_stage1_ssr5 (sim_ss_r5: per-team type table)", fold=2, season=TEST, n_seeds=a.seeds, sealed_touched=False,
                hazard_arm=a.arm, type_arm=a.type_arm, goals="STUB: league goal rate per skater state, 2023-24, "
                "no team terms (not graded)", goalie_pull="none (EN STUB-DEPENDENT)",
                shootout="skipped; home_win of SO rows is a 50/50 STUB", seconds_per_chunk=timing,
                goal_rate_stub_per_hour=stub["goal_rate"], stop_rate_ot_stub=stub["stop_rate_ot"])
    (out_dir / "run_meta.json").write_text(json.dumps(meta, indent=1))
    # ---- G1
    tol = yaml.safe_load(Path("docs/gates.yaml").read_text())
    tg = load_reference(f"gate_targets_{TEST}")
    g1t = tg[(tg.gate == "G1") & (tg.segment == "all")]
    real = G1.real_frame(TEST)
    R = G1.summarize(real)
    if len(g1t):
        ref = dict(zip(g1t.metric, g1t.value))
        bad = [k for k in R if abs(ref.get(k, np.nan) - R[k]) > 1e-9]
        if bad:
            raise RuntimeError(f"gate_targets G1 rows disagree with the recomputed real frame: {bad}")
    sim = s.merge(gt[["home_id", "away_id", "game_type"]].reset_index(), on="game_id")
    n = len(real)
    c200 = G1.evaluate(sim, real, tol, n, tol["min_cell_n"])
    c100 = G1.evaluate(sim[sim.seed < 100], real, tol, n, tol["min_cell_n"])
    T = pd.DataFrame(c200).set_index("check")
    T["sim_100"] = [c["sim"] for c in c100]
    T["status_100"] = [c["status"] for c in c100]
    T["seed_stability_|200-100|"] = (T.sim - T.sim_100).abs()
    pt_r, pt_s = G1.per_team(real), G1.per_team(sim)
    PT = pt_r.join(pt_s, lsuffix="_real", rsuffix="_sim")
    PT["n_team_games"] = pd.concat([real.home_id, real.away_id]).value_counts().reindex(PT.index)
    PT["status"] = np.where(PT.n_team_games < tol["min_cell_n"], "UNDERPOWERED", "")
    corr = np.corrcoef(PT.ppo_real, PT.ppo_sim)[0, 1]
    seg = []
    for nm, f in (("RS", 2), ("PO", 3)):
        rr, ss = real[real.game_type == f], sim[sim.game_type == f]
        cs = G1.evaluate(ss, rr, tol, len(rr), tol["min_cell_n"])
        c1 = G1.evaluate(ss[ss.seed < 100], rr, tol, len(rr), tol["min_cell_n"])
        d = pd.DataFrame(cs).set_index("check")[["sim", "real", "status"]]
        d["sim_100"] = [c["sim"] for c in c1]
        d["|200-100|"] = (d.sim - d.sim_100).abs()
        seg.append(d.add_suffix(f"_{nm}"))
    SEG = pd.concat(seg, axis=1)
    types = s[[c for c in s.columns if c.startswith("n_")]].sum()
    L = [f"# G1 closed loop (SS-R3 offsets + SS-R5 team-term type arm): {tag} (fold 2, 2024-25, {len(games)} games x {a.seeds} seeds)", "",
         f"Generated {now()} by `scripts/run_strength_state_g1.py`. Hazard arm {a.arm}, type arm {a.type_arm}, "
         "rulebook mechanics in GameState, goals from a LABELLED STUB (league goal rate per skater state from 2023-24, "
         "no team terms, not graded), no goalie pull, SO skipped. Real values: mechanics replay of the real 2024-25 "
         "penalty/goal/stoppage sequence (TOI is penalty-derived strength; EN time from pbp goalie state). "
         "Tolerances `docs/gates.yaml` g1_toi_min / g1_pp_opps; metrics without a g1_* tolerance are NO-TOLERANCE "
         "(reported).", "",
         f"Chunk timings (s, {a.chunk} seeds each): {[round(x) for x in timing]}", "",
         "## Overall", "", md(T[["sim", "real", "tol", "status", "note", "sim_100", "status_100",
                                 "seed_stability_|200-100|"]], ".4f"), "",
         "## By segment (RS / PO; PO is UNDERPOWERED, n < min_cell_n)", "", md(SEG, ".4f"), "",
         f"## Per team (n = team-games, every cell UNDERPOWERED; corr of PP opps per team-game sim vs real {corr:.2f})",
         "", md(PT, ".3f"), "",
         "## Sim penalty-type counts (all seeds)", "", md(types.to_frame("count")), "",
         "## Stub tables", "", f"Goal rate per hour [own skaters 3..5][opp skaters 3..5]: {np.round(stub['goal_rate'], 3).tolist()}",
         f"RS-OT whistle rate per second: {stub['stop_rate_ot']:.5f}", ""]
    rep = Path(a.report or f"docs/tests/gates_g1_{tag}_2026-10-15.md")
    rep.write_text("\n".join(L) + "\n", encoding="utf-8")
    T.to_csv(out_dir / "g1_overall.csv")
    print(now(), "wrote", rep, flush=True)
    print(T[["sim", "real", "status", "seed_stability_|200-100|"]].to_string(), flush=True)


if __name__ == "__main__":
    main()
