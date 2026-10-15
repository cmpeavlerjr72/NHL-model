"""Explicit NHL API play-by-play event-type mapping. Unknown types raise."""
from __future__ import annotations

# typeDescKey -> (canonical event, family)
EVENT_MAP: dict[str, tuple[str, str]] = {
    "faceoff": ("FACEOFF", "stoppage_restart"),
    "hit": ("HIT", "physical"),
    "giveaway": ("GIVEAWAY", "possession"),
    "takeaway": ("TAKEAWAY", "possession"),
    "shot-on-goal": ("SHOT", "shot_attempt"),
    "missed-shot": ("MISS", "shot_attempt"),
    "blocked-shot": ("BLOCK", "shot_attempt"),
    "goal": ("GOAL", "shot_attempt"),
    "penalty": ("PENALTY", "penalty"),
    "delayed-penalty": ("DELAYED_PENALTY", "penalty"),
    "stoppage": ("STOPPAGE", "stoppage_restart"),
    "period-start": ("PERIOD_START", "admin"),
    "period-end": ("PERIOD_END", "admin"),
    "game-end": ("GAME_END", "admin"),
    "shootout-complete": ("SHOOTOUT_COMPLETE", "admin"),
    "failed-shot-attempt": ("FAILED_SHOT_ATTEMPT", "shootout"),
}

SHOT_ATTEMPT_TYPES = {"SHOT", "MISS", "BLOCK", "GOAL"}


class UnknownEventType(KeyError):
    pass


def map_event(type_desc_key: str) -> tuple[str, str]:
    try:
        return EVENT_MAP[type_desc_key]
    except KeyError:
        raise UnknownEventType(f"unmapped NHL pbp event type: {type_desc_key!r}") from None
