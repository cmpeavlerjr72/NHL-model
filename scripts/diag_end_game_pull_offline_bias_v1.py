"""EG-R1 part A diagnostic (Lane H8a): is the offline pulled-time check biased by construction? Replays the ACTUAL
episode start times of a season, each shifted by a random offset N(0, sigma), through the same offline machinery
(actual score path, actual goal seconds as the only returns). sigma = 0 must reproduce the actual pulled time exactly;
any excess at sigma > 0 is what a process with the right timing distribution but its own randomness gets from the
endogeneity of the return goals (the goals against an empty net happen when the REAL goalie is out).

    diag_end_game_pull_offline_bias_v1.py --season 20232024

Second part (in-sample calibration): P0 and P1 fitted on the season itself (P0 then reproduces the season's per-second
row hazard exactly) run through PL.simulate_offline on the same season's paths: the offline check's own bias.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from nhl_sim.end_game import pull as PL  # noqa: E402

DATA = ROOT / "data" / "processed" / "end_game"


def replay(paths, ep, sigma, reps, rng):
    dfc, dp, ret = (PL.unpack(paths, c) for c in ("deficit", "dp", "ret"))
    E = {k: np.sort(d.start.to_numpy()) for k, d in ep.groupby(["game_id", "team_id"])}
    tot = 0
    for r in range(reps):
        for i, (g, t) in enumerate(zip(paths.game_id, paths.team_id)):
            st = E.get((g, t))
            if st is None:
                continue
            intent = np.sort(st + (np.round(rng.normal(0, sigma, len(st))) if sigma > 0 else 0))
            out, k = False, 0
            for j in range(PL.NSEC):
                s = PL.WIN0 + j
                if not out:
                    while k < len(intent) and intent[k] <= s and not (dfc[i, j] >= 1 and dp[i, j] == 0):
                        if intent[k] < s - 0:              # intent passed while not eligible: wait for eligibility
                            break
                        k += 1
                    if k < len(intent) and intent[k] <= s and dfc[i, j] >= 1 and dp[i, j] == 0:
                        out, k = True, k + 1
                else:
                    while k < len(intent) and intent[k] <= s:  # intents while out are absorbed
                        k += 1
                if out:
                    tot += 1
                    if ret[i, j]:
                        out = False
    return tot / reps / paths.game_id.nunique()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=20232024)
    ap.add_argument("--reps", type=int, default=5)
    a = ap.parse_args()
    if a.season == 20242025:
        raise SystemExit("training seasons only")
    paths = pd.read_parquet(DATA / f"pull_paths_v1_{a.season}.parquet")
    ep = pd.read_parquet(DATA / f"pull_episodes_v1_{a.season}.parquet")
    rng = np.random.default_rng(0)
    act = paths.out_engine.sum() / paths.game_id.nunique()
    res = dict(season=a.season, actual_engine_rule_s_per_game=float(act))
    for sg in (0, 5, 10, 20, 30):
        v = replay(paths, ep, sg, 1 if sg == 0 else a.reps, rng)
        res[f"sigma_{sg}"] = dict(s_per_game=float(v), ratio=float(v / act))
        print(sg, round(v, 2), round(v / act, 4), flush=True)
    rows = pd.read_parquet(DATA / f"pull_rows_v1_{a.season}.parquet")
    act_s = PL.actual_stats(paths, ep)
    res["actual"] = act_s
    for nm, m in (("P0_in_sample", PL.fit_p0(rows)), ("P1_in_sample", PL.fit_p1(rows))):
        sim = PL.simulate_offline(m, paths, reps=100, seed=1)
        res[nm] = dict(sim=sim, pulled_ratio=sim["pulled_s_per_game"] / act_s["pulled_s_per_game"],
                       trail1_share_pp=100 * (sim["share_trail1_pulled"] - act_s["share_trail1_pulled"]),
                       checks=PL.bias_checks(sim, act_s))
        print(nm, json.dumps(res[nm]), flush=True)
    print(json.dumps(res))
    (ROOT / "results" / "end_game_pull_v1" / f"diag_offline_bias_{a.season}.json").write_text(json.dumps(res, indent=1))
