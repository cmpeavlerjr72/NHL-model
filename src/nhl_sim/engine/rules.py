"""Rule-era flags. They live in GameState, never inside sub-models (CLAUDE.md modeling rules)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuleEra:
    name: str = "nhl_2015_present"
    reg_period_s: int = 1200
    n_reg_periods: int = 3
    rs_ot_s: int = 300                 # regular-season OT length (3v3 since 2015-16)
    rs_ot_skaters: int = 3
    po_ot_s: int = 1200                # playoff OT periods, 5v5, sudden death, repeated
    full_skaters: int = 5
    min_skaters: int = 3               # 3-skater floor; extra penalties queue (stacked)
    max_running: int = 2               # penalties that count against strength at once
    minor_s: int = 120
    major_s: int = 300
    pp_goal_ends_minor: bool = True    # Rule 16.2: PP goal ends the oldest expirable minor of the shorthanded team
    coincidental_5v5_exception: bool = True   # one minor each at full strength -> 4v4 (Rule 19.1)
    ot_expiry_holds_until_stoppage: bool = True  # 3v3 OT: after an expiry the advantaged team keeps its extra
    #                                              skater until the next stoppage (Rule 84.2)
    shootout: bool = True              # regular season only; skipped by the strength-state engine


ERA_2015 = RuleEra()


def era_for_season(season: int) -> RuleEra:
    """All seasons in this project (2021-22 on) are the 3v3-OT era."""
    if int(season) < 20152016:
        raise ValueError(f"no rule era defined for season {season}")
    return ERA_2015
