"""SS-R1 step 2: replay real penalty / goal / stoppage sequences of fold-1 games (2021-22 .. 2023-24) through the
GameState mechanics and compare the strength-state timeline second by second with the pbp situationCode.

    diag_strength_state_replay.py [--seasons 20212022 20222023 20232024] [--out results/strength_state_r1/replay]

Writes per-game agreement and the disagreement runs (classified) to --out; prints the summary used in the report.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from nhl_sim.data.load import load_events  # noqa: E402
from nhl_sim.strength_state.timeline import EV_COLS, agreement, season_timeline  # noqa: E402


def runs_of(mask_row):
    s = np.nonzero(mask_row)[0]
    if s.size == 0:
        return []
    return np.split(s, np.nonzero(np.diff(s) > 1)[0] + 1)


def classify_run(r, prev, nxt, sk):
    t0 = r[0]
    p, n = prev[t0], nxt[t0]
    if p[0] == 0 or p[3] == 0 or n[0] == 0 or n[3] == 0:
        return "goalie_pull_adjacent"
    if t0 >= 3600:
        return "overtime"
    psk = (p[2], p[1])
    if max(psk) > 5 or min(psk) < 3:
        return "pbp_code_anomaly"
    return "other"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="+", type=int, default=[20212022, 20222023, 20232024])
    ap.add_argument("--out", default="results/strength_state_r1/replay")
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--lazy-expiry", action="store_true",
                    help="alternative timing convention: penalties due at second s expire AFTER that second's events "
                         "(default: before; chosen on fold-1 agreement, see the SS-R1 report)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "start", flush=True)
    per_game, runs = [], []
    for s in a.seasons:
        t0 = time.time()
        ev = load_events([s], columns=EV_COLS)
        tl = season_timeline(ev, expire_first=not a.lazy_expiry)
        ag, d = agreement(tl)
        bad = d["played"] & ~d["gap"]
        g = tl["games"]
        for i in np.nonzero(bad.any(1))[0]:
            for r in runs_of(bad[i]):
                runs.append(dict(game_id=int(g.game_id[i]), season=s, t_start=int(r[0]), t_end=int(r[-1]),
                                 n_s=len(r), cls=classify_run(r, tl["prev"][i], tl["nxt"][i], tl["sk"][i]),
                                 eng_sk=tuple(int(x) for x in tl["sk"][i, r[0]]),
                                 pbp_prev=tl["prev"][i, r[0]].tolist(), pbp_next=tl["nxt"][i, r[0]].tolist()))
        per_game.append(ag)
        print(time.strftime("%H:%M:%S"), s, f"games={len(g)} replay+compare {time.time() - t0:.1f}s", flush=True)
    pg = pd.concat(per_game, ignore_index=True)
    rn = pd.DataFrame(runs)
    pg.to_parquet(out / "per_game.parquet")
    rn.to_parquet(out / "disagreement_runs.parquet") if len(rn) else None
    tot = pg[["n_s", "strict_agree_s", "gap_agree_s", "ambiguous_s", "strict_miss_unambiguous_s"]].sum()
    summ = dict(games=len(pg), seconds=int(tot.n_s), strict=float(tot.strict_agree_s / tot.n_s),
                gap_aware=float(tot.gap_agree_s / tot.n_s), ambiguous_share=float(tot.ambiguous_s / tot.n_s),
                strict_miss_share_outside_ambiguous_gaps=float(tot.strict_miss_unambiguous_s / max(1, tot.n_s - tot.strict_agree_s)))
    rng = np.random.default_rng(20261015)
    samp = pg.iloc[rng.choice(len(pg), size=min(a.sample, len(pg)), replace=False)]
    st = samp[["n_s", "strict_agree_s", "gap_agree_s"]].sum()
    summ["sample300"] = dict(strict=float(st.strict_agree_s / st.n_s), gap_aware=float(st.gap_agree_s / st.n_s))
    by = pg.groupby(["season", "game_type"])[["n_s", "strict_agree_s", "gap_agree_s"]].sum()
    by["strict"] = by.strict_agree_s / by.n_s
    by["gap_aware"] = by.gap_agree_s / by.n_s
    pg["gap_rate"] = pg.gap_agree_s / pg.n_s
    summ["games_below_99pct_gap"] = int((pg.gap_rate < 0.99).sum())
    summ["by_season_type"] = by[["strict", "gap_aware", "n_s"]].reset_index().to_dict("records")
    if len(rn):
        summ["disagree_seconds_by_class"] = rn.groupby("cls").n_s.sum().to_dict()
        summ["disagree_runs_by_class"] = rn.groupby("cls").size().to_dict()
    (out / "summary.json").write_text(json.dumps(summ, indent=1, default=int))
    print(json.dumps(summ, indent=1, default=int))
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "done", flush=True)


if __name__ == "__main__":
    main()
