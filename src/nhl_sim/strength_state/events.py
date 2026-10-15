"""Real pbp -> mechanics events (for replay) and penalty-taking events (SS-R1 target).

Per stoppage (same game, same game_time_s) the strength penalties of the two teams are resolved like the rulebook:
majors cancel majors one for one, then minor units cancel one for one (a double minor is 2 units; singles are
cancelled before doubles). A stoppage with any cancellation yields ONE coincidental penalty-taking event for EACH
team (the spec: "counted for both teams and typed as coincidental"); the 5v5 exception flag `smp` is set when the
stoppage holds exactly one single minor per team and nothing else. Every uncancelled penalty is one event of its
class (minor / double / major); uncancelled penalties of ONE serving player at one stoppage are served
consecutively (majors first) and form ONE penalty-taking event (minor+minor -> double, anything with a major ->
major; the n_raw column keeps the raw count). Misconducts, game misconducts and penalty shots are tallied, not targets.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from nhl_sim.strength_state.penalty_map import classify_frame

PEN_COLS = ["game_id", "season", "game_type", "sort_order", "event", "period_type", "game_time_s", "owner_is_home",
            "pen_type", "pen_desc", "pen_minutes", "pen_committed_by", "pen_served_by"]
TARGET_CLASSES = ("minor", "double", "major", "coincidental")
UNIT_PIM = {"minor": 2, "double": 4, "major": 5}


def _resolve(items):
    """items: list of (sort_order, team, cls, who) at one stoppage -> (coinc dict | None, remaining list of
    (sort_order, team, cls, who))."""
    by = {0: [], 1: []}
    for so, tm, c, w in sorted(items):
        by[tm].append([so, c, w])
    maj = {t: [x for x in by[t] if x[1] == "major"] for t in (0, 1)}
    c_maj = min(len(maj[0]), len(maj[1]))
    rem = {t: maj[t][c_maj:] for t in (0, 1)}
    singles = {t: [x for x in by[t] if x[1] == "minor"] for t in (0, 1)}
    doubles = {t: [x for x in by[t] if x[1] == "double"] for t in (0, 1)}
    units = {t: len(singles[t]) + 2 * len(doubles[t]) for t in (0, 1)}
    c_min = min(units[0], units[1])
    for t in (0, 1):
        k = c_min
        s = singles[t][k:] if k <= len(singles[t]) else []
        k = max(0, k - len(singles[t]))
        d = []
        for so, _, w in doubles[t]:
            if k >= 2:
                k -= 2
            elif k == 1:
                k = 0
                s.append([so, "minor", w])
            else:
                d.append([so, "double", w])
        rem[t] += s + d
    remaining = sorted((so, t, c, w) for t in (0, 1) for so, c, w in rem[t])
    coinc = None
    if c_maj + c_min > 0:
        smp = (c_maj == 0 and all(len(by[t]) == 1 and by[t][0][1] == "minor" for t in (0, 1)))
        coinc = dict(so=min(x[0] for x in items), smp=bool(smp),
                     pim=int(2 * (5 * c_maj + 2 * c_min)), n_major_pairs=c_maj, n_minor_unit_pairs=c_min)
    return coinc, remaining


def penalty_events(ev: pd.DataFrame):
    """ev: events rows (any seasons). Returns (targets, tally):
    targets: one row per penalty-taking event: game_id, season, game_type, t, so, team (0 home / 1 away),
             cls in TARGET_CLASSES, smp, pim.
    tally: counts of non-target penalty rows by class (misconduct / game_misc / ps) per season."""
    p = ev[(ev.event == "PENALTY") & (ev.period_type != "SO")].copy()
    if p.owner_is_home.isna().any():
        raise ValueError("penalty rows without an owner team")
    p["cls"] = classify_frame(p)
    tally = p[~p.cls.isin(["minor", "double", "major"])].groupby(["season", "cls"]).size().rename("n").reset_index()
    s = p[p.cls.isin(["minor", "double", "major"])]
    # consecutive-service key: the penalised player (a substitute may serve); bench minors: the server
    who = s.pen_committed_by.where(s.pen_committed_by.notna(), s.pen_served_by)
    s = s.assign(team=np.where(s.owner_is_home.astype(bool), 0, 1), who=who.fillna(-1).astype(np.int64))
    rows, mech = [], []
    meta = s.groupby("game_id")[["season", "game_type"]].first()
    for (gid, t), grp in s.groupby(["game_id", "game_time_s"], sort=True):
        items = list(zip(grp.sort_order.tolist(), grp.team.tolist(), grp.cls.tolist(), grp.who.tolist()))
        coinc, remaining = _resolve(items)
        se, gt = meta.loc[gid, "season"], meta.loc[gid, "game_type"]
        if coinc is not None:
            for tm in (0, 1):
                rows.append((gid, se, gt, int(t), coinc["so"], tm, "coincidental", coinc["smp"], coinc["pim"], 1))
        # same serving player at one stoppage: served consecutively (majors first) -> ONE penalty-taking event
        groups = {}
        for so, tm, c, w in remaining:
            key = (tm, w) if w >= 0 else (tm, -so - 1)
            groups.setdefault(key, []).append((so, c))
        for (tm, w), lst in groups.items():
            cl = [c for _, c in lst]
            units = sum(1 if c == "minor" else 2 if c == "double" else 0 for c in cl)
            cls = "major" if "major" in cl else ("double" if units >= 2 else "minor")
            so0 = min(so for so, _ in lst)
            rows.append((gid, se, gt, int(t), so0, tm, cls, False, sum(UNIT_PIM[c] for c in cl), len(lst)))
            for j, (so, c) in enumerate(sorted(lst, key=lambda x: (x[1] != "major", x[0]))):
                mech.append((gid, int(t), so0 + 0.01 * j, "pen", tm, c, False, w))
    tg = pd.DataFrame(rows, columns=["game_id", "season", "game_type", "t", "so", "team", "cls", "smp", "pim",
                                     "n_raw"])
    mp = pd.DataFrame(mech, columns=["game_id", "t", "so", "kind", "team", "cls", "smp", "who"])
    return tg, tally, mp


def mech_events(ev: pd.DataFrame, targets: pd.DataFrame, pen_mech: pd.DataFrame) -> pd.DataFrame:
    """Ordered mechanics events per game for the replay: kind in {goal, pen, coinc, stop}.
    Coincidental events appear once per stoppage (team = -1)."""
    g = ev[(ev.event == "GOAL") & (ev.period_type != "SO")]
    goals = pd.DataFrame({"game_id": g.game_id, "t": g.game_time_s.astype(int), "so": g.sort_order, "kind": "goal",
                          "team": np.where(g.owner_is_home.astype(bool), 0, 1), "cls": "", "smp": False, "who": -1})
    st = ev[ev.event.isin(["STOPPAGE", "FACEOFF"]) & (ev.period_type != "SO")]
    stops = pd.DataFrame({"game_id": st.game_id, "t": st.game_time_s.astype(int), "so": st.sort_order, "kind": "stop",
                          "team": -1, "cls": "", "smp": False, "who": -1})
    pens = pen_mech
    cc = targets[(targets.cls == "coincidental") & (targets.team == 0)]
    # coincidental first within its stoppage (so - 0.5), then the uncancelled penalties
    coincs = pd.DataFrame({"game_id": cc.game_id, "t": cc.t, "so": cc.so - 0.5, "kind": "coinc", "team": -1,
                           "cls": "coincidental", "smp": cc.smp, "who": -1})
    m = pd.concat([goals, stops, pens, coincs], ignore_index=True)
    return m.sort_values(["game_id", "t", "so"]).reset_index(drop=True)
