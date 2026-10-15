"""Vectorised penalty box over N simulations x 2 teams (0 = home, 1 = away) x K slots.

Mechanics (RuleEra flags):
- minor 120 s, double minor 2 x 120 s (a PP goal in the first half ends the first minor and the second starts
  fresh; in the second half it ends the penalty), major 300 s (never ended by a goal);
- at most `max_running` penalties per team count against strength; further ones queue (stacked) and start, oldest
  first, when a running one ends (3-skater floor);
- a PP goal ends the oldest running *expirable* minor of the shorthanded team;
- coincidental minors under the 5v5 exception occupy a non-expirable running slot on both teams (4v4); offsetting
  coincidental penalties never enter the box.
"""
from __future__ import annotations

import numpy as np

from nhl_sim.engine.rules import RuleEra

MINOR, DOUBLE, MAJOR, COINC_MINOR = 1, 2, 3, 4
KIND_NAMES = {MINOR: "minor", DOUBLE: "double_minor", MAJOR: "major", COINC_MINOR: "coincidental_minor"}
_BIG = np.iinfo(np.int64).max


class BoxOverflow(RuntimeError):
    pass


class PenaltyBox:
    def __init__(self, n: int, era: RuleEra, k: int = 8):
        self.n, self.k, self.era = n, k, era
        shp = (n, 2, k)
        self.rem = np.zeros(shp, np.int32)        # seconds left in the current part (0 = empty slot)
        self.run = np.zeros(shp, bool)            # counts against strength now (False + rem>0 = queued)
        self.expi = np.zeros(shp, bool)           # can be ended by a PP goal
        self.dm2 = np.zeros(shp, bool)            # double minor with its second part still to serve
        self.kind = np.zeros(shp, np.int8)
        self.order = np.zeros(shp, np.int64)      # assessment sequence (oldest = smallest)
        self.who = np.full(shp, -1, np.int64)      # serving player (replay only; -1 = unknown)
        self.wait = np.zeros(shp, bool)           # chained behind the same player's earlier penalty
        self.pred = np.full(shp, -1, np.int64)     # order of the slot it waits for
        self.seq = np.zeros(n, np.int64)
        # counters for G1 ("share of minors ended by a PP goal")
        self.n_minor = np.zeros((n, 2), np.int32)
        self.n_minor_pp_ended = np.zeros((n, 2), np.int32)

    # ------------------------------------------------------------------ queries
    def n_running(self) -> np.ndarray:
        return self.run.sum(2)

    def any_active(self) -> np.ndarray:
        """(N, 2): team has any penalty in the box (running or queued)."""
        return (self.rem > 0).any(2)

    # ------------------------------------------------------------------ mutations
    def add(self, idx: np.ndarray, team: np.ndarray, kind: int, who=None) -> None:
        """Assess one penalty per (sim, team). `who` (serving player id, replay only): a player already in the box
        serves consecutively, so the new penalty waits for that player's latest penalty to end (it does not
        count against strength meanwhile)."""
        idx = np.asarray(idx, np.int64)
        team = np.broadcast_to(np.asarray(team, np.int64), idx.shape)
        if idx.size == 0:
            return
        if len(np.unique(idx * 2 + team)) != idx.size:
            raise ValueError("add(): one assessment per (sim, team) per call")
        active = self.rem[idx, team] > 0
        if active.all(1).any():
            raise BoxOverflow(f"more than {self.k} penalties in the box for one team")
        slot = np.argmin(active, axis=1)
        nrun = self.run[idx, team].sum(1)
        secs = self.era.major_s if kind == MAJOR else self.era.minor_s
        waits = np.zeros(idx.size, bool)
        if who is not None:
            who = np.broadcast_to(np.asarray(who, np.int64), idx.shape)
            same = active & (self.who[idx, team] == who[:, None]) & (who[:, None] >= 0)
            waits = same.any(1)
            last = np.argmax(np.where(same, self.order[idx, team], -1), axis=1)
            self.pred[idx[waits], team[waits], slot[waits]] = self.order[idx[waits], team[waits], last[waits]]
            self.who[idx, team, slot] = who
        self.wait[idx, team, slot] = waits
        self.rem[idx, team, slot] = secs
        self.run[idx, team, slot] = (nrun < self.era.max_running) & ~waits
        self.expi[idx, team, slot] = kind in (MINOR, DOUBLE)
        self.dm2[idx, team, slot] = kind == DOUBLE
        self.kind[idx, team, slot] = kind
        self.order[idx, team, slot] = self.seq[idx]
        np.add.at(self.seq, idx, 1)
        if kind == MINOR:
            np.add.at(self.n_minor, (idx, team), 1)

    def _clear(self, m) -> None:
        """m: boolean mask over (N, 2, K) or an (i, t, k) index tuple. Releases penalties chained behind it."""
        i, t, k = np.nonzero(m) if isinstance(m, np.ndarray) else m
        ords = self.order[i, t, k]
        if self.wait.any():
            rel = self.wait[i, t] & (self.pred[i, t] == ords[:, None])
            ii, kk = np.nonzero(rel)
            self.wait[i[ii], t[ii], kk] = False
        self.who[m] = -1
        self.wait[m] = False
        self.pred[m] = -1
        self.rem[m] = 0
        self.run[m] = False
        self.expi[m] = False
        self.dm2[m] = False
        self.kind[m] = 0

    def _start_queued(self) -> None:
        for _ in range(self.k):
            queued = (self.rem > 0) & ~self.run & ~self.wait
            need = queued.any(2) & (self.run.sum(2) < self.era.max_running)
            if not need.any():
                return
            o = np.where(queued, self.order, _BIG)
            first = np.argmin(o, axis=2)
            i, t = np.nonzero(need)
            self.run[i, t, first[i, t]] = True

    def tick(self, alive: np.ndarray) -> None:
        """End of a second for alive sims: running penalties lose one second. A part that reaches 0 is DUE and is
        expired by `expire_due` at the next second, after that second's events (so a goal at the exact expiry
        second still sees the penalty; for a double minor it counts as the first half)."""
        r = self.run & alive[:, None, None] & (self.rem > 0)
        self.rem[r] -= 1

    def expire_due(self, alive: np.ndarray) -> np.ndarray:
        """Expire due parts. Returns (N, 2) bool: a strength-affecting penalty ended."""
        exp = self.run & alive[:, None, None] & (self.rem == 0)
        if not exp.any():
            return np.zeros((self.n, 2), bool)
        part1 = exp & self.dm2
        if part1.any():               # double minor: second part starts at once, strength unchanged
            self.rem[part1] = self.era.minor_s
            self.dm2[part1] = False
        full = exp & ~part1
        ended = full.any(2)
        if full.any():
            self._clear(full)
            self._start_queued()
        return ended

    def pp_goal(self, idx: np.ndarray, scoring_team: np.ndarray) -> np.ndarray:
        """PP goal by `scoring_team` in sims `idx`: end the oldest running expirable minor of the other team.
        Returns bool per idx: a penalty part was ended."""
        idx = np.asarray(idx, np.int64)
        if idx.size == 0:
            return np.zeros(0, bool)
        opp = 1 - np.broadcast_to(np.asarray(scoring_team, np.int64), idx.shape)
        cand = self.run[idx, opp] & self.expi[idx, opp]   # rem == 0 (due this second) still counts
        has = cand.any(1)
        o = np.where(cand, self.order[idx, opp], _BIG)
        k = np.argmin(o, axis=1)
        ii, tt, kk = idx[has], opp[has], k[has]
        second = self.dm2[ii, tt, kk]
        # double minor in its first half: first minor ends, second starts fresh
        self.rem[ii[second], tt[second], kk[second]] = self.era.minor_s
        self.dm2[ii[second], tt[second], kk[second]] = False
        end = ~second
        if end.any():
            minor_end = self.kind[ii[end], tt[end], kk[end]] == MINOR
            np.add.at(self.n_minor_pp_ended, (ii[end][minor_end], tt[end][minor_end]), 1)
            self._clear((ii[end], tt[end], kk[end]))
            self._start_queued()
        return has
