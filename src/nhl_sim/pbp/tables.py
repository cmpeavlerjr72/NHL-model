"""Raw NHL API JSON -> flat per-game row sets (events, shifts, player_box, goalie_box, game summary)."""
from __future__ import annotations

import json
from pathlib import Path

from nhl_sim.pbp.event_map import map_event

RAW = Path(__file__).resolve().parents[3] / "data" / "raw" / "nhl_api"
SHOT_EVENTS = ("SHOT", "MISS", "BLOCK", "GOAL", "FAILED_SHOT_ATTEMPT")


def mmss(s):
    if s is None or s == "":
        return None
    m, sec = s.split(":")
    return int(m) * 60 + int(sec)


def period_offset(period: int, game_type: int) -> int:
    """Elapsed game seconds at the start of a period (RS OT = 300s, playoff OT = 1200s)."""
    if period <= 3:
        return 1200 * (period - 1)
    ot_len = 1200 if game_type == 3 else 300
    return 3600 + ot_len * (period - 4)


def strength_label(sf: int, sa: int, own_g: int, opp_g: int) -> str:
    """Strength state from the event owner's view."""
    if not own_g:
        return "EN_FOR"      # owner has pulled its goalie
    if not opp_g:
        return "EN_AGAINST"  # opponent has pulled its goalie
    if sf == sa:
        return f"{sf}v{sa}"
    return "PP" if sf > sa else "PK"


def _ratio(s):
    """'saves/shots' string -> (saves, shots)."""
    if not s:
        return None, None
    a, b = s.split("/")
    return int(a), int(b)


def load(kind: str, gid: int):
    path = RAW / kind / f"{gid}.json"
    if kind == "shifts" and not path.exists():
        return {"data": [], "total": 0}   # NHL API has no chart for this game (see audit)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def process_game(gid: int):
    pbp, box, sh = load("pbp", gid), load("boxscore", gid), load("shifts", gid)
    gt = pbp["gameType"]
    home_id, away_id = pbp["homeTeam"]["id"], pbp["awayTeam"]["id"]
    pos = {r["playerId"]: r["positionCode"] for r in pbp.get("rosterSpots", [])}
    ev, hs, as_ = [], 0, 0
    reg_goals = {home_id: 0, away_id: 0}
    so_goals = {home_id: 0, away_id: 0}
    last_period, last_ptype = 1, "REG"
    for p in sorted(pbp["plays"], key=lambda x: x["sortOrder"]):
        d = p.get("details", {})
        pd_ = p["periodDescriptor"]
        per, ptype = pd_["number"], pd_["periodType"]
        etype, fam = map_event(p["typeDescKey"])
        owner = d.get("eventOwnerTeamId")
        is_home = None if owner is None else owner == home_id
        sc = p.get("situationCode") or ""
        row = dict(game_id=gid, season=pbp["season"], game_type=gt, event_id=p["eventId"], sort_order=p["sortOrder"],
                   period=per, period_type=ptype, time_in_period_s=mmss(p.get("timeInPeriod")),
                   event=etype, family=fam, type_desc_key=p["typeDescKey"], owner_team_id=owner, owner_is_home=is_home)
        row["game_time_s"] = (None if row["time_in_period_s"] is None
                              else period_offset(per, gt) + row["time_in_period_s"])
        row["situation_code"] = sc or None
        if len(sc) == 4:
            ag, ask, hsk, hg = (int(c) for c in sc)
            row.update(away_goalie=ag, away_skaters=ask, home_skaters=hsk, home_goalie=hg)
            if is_home is not None:
                sf, sa = (hsk, ask) if is_home else (ask, hsk)
                og, pg = (hg, ag) if is_home else (ag, hg)
                row["strength_state"] = "SO" if ptype == "SO" else strength_label(sf, sa, og, pg)
                row["skaters_for"], row["skaters_against"] = sf, sa
        row["home_score_pre"], row["away_score_pre"] = hs, as_
        row["home_def_side"] = p.get("homeTeamDefendingSide")
        x, y = d.get("xCoord"), d.get("yCoord")
        row["x"], row["y"], row["zone"] = x, y, d.get("zoneCode")
        if x is not None and is_home is not None and row["home_def_side"]:
            # owner attacks +x after normalisation
            att = 1 if ((is_home and row["home_def_side"] == "left") or
                        (not is_home and row["home_def_side"] == "right")) else -1
            row["x_norm"], row["y_norm"] = x * att, y * att
            if etype in SHOT_EVENTS:
                # eventOwnerTeamId is the SHOOTING team for blocked shots too, and x/y are already in the
                # shooter's frame (zoneCode, however, is relative to the blocking team: 'D' for most blocks).
                row["sx"], row["sy"] = x * att, y * att
        if etype in SHOT_EVENTS:
            row["shooting_team_id"] = owner
        row.update(shot_type=d.get("shotType"), shooter_id=d.get("shootingPlayerId", d.get("scoringPlayerId")),
                   goalie_id=d.get("goalieInNetId"), blocker_id=d.get("blockingPlayerId"),
                   reason=d.get("reason"), secondary_reason=d.get("secondaryReason"),
                   assist1_id=d.get("assist1PlayerId"), assist2_id=d.get("assist2PlayerId"),
                   faceoff_winner_id=d.get("winningPlayerId"), faceoff_loser_id=d.get("losingPlayerId"),
                   hitter_id=d.get("hittingPlayerId"), hittee_id=d.get("hitteePlayerId"),
                   player_id=d.get("playerId"),
                   pen_type=d.get("typeCode") if etype == "PENALTY" else None, pen_desc=d.get("descKey"),
                   pen_minutes=d.get("duration"), pen_committed_by=d.get("committedByPlayerId"),
                   pen_drawn_by=d.get("drawnByPlayerId"), pen_served_by=d.get("servedByPlayerId"))
        ev.append(row)
        if etype == "GOAL":
            if ptype == "SO":
                so_goals[owner] += 1
            else:
                reg_goals[owner] += 1
                hs, as_ = (hs + 1, as_) if owner == home_id else (hs, as_ + 1)
        last_period, last_ptype = per, ptype
    # pbp-accumulated final
    h, a = reg_goals[home_id], reg_goals[away_id]
    if so_goals[home_id] > so_goals[away_id]:
        h += 1
    elif so_goals[away_id] > so_goals[home_id]:
        a += 1
    # shifts (typeCode 517 = real shift; 505 = goal marker)
    shifts = []
    for r in sh["data"]:
        if r["typeCode"] != 517:
            continue
        off = period_offset(r["period"], gt)
        s, e = mmss(r["startTime"]), mmss(r["endTime"])
        shifts.append(dict(game_id=gid, season=pbp["season"], player_id=r["playerId"], team_id=r["teamId"],
                           position=pos.get(r["playerId"]), period=r["period"], shift_number=r["shiftNumber"],
                           start_s=None if s is None else off + s, end_s=None if e is None else off + e,
                           duration_s=mmss(r["duration"])))
    # boxscores
    pbs, gbs = [], []
    for side, tid in (("homeTeam", home_id), ("awayTeam", away_id)):
        t = box["playerByGameStats"][side]
        for grp in ("forwards", "defense"):
            for q in t[grp]:
                pbs.append(dict(game_id=gid, season=pbp["season"], team_id=tid, is_home=side == "homeTeam",
                                player_id=q["playerId"], position=q["position"], group=grp, name=q["name"]["default"],
                                goals=q["goals"], assists=q["assists"], points=q["points"], plus_minus=q["plusMinus"],
                                pim=q["pim"], hits=q["hits"], ppg=q["powerPlayGoals"], sog=q["sog"],
                                faceoff_pct=q["faceoffWinningPctg"], toi_s=mmss(q["toi"]), blocks=q["blockedShots"],
                                shifts=q["shifts"], giveaways=q["giveaways"], takeaways=q["takeaways"]))
        for q in t["goalies"]:
            es = _ratio(q.get("evenStrengthShotsAgainst"))
            pp = _ratio(q.get("powerPlayShotsAgainst"))
            sk = _ratio(q.get("shorthandedShotsAgainst"))
            gbs.append(dict(game_id=gid, season=pbp["season"], team_id=tid, is_home=side == "homeTeam",
                            player_id=q["playerId"], name=q["name"]["default"], starter=q.get("starter"),
                            decision=q.get("decision"), toi_s=mmss(q["toi"]), shots_against=q.get("shotsAgainst"),
                            saves=q.get("saves"), goals_against=q.get("goalsAgainst"), pim=q.get("pim"),
                            es_saves=es[0], es_sa=es[1], pp_saves=pp[0], pp_sa=pp[1], sh_saves=sk[0], sh_sa=sk[1]))
    game = dict(game_id=gid, season=pbp["season"], game_type=gt, game_date_local=pbp["gameDate"],
                puck_drop_utc=pbp["startTimeUTC"], home_id=home_id, away_id=away_id,
                home=pbp["homeTeam"]["abbrev"], away=pbp["awayTeam"]["abbrev"],
                home_score_box=box["homeTeam"]["score"], away_score_box=box["awayTeam"]["score"],
                end_state_box=(box.get("gameOutcome") or {}).get("lastPeriodType"),
                home_score_pbp=h, away_score_pbp=a, end_state_pbp=last_ptype, last_period_pbp=last_period,
                home_sog_box=box["homeTeam"].get("sog"), away_sog_box=box["awayTeam"].get("sog"),
                home_goals_playersum=sum(q["goals"] for q in pbs if q["is_home"]),
                away_goals_playersum=sum(q["goals"] for q in pbs if not q["is_home"]),
                home_ga_goaliesum=sum(q["goals_against"] or 0 for q in gbs if q["is_home"]),
                away_ga_goaliesum=sum(q["goals_against"] or 0 for q in gbs if not q["is_home"]),
                n_events=len(ev), n_shift_rows=len(shifts))
    return game, ev, shifts, pbs, gbs
