"""GameState: NumPy arrays over N simulations (games x seeds) advanced in lockstep, one second per step.

Clock convention: `t` is elapsed game seconds (periods 1-3 = 0..3599, RS OT = 3600..3899, playoff OT periods of
1200 s from 3600). Events at second t are applied, then the second is recorded with the post-event state, then
`end_second()` runs the box clock (a minor assessed at t covers seconds t..t+119).

Team index 0 = home, 1 = away. Skater counts here are penalty-derived (goalie pulls are not modelled at this
stage; a replay passes the real goalie state separately).
"""
from __future__ import annotations

import numpy as np

from nhl_sim.engine.box import COINC_MINOR, DOUBLE, MAJOR, MINOR, PenaltyBox
from nhl_sim.engine.rules import RuleEra

END_NONE, END_REG, END_OT, END_SO = 0, 1, 2, 3
END_NAMES = {END_REG: "REG", END_OT: "OT", END_SO: "SO"}


class GameState:
    def __init__(self, game_type: np.ndarray, era: RuleEra, auto_end: bool = True, k_slots: int = 8):
        self.gt = np.asarray(game_type, np.int8)
        self.n = len(self.gt)
        self.era = era
        self.auto_end = auto_end
        self.t = 0
        self.box = PenaltyBox(self.n, era, k_slots)
        self.score = np.zeros((self.n, 2), np.int16)
        self.pen_count = np.zeros((self.n, 2), np.int16)   # penalty-taking events so far (coincidental: both)
        self.alive = np.ones(self.n, bool)
        self.end_state = np.zeros(self.n, np.int8)
        self.hold = np.zeros(self.n, bool)                 # 3v3 OT post-expiry hold until the next stoppage
        self.held = np.zeros((self.n, 2), np.int8)
        self.reg_end = era.reg_period_s * era.n_reg_periods
        self.is_rs = self.gt == 2

    # ------------------------------------------------------------------ clock / periods
    def period(self) -> np.ndarray:
        """(N,) period number at the current second (1-3 regulation, 4+ OT)."""
        t, e = self.t, self.era
        if t < self.reg_end:
            return np.full(self.n, t // e.reg_period_s + 1, np.int8)
        return np.where(self.is_rs, 4, 4 + (t - self.reg_end) // e.po_ot_s).astype(np.int8)

    def in_ot(self) -> bool:
        return self.t >= self.reg_end

    def rs_ot(self) -> np.ndarray:
        """(N,) bool: currently in regular-season 3v3 overtime."""
        return self.is_rs & (self.t >= self.reg_end)

    # ------------------------------------------------------------------ strength
    def _mapped_skaters(self) -> np.ndarray:
        e = self.era
        nr = np.minimum(self.box.n_running(), e.max_running).astype(np.int8)
        sk = (e.full_skaters - nr).astype(np.int8)
        ot = self.rs_ot()
        if ot.any():
            d = nr[ot, 1].astype(np.int16) - nr[ot, 0]
            base = e.rs_ot_skaters
            sk[ot, 0] = np.clip(base + np.maximum(d, 0), base, e.full_skaters)
            sk[ot, 1] = np.clip(base + np.maximum(-d, 0), base, e.full_skaters)
        return sk

    def skaters(self) -> np.ndarray:
        """(N, 2) penalty-derived skaters on ice (home, away)."""
        sk = self._mapped_skaters()
        if self.hold.any():
            sk[self.hold] = self.held[self.hold]
        return sk

    # ------------------------------------------------------------------ events
    def goal(self, idx: np.ndarray, team: np.ndarray) -> None:
        idx = np.asarray(idx, np.int64)
        if idx.size == 0:
            return
        team = np.broadcast_to(np.asarray(team, np.int64), idx.shape)
        sk = self.skaters()[idx]
        pp = sk[np.arange(idx.size), team] > sk[np.arange(idx.size), 1 - team]
        np.add.at(self.score, (idx, team), 1)
        if self.era.pp_goal_ends_minor and pp.any():
            self.box.pp_goal(idx[pp], team[pp])
        if self.auto_end and self.in_ot():
            self.alive[idx] = False
            self.end_state[idx] = END_OT

    def penalty(self, idx: np.ndarray, team: np.ndarray, kind: int, who=None) -> None:
        idx = np.asarray(idx, np.int64)
        if idx.size == 0:
            return
        team = np.broadcast_to(np.asarray(team, np.int64), idx.shape)
        if kind not in (MINOR, DOUBLE, MAJOR):
            raise ValueError(kind)
        self.box.add(idx, team, kind, who=who)
        np.add.at(self.pen_count, (idx, team), 1)

    def coincidental(self, idx: np.ndarray, single_minor_pair: np.ndarray) -> np.ndarray:
        """Coincidental penalties at one stoppage. With the 5v5 exception (exactly one minor each, both teams at
        full strength, not 3v3 OT) both teams go a skater down (4v4, non-expirable); otherwise they offset.
        Every coincidental event counts once for each team in `pen_count`. Returns bool per idx: 4v4 applied."""
        idx = np.asarray(idx, np.int64)
        if idx.size == 0:
            return np.zeros(0, bool)
        smp = np.broadcast_to(np.asarray(single_minor_pair, bool), idx.shape)
        np.add.at(self.pen_count, (idx, 0), 1)
        np.add.at(self.pen_count, (idx, 1), 1)
        full = ~self.box.any_active()[idx].any(1)
        ex = smp & full & ~self.rs_ot()[idx] & self.era.coincidental_5v5_exception
        j = idx[ex]
        self.box.add(j, np.zeros(j.size, np.int64), COINC_MINOR)
        self.box.add(j, np.ones(j.size, np.int64), COINC_MINOR)
        return ex

    def stoppage(self, idx: np.ndarray) -> None:
        self.hold[np.asarray(idx, np.int64)] = False

    # ------------------------------------------------------------------ advance
    def settle(self) -> None:
        """Expire penalties due at this second. Convention (chosen on fold-1 replay agreement): call it at the
        start of each second, BEFORE that second's events, so a goal at the exact expiry second no longer sees
        the expired part (calling it after the events is the alternative 'lazy' convention)."""
        e = self.era
        before = self.skaters() if self.in_ot() else None
        ended = self.box.expire_due(self.alive)
        if self.in_ot() and e.ot_expiry_holds_until_stoppage:
            m = self.alive & self.rs_ot() & ended.any(1)
            if m.any():
                b = before[m].astype(np.int16)
                # the returning player comes back on; a team that had the man advantage keeps its extra skater
                # until the next stoppage (only a team that was outnumbered gains a skater)
                inc = ended[m] & (b < b[:, ::-1])
                held = np.minimum(b + inc, e.full_skaters)
                new = self._mapped_skaters()[m]
                h = (held != new).any(1)
                mi = np.nonzero(m)[0]
                self.held[mi[h]] = held[h]
                self.hold[mi[h]] = True
                self.hold[mi[~h]] = False

    def end_second(self) -> None:
        e = self.era
        self.box.tick(self.alive)
        self.t += 1
        if not self.auto_end:
            return
        t = self.t
        if t == self.reg_end:
            dec = self.alive & (self.score[:, 0] != self.score[:, 1])
            self.alive[dec] = False
            self.end_state[dec] = END_REG
            self.hold[:] = False
        elif t == self.reg_end + e.rs_ot_s:
            so = self.alive & self.is_rs
            self.alive[so] = False
            self.end_state[so] = END_SO
