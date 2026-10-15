"""Per-second timelines for one batch of games: the replayed (engine) skater counts and the pbp situationCode.

The pbp situationCode is event-sampled: it is only observed at events. For second s:
  prev code = code of the last event with game_time_s <= s (by sort order)   ("carry-forward")
  next code = code of the first event with game_time_s > s
A second is UNAMBIGUOUS when prev == next (no state change can be dated inside the gap) and AMBIGUOUS otherwise
(the change happened somewhere in the gap, e.g. a penalty expiring between two events).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.engine.replay import replay
from nhl_sim.engine.rules import era_for_season
from nhl_sim.strength_state.events import mech_events, penalty_events

EV_COLS = ["game_id", "season", "game_type", "sort_order", "event", "period", "period_type", "game_time_s",
           "owner_is_home", "situation_code", "pen_type", "pen_desc", "pen_minutes", "pen_committed_by",
           "pen_served_by", "home_score_pre", "away_score_pre"]


def game_frame(ev: pd.DataFrame) -> pd.DataFrame:
    x = ev[ev.period_type != "SO"]
    g = x.groupby("game_id").agg(season=("season", "first"), game_type=("game_type", "first"),
                                 end_t=("game_time_s", "max")).reset_index()
    so = ev[ev.period_type == "SO"].game_id.unique()
    g["went_so"] = g.game_id.isin(so)
    g["end_t"] = g.end_t.astype(int)
    return g


def pbp_codes(ev: pd.DataFrame, games: pd.DataFrame, T: int):
    """(N, T, 4) prev and next situation codes as int8 digits (away_g, away_sk, home_sk, home_g); -1 = none."""
    N = len(games)
    prev = np.full((N, T, 4), -1, np.int8)
    nxt = np.full((N, T, 4), -1, np.int8)
    x = ev[(ev.period_type != "SO") & ev.situation_code.notna()].sort_values(["game_id", "sort_order"])
    x = x[x.situation_code.str.len() == 4]
    digits = np.array([list(map(int, s)) for s in x.situation_code.to_numpy()], np.int8).reshape(-1, 4)
    gid = x.game_id.to_numpy()
    tm = x.game_time_s.to_numpy().astype(np.int64)
    bounds = np.searchsorted(gid, games.game_id.to_numpy(), side="left"), \
        np.searchsorted(gid, games.game_id.to_numpy(), side="right")
    sec = np.arange(T)
    for i, (a, b) in enumerate(zip(*bounds)):
        if b <= a:
            continue
        t_g, d_g = tm[a:b], digits[a:b]
        ip = np.searchsorted(t_g, sec, side="right") - 1
        inx = ip + 1
        ok = ip >= 0
        prev[i, ok] = d_g[ip[ok]]
        ok2 = inx < len(t_g)
        nxt[i, ok2] = d_g[inx[ok2]]
        # before the first event, prev is unknown: use the first code
        prev[i, ~ok] = d_g[0]
    return prev, nxt


def season_timeline(ev: pd.DataFrame, expire_first: bool = True):
    """Replay every game in `ev` (one season or a subset). Returns dict with games, sk, goalies (from pbp
    carry-forward), prev/next pbp codes, targets, mech, box counters."""
    ev = ev.sort_values(["game_id", "sort_order"]).reset_index(drop=True)
    games = game_frame(ev)
    targets, tally, pen_mech = penalty_events(ev)
    mech = mech_events(ev, targets, pen_mech)
    seasons = games.season.unique()
    era = era_for_season(int(seasons.max()))
    for s in seasons:
        assert era_for_season(int(s)) is era
    T = int(games.end_t.max())
    rp = replay(games.game_id.to_numpy(), games.game_type.to_numpy(), games.end_t.to_numpy(), mech, era,
                expire_first=expire_first)
    prev, nxt = pbp_codes(ev, games, T)
    return dict(games=games, sk=rp["sk"], prev=prev, nxt=nxt, targets=targets, tally=tally, mech=mech,
                n_minor=rp["n_minor"], n_minor_pp_ended=rp["n_minor_pp_ended"], coinc_4v4=rp["coinc_4v4"], T=T)


def engine_codes(tl) -> np.ndarray:
    """(N, T, 4) engine situation code: penalty skaters + the pbp (carry-forward) goalie state; a pulled goalie
    adds an extra attacker, as in the pbp code."""
    sk, prev = tl["sk"], tl["prev"]
    ag, hg = prev[..., 0], prev[..., 3]
    out = np.empty_like(prev)
    out[..., 0] = ag
    out[..., 3] = hg
    out[..., 1] = sk[..., 1] + (ag == 0)
    out[..., 2] = sk[..., 0] + (hg == 0)
    return out


def agreement(tl):
    """Per-game played-second agreement (strict carry-forward, and gap-aware)."""
    games = tl["games"]
    T = tl["T"]
    played = np.arange(T)[None, :] < games.end_t.to_numpy()[:, None]
    eng = engine_codes(tl)
    prev, nxt = tl["prev"], tl["nxt"]
    eq_prev = (eng == prev).all(-1)
    eq_next = (eng == nxt).all(-1) & (nxt[..., 0] >= 0)
    amb = ~(prev == nxt).all(-1) & (nxt[..., 0] >= 0)
    strict = eq_prev
    # gap-aware check on penalty-derived skaters (pbp skaters minus the extra attacker of a pulled goalie, so a
    # goalie pull inside the gap does not mask the comparison). Inside an ambiguous gap each team's count must
    # lie between the bracketing counts (it may or may not have changed yet; two changes can share one gap).
    def pen_sk(c):
        return np.stack([c[..., 2] - (c[..., 3] == 0), c[..., 1] - (c[..., 0] == 0)], -1)
    sk, ps, ns = tl["sk"], pen_sk(prev), pen_sk(nxt)
    lo, hi = np.minimum(ps, ns), np.maximum(ps, ns)
    in_gap = ((sk >= lo) & (sk <= hi)).all(-1)
    gap = np.where(amb, in_gap, (sk == ps).all(-1))
    out = games[["game_id", "season", "game_type", "end_t"]].copy()
    out["n_s"] = played.sum(1)
    out["strict_agree_s"] = (strict & played).sum(1)
    out["gap_agree_s"] = (gap & played).sum(1)
    out["ambiguous_s"] = (amb & played).sum(1)
    out["strict_miss_unambiguous_s"] = (~strict & ~amb & played).sum(1)
    return out, dict(eng=eng, strict=strict, gap=gap, amb=amb, played=played)
