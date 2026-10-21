"""EG-R1 part A step 1 (Lane H8a, INV-66): pull detection (the step-0 audit rule), engine-rule episodes, hazard rows and
the per-team-game paths, per season; plus the step-0 table (per-season first-pull medians by deficit, pulled time per
game). Seasons are passed explicitly; the 2024-25 build is run only at the fold-2 selection step.

    build_end_game_pull_rows_v1.py build --seasons 20212022 20222023 20232024
    build_end_game_pull_rows_v1.py step0 --seasons 20212022 20222023 20232024   -> docs/tests/end_game_eg_r1_pull_step0_2026-10-21.md
"""
import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from nhl_sim.data.load import load_events, load_games, load_shifts  # noqa: E402
from nhl_sim.end_game import pull as PL  # noqa: E402

OUT = ROOT / "data" / "processed" / "end_game"
SLAB = {20212022: "2021-22", 20222023: "2022-23", 20232024: "2023-24", 20242025: "2024-25"}


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S %z")


def build(season):
    t0 = time.time()
    G = load_games([season])
    EV = load_events([season], columns=PL.EV_COLS)
    SH = load_shifts([season])
    SH = SH[SH.position == "G"]
    P = PL.detect_pulls(G, EV, SH)
    has = set(map(tuple, SH[["game_id", "team_id"]].drop_duplicates().to_numpy().tolist()))
    rows, ep, paths = PL.episodes_and_rows(G, EV, P, has)
    OUT.mkdir(parents=True, exist_ok=True)
    P.to_parquet(OUT / f"pulls_v1_{season}.parquet", index=False)
    rows.to_parquet(OUT / f"pull_rows_v1_{season}.parquet", index=False)
    ep.to_parquet(OUT / f"pull_episodes_v1_{season}.parquet", index=False)
    paths.to_parquet(OUT / f"pull_paths_v1_{season}.parquet", index=False)
    rs = G[G.game_type == 2]
    n_tg = 2 * len(rs)
    print(now(), f"{season}: {len(P):,} pulls, {len(rows):,} rows ({int(rows.y.sum()):,} y), {len(ep):,} episodes, "
          f"{len(paths):,} of {n_tg:,} RS team-games with goalie shifts, {time.time() - t0:.0f}s", flush=True)


def step0(seasons, out_md):
    L = ["# EG-R1 part A step 0 (Lane H8a, INV-66): pull rows and the level question, training seasons only", "",
         f"Generated {now()} by `scripts/build_end_game_pull_rows_v1.py step0`. Regular season. Training seasons only "
         "(2021-22, 2022-23, 2023-24); nothing from 2024-25 is read. Committed before any fit.", "",
         "Definitions: `src/nhl_sim/end_game/pull.py` module doc and the Lane H8a execution note in "
         "`docs/models/end_game/experiments.md`. Engine-rule episode = non-DP pull start while trailing in the last 600 s, "
         "until the first goal against / tying goal / end of regulation. Literal = shift-chart non-DP goalie-out seconds in "
         "the window. Bridged = engine-rule out seconds that are goalie-in on the shift chart (a non-goal return).", ""]
    T, F, X = [], [], []
    for s in seasons:
        rows = pd.read_parquet(OUT / f"pull_rows_v1_{s}.parquet")
        ep = pd.read_parquet(OUT / f"pull_episodes_v1_{s}.parquet")
        pa = pd.read_parquet(OUT / f"pull_paths_v1_{s}.parquet")
        P = pd.read_parquet(OUT / f"pulls_v1_{s}.parquet")
        ng = pa.game_id.nunique()
        allp = P[(P.game_type == 2)]
        p3 = allp[(allp.period == 3)]
        win_all = np.clip(p3.end, PL.WIN0, PL.WIN1) - np.clip(p3.start, PL.WIN0, PL.WIN1)
        T.append(dict(season=SLAB[s], games=ng, team_games=len(pa), rows=len(rows), pulls_y=int(rows.y.sum()),
                      episodes=len(ep), first_episodes=int((~ep.pulled_before).sum()), repulls=int(ep.pulled_before.sum()),
                      engine_rule_s_per_game=pa.out_engine.sum() / ng, literal_nonDP_window_s_per_game=pa.out_literal.sum() / ng,
                      bridged_s_per_game=pa.bridged.sum() / ng, literal_outside_episode_s_per_game=pa.literal_outside.sum() / ng,
                      all_shift_pulls_window_incl_DP_s_per_game=float(win_all.sum()) / ng,
                      all_shift_pulls_game_incl_DP_s_per_game=float(allp.dur.sum()) / ng))
        first = ep[~ep.pulled_before].copy()
        first["rem"] = PL.WIN1 - first.start
        for d, x in first.groupby(np.minimum(first.deficit, 3)):
            F.append(dict(season=SLAB[s], deficit={1: "trail1", 2: "trail2", 3: "trail3+"}[int(d)], n=len(x),
                          flag="UNDERPOWERED" if len(x) < 100 else "", p10=x.rem.quantile(.1), p25=x.rem.quantile(.25),
                          median=x.rem.median(), p75=x.rem.quantile(.75), p90=x.rem.quantile(.9)))
        ga = ep[ep.cause == "goal_against"]
        nxt = ep.sort_values("start").groupby(["game_id", "team_id"]).start.shift(-1)
        rep = nxt.reindex(ga.index).notna()
        X.append(dict(season=SLAB[s], episodes_ended_by_goal_against=len(ga), repull_share=float(rep.mean()),
                      ended_tie=int((ep.cause == "tie").sum()), ended_period_end=int((ep.cause == "period_end").sum()),
                      first_cause_stoppage=int((ep.first_cause == "stoppage").sum()),
                      first_cause_goal_for=int((ep.first_cause == "goal_for").sum()),
                      first_cause_in_play=int((ep.first_cause == "in_play").sum()),
                      share_eps_with_pen_pk=float((ep.pen == 1).mean()), share_eps_with_pen_pp=float((ep.pen == 2).mean())))
    L += ["## Rows and pulled time per game (seconds, both teams, regular season)", "", pd.DataFrame(T).to_markdown(index=False, floatfmt=".2f"), "",
          "`all_shift_pulls_game_incl_DP` is the audit's 'pulled time per game, all pulls' (table 1h, any period); the "
          "window column restricts it to the last 600 s of P3.", "",
          "## First-pull seconds left by deficit at the start (engine-rule first episode per team-game)", "",
          pd.DataFrame(F).to_markdown(index=False, floatfmt=".1f"), "",
          "## Episode ends and re-pulls", "", pd.DataFrame(X).to_markdown(index=False, floatfmt=".3f"), "",
          "`first_cause_*` = how the first shift gap of the episode ended on the shift chart (a non-goal return is bridged).", "",
          "## Level question (L27)", "",
          "Per-season pulled time per game and first-pull medians above: the spec carries no level in EG-R1; a fold-2 pulled-time "
          "miss > 10% makes a level EG-R2's first item. Whether the training seasons show a trend is read from the table above.", ""]
    Path(out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", out_md)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "step0"])
    ap.add_argument("--seasons", type=int, nargs="+", required=True)
    ap.add_argument("--out", default="docs/tests/end_game_eg_r1_pull_step0_2026-10-21.md")
    a = ap.parse_args()
    print(now(), "start", a.cmd, a.seasons, flush=True)
    if a.cmd == "build":
        for s in a.seasons:
            build(s)
    else:
        step0(a.seasons, a.out)
