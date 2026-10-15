"""SS-R2 change 1: delayed-penalty state (LEARNINGS L20).

A DELAYED_PENALTY event is the referee's signal against its owner team (the penalised team: in 2024-25 every one of
the 3,252 signal windows that end in a PENALTY whistle ends in a penalty on the owner). Play continues, the
non-offending team pulls its goalie, and the penalty is recorded at the whistle. The pbp goalie state between the
signal and the whistle is therefore CAUSED by the penalty. SS-R2 gives those seconds, and the penalty recorded at
the whistle, the state at the signal, before the pull.

Window: from the signal second ts up to (not including) the second tw of the first whistle event after the signal
by sort order (STOPPAGE, GOAL, PENALTY, PERIOD_END, GAME_END). A penalty at second t is counted in the row holding
second t-1 (tables.py), so a penalty at the whistle falls in the window.
Pre-signal goalie state: the situation code of the last event strictly before the signal (sort order). The code on
the signal event itself is not used, because the pbp sometimes stamps the signal with the post-pull code (244 of
7,092 signals in 2023-25 show a pulled goalie that the previous event did not). A goalie already pulled before the
signal (a trailing-team pull) stays pulled. Overlapping windows take the earliest signal's pre-signal state.
Only the goalie digits are replaced; the skater counts stay the engine replay of the real penalties.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

WHISTLES = ("STOPPAGE", "GOAL", "PENALTY", "PERIOD_END", "GAME_END")


def delayed_windows(ev: pd.DataFrame, game_ids) -> pd.DataFrame:
    """ev: events of the games (any order), SO excluded by the caller or here. Returns one row per signal:
    g (index into game_ids), ts, tw, owner_team (0 home / 1 away), pre_ag, pre_hg (goalie digits before the
    signal, 1 = in, 0 = pulled), whistle (event name ending the window)."""
    x = ev[ev.period_type != "SO"].sort_values(["game_id", "sort_order"]).reset_index(drop=True)
    gi = {g: i for i, g in enumerate(np.asarray(game_ids))}
    code = x.situation_code.where(x.situation_code.str.len() == 4)
    prev_code = code.groupby(x.game_id).transform(lambda s: s.ffill().shift(1))
    is_wh = x.event.isin(WHISTLES).to_numpy()
    gid = x.game_id.to_numpy()
    t = x.game_time_s.to_numpy().astype(np.int64)
    # index of the next whistle event at or after each row (same game)
    n = len(x)
    nxt = np.full(n, -1, np.int64)
    last = -1
    for i in range(n - 1, -1, -1):
        if i + 1 < n and gid[i + 1] != gid[i]:
            last = -1
        nxt[i] = last
        if is_wh[i]:
            last = i
    sig = np.nonzero((x.event == "DELAYED_PENALTY").to_numpy())[0]
    rows = []
    for i in sig:
        j = nxt[i]
        pc = prev_code.iloc[i]
        if not isinstance(pc, str):
            pc = code.iloc[i] if isinstance(code.iloc[i], str) else "1551"
        tw = int(t[j]) if j >= 0 else int(t[i])
        rows.append((gi[gid[i]], int(t[i]), tw, 0 if bool(x.owner_is_home.iloc[i]) else 1, int(pc[0]), int(pc[3]),
                     x.event.iloc[j] if j >= 0 else "END"))
    return pd.DataFrame(rows, columns=["g", "ts", "tw", "owner_team", "pre_ag", "pre_hg", "whistle"])


def apply_delayed_fix(prev: np.ndarray, windows: pd.DataFrame) -> tuple[np.ndarray, int]:
    """Return a copy of the (N, T, 4) carry-forward pbp codes with the goalie digits of every signal window set to
    the pre-signal state, and the number of seconds whose goalie state changed."""
    out = prev.copy()
    T = prev.shape[1]
    # latest signal first, so an earlier overlapping signal overwrites it
    for r in windows.sort_values("ts", ascending=False).itertuples():
        a, b = r.ts, min(r.tw, T)
        if b <= a:
            continue
        out[r.g, a:b, 0] = r.pre_ag
        out[r.g, a:b, 3] = r.pre_hg
    changed = int(((out[..., 0] != prev[..., 0]) | (out[..., 3] != prev[..., 3])).sum())
    return out, changed
