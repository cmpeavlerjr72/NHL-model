"""G1 (strength-state TOI, PP opportunities, penalty minutes, minors ended by a PP goal).

One summary function serves real and sim, from a per-(game, seed) frame with the strength_toi.parquet columns
(docs/ops/sim_output_schema.md). Real per-game values come from the mechanics replay of the real penalty / goal /
stoppage sequence (step-2 agreement 99.99% gap-aware) with the same `Recorder` the sim uses, so TOI is
penalty-derived strength (a pulled goalie does not create a state; EN time is reported separately from pbp).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.engine.sim import TOI_COLS, Recorder

PPO_K = list(range(8))   # 0..6, 7 = 7+
STUB_DEPENDENT = {
    "TOI 3v3 (min/game)": "3v3 time is regular-season OT; OT frequency comes from the stub goals",
    "share of minors ended by PP goal": "PP-goal frequency is the stub goal rate (league, no team terms)",
    "TOI EN (min/game)": "no goalie-pull model yet (stage 8)",
}
PARTLY_STUB = {"TOI 5v5 (min/game)", "TOI PP total (min/game)", "TOI 5v3/3v5 (min/game)", "TOI 4v4 (min/game)"}


def real_frame(season: int) -> pd.DataFrame:
    from nhl_sim.data.load import load_events, load_games
    from nhl_sim.strength_state.timeline import EV_COLS, season_timeline
    ev = load_events([season], columns=EV_COLS)
    tl = season_timeline(ev)
    games, sk, prev = tl["games"], tl["sk"], tl["prev"]
    N, T = sk.shape[:2]
    end = games.end_t.to_numpy()
    rec = Recorder(N)
    for t in range(T):
        idx = np.nonzero(t < end)[0]
        rec.record(idx, sk[idx, t])
    played = np.arange(T)[None, :] < end[:, None]
    en_s = (played & ((prev[..., 0] == 0) | (prev[..., 3] == 0))).sum(1)
    tg = tl["targets"]
    pen = tg.groupby(["game_id", "team"]).size().unstack(fill_value=0).reindex(games.game_id, fill_value=0)
    pim = tg[~((tg.cls == "coincidental") & (tg.team == 1))].groupby("game_id").pim.sum().reindex(games.game_id,
                                                                                                    fill_value=0)
    out = pd.DataFrame({"game_id": games.game_id.to_numpy(), "seed": 0})
    for i, c in enumerate(TOI_COLS):
        out[c] = rec.toi[:, i]
    out["toi_en_s"] = en_s
    out["played_s"] = rec.played
    out["ppo_home"], out["ppo_away"] = rec.ppo[:, 0], rec.ppo[:, 1]
    out["pen_home"], out["pen_away"] = pen.get(0, 0).to_numpy(), pen.get(1, 0).to_numpy()
    out["pim"] = pim.to_numpy()
    out["minors_home"], out["minors_away"] = tl["n_minor"][:, 0], tl["n_minor"][:, 1]
    out["minors_pp_ended_home"], out["minors_pp_ended_away"] = tl["n_minor_pp_ended"][:, 0], tl["n_minor_pp_ended"][:, 1]
    g = load_games([season], columns=["game_id", "game_type", "home_id", "away_id"])
    return out.merge(g[["game_id", "game_type", "home_id", "away_id"]], on="game_id", how="left")


def summarize(df: pd.DataFrame) -> dict:
    r = {}
    m = 60.0
    r["TOI 5v5 (min/game)"] = df.toi_5v5_s.mean() / m
    r["TOI PP total (min/game)"] = (df.toi_pp_home_s + df.toi_pp_away_s).mean() / m
    r["TOI PP home (min/game)"] = df.toi_pp_home_s.mean() / m
    r["TOI PP away (min/game)"] = df.toi_pp_away_s.mean() / m
    r["TOI 4v4 (min/game)"] = df.toi_4v4_s.mean() / m
    r["TOI 3v3 (min/game)"] = df.toi_3v3_s.mean() / m
    r["TOI 5v3/3v5 (min/game)"] = df.toi_5v3_s.mean() / m
    r["TOI EN (min/game)"] = df.toi_en_s.mean() / m if "toi_en_s" in df.columns else 0.0
    ppo = np.concatenate([df.ppo_home.to_numpy(), df.ppo_away.to_numpy()]).astype(float)
    r["PP opps / team-game mean"] = ppo.mean()
    r["PP opps / team-game SD"] = ppo.std()
    for k in PPO_K:
        r[f"P(PP opps={k}{'+' if k == 7 else ''})"] = float(np.mean(np.minimum(ppo, 7) == k))
    pen = np.concatenate([df.pen_home.to_numpy(), df.pen_away.to_numpy()]).astype(float)
    r["penalty-taking events / team-game"] = pen.mean()
    r["PIM / game (strength penalties)"] = df.pim.mean()
    mn = (df.minors_home + df.minors_away).sum()
    r["share of minors ended by PP goal"] = (df.minors_pp_ended_home + df.minors_pp_ended_away).sum() / max(1, mn)
    return {k: float(v) for k, v in r.items()}


def targets_rows(real: pd.DataFrame, season: int) -> pd.DataFrame:
    rows = []
    for seg, d in (("all", real), ("RS", real[real.game_type == 2]), ("PO", real[real.game_type == 3])):
        if len(d) == 0:
            continue
        for k, v in summarize(d).items():
            rows.append(dict(season=season, segment=seg, gate="G1", metric=k, key="", value=v, n_games=len(d)))
    return pd.DataFrame(rows)


def per_team(df: pd.DataFrame) -> pd.DataFrame:
    h = pd.DataFrame({"team_id": df.home_id, "ppo": df.ppo_home, "pp_s": df.toi_pp_home_s, "pk_s": df.toi_pp_away_s,
                      "pen": df.pen_home})
    a = pd.DataFrame({"team_id": df.away_id, "ppo": df.ppo_away, "pp_s": df.toi_pp_away_s, "pk_s": df.toi_pp_home_s,
                      "pen": df.pen_away})
    x = pd.concat([h, a])
    return x.groupby("team_id").agg(ppo=("ppo", "mean"), pp_min=("pp_s", lambda s: s.mean() / 60),
                                    pk_min=("pk_s", lambda s: s.mean() / 60), pen=("pen", "mean"))


def evaluate(sim: pd.DataFrame, real: pd.DataFrame, tol: dict, n_games: int, min_n: int) -> list[dict]:
    S, R = summarize(sim), summarize(real)
    checks = []
    for k in S:
        if k.startswith("TOI"):
            t = tol["g1_toi_min"]
        elif k in ("PP opps / team-game mean", "PP opps / team-game SD"):
            t = tol["g1_pp_opps"]
        else:
            t = None
        d = S[k] - R[k]
        if t is None:
            st = "NO-TOLERANCE"
        elif n_games < min_n:
            st = "UNDERPOWERED"
        else:
            st = "PASS" if abs(d) <= t else "FAIL"
        note = ""
        if k in STUB_DEPENDENT:
            note = f"STUB-DEPENDENT: {STUB_DEPENDENT[k]} (literal {st})"
            st = "STUB-DEPENDENT"
        elif k in PARTLY_STUB:
            note = "PP minors end on stub goals: duration partly stub-driven"
        checks.append(dict(check=k, sim=S[k], real=R[k], tol="" if t is None else str(t), status=st, n=n_games,
                           note=note or f"delta={d:+.4f}"))
    return checks
