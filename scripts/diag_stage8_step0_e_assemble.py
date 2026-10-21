"""Assemble docs/tests/stage8_step0_audit_2026-10-21.md from the part files written by scripts a-d (results/stage8_step0/)."""
from diag_stage8_step0_common import *

HEAD = """# Stage 7-8 step-0 audit (INV-65), 2026-10-21

Lane Z (Sonnet). Read-only empirical audit to ground the stage 7 and stage 8 pre-registrations. No model is fit, nothing gates. Training seasons only: 2021-22, 2022-23, 2023-24. 2024-25 (fold-2 holdout) was not requested from the loader at any point, 2025-26 is sealed (`NHL_UNSEAL_2025` not set). All data through `src/nhl_sim/data/load.py`. Regular season (RS) and playoffs (PO) are reported separately; any cell with fewer than 100 events is labelled UNDERPOWERED in its table.

Reproduce (about 1 minute total on the home box; no step projected near 15 minutes, so no box request):

```
.venv/Scripts/python.exe scripts/diag_stage8_step0_a_pulls.py     # items 1, 4   (46 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_b_ot_so.py     # items 2, 3   (1 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_c_reb_fo.py    # item 5       (3 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_d_gates.py     # item 6       (1 s)
.venv/Scripts/python.exe scripts/diag_stage8_step0_e_assemble.py  # this document
```

Wall clock: started 2026-10-21 13:13; compute steps 13:18 to 13:25 (part A 46 s, B/C/D under 5 s each); intermediate tables under `results/stage8_step0/` (gitignored).

## Headline numbers that constrain the stage-8 spec

| quantity | 2021-22 RS | 2022-23 RS | 2023-24 RS | note |
|---|---|---|---|---|
| tied after regulation (reg tie rate) | 21.95% | 23.02% | 20.73% | G7 targets match (section 6). PO 16.9 / 27.3 / 18.2% (UNDERPOWERED, 88-89 games) |
| tied games ending in an OT goal / in a shootout | 64.6 / 35.4% | 68.5 / 31.5% | 69.9 / 30.1% | pooled 583 OT goals, 279 shootouts (32.4%) |
| shootout share of all games | 7.77% | 7.24% | 6.25% | |
| 3v3 goals per 60 (both teams combined) | 12.2 | 12.9 | 13.2 | pooled 12.76 (495 goals, 38.8 h of exposure); per team about 6.4. Attempts 113.0 and SOG 73.4 per 60 combined |
| OT time at 3v3 | 88.5% | 83.4% | 83.7% | rest is mostly 4v3 (10%, 14.3 goals/60, 68 goals) and 4v4 (4%) after OT penalties (23-29 per 100 OT games) |
| EN goals against per game (goals into an empty net) | 0.363 | 0.334 | 0.341 | PO 0.49 / 0.28 / 0.43 (UNDERPOWERED) |
| EN goals for per game (own goalie pulled) | 0.155 | 0.155 | 0.163 | |
| pulled time per game (both teams, all pulls) | 72.6 s | 68.4 s | 72.5 s | of which 11 to 12 s is delayed-penalty pulls |
| first pull while trailing by 1, 5v5, seconds left (median, IQR) | 109 (88-134) | 113 (90-134) | 113 (92-138) | trail 2: about 175 s; trail 3+: about 250 s |
| trailing-by-1 team has pulled by 2:00 left | 99.5% | 99.8% | 100% | by 5:00 left: 88.5 / 88.4 / 88.4% |
| relief goalie appearances per 100 team-games | 7.5 | 6.2 | 6.7 | 197 / 163 / 176 appearances; about 60% when down 3 or more |
| share of SOG faced by a relief goalie | 3.20% | 2.45% | 3.10% | pooled RS 2.92% (Lane E2 fold-2 figure of 2.4% is at the low end of this range) |
| shootout per-attempt success | 30.0% | 33.7% | 29.5% | pooled 31.1% (2,034 attempts); no home/away or round-order effect detectable |
| shootouts going past round 3 | 30.4% | 34.7% | 34.1% | pooled 33%; home team shoots first in 80 to 90% |

Data limitations that bind the spec (details in the sections):

1. No actual goalie-pull record exists. Pulls are inferred from gaps in the goalie shift chart (confirmed by the pbp goalie flag in 96.4% of pulls in 2021-22 and 99.5% / 99.95% afterwards; 2021-22 has more spurious gaps). The situation-code goalie flag alone is not a usable pull record: it is observed only at events and also fires on PERIOD_END / GAME_END events (it counts 25% more team-games with a pull than the shift gaps do, mostly end-of-period events; table 1j).
2. The pbp `DELAYED_PENALTY` event is logged for only 42-62% of delayed-penalty pulls (its rate roughly doubled from 2022-23 to 2023-24); delayed-penalty pulls are identified mostly from the pull ending at an opponent penalty call.
3. Strength state in the situation code changes only at events, so OT exposure per state is bracketed (prev-event vs next-event attribution), not exact; the bracket is narrow for 3v3 (+/- 0.1 goals/60) and wide for 4v3.
4. No shootout round index in the pbp (round is derived from alternation, which holds in 100% of shootouts). Shootout misses are typed `missed-shot` / `shot-on-goal` in 2021-22 and partly `failed-shot-attempt` afterwards.
5. A per-shooter shootout model is thin: 383 distinct shooters, 154 with >= 5 attempts, 72 with >= 10 (50% of attempts), 6 with >= 20. Shooter dispersion is 1.21 times binomial; goalie dispersion 0.91 (no goalie signal).
6. The rebound proxy is recording-era sensitive: its share of unblocked attempts rises 7.2% to 8.9% to 10.2% across the three seasons while the goal rate on proxies falls 17.9% to 13.8% to 11.2% (non-rebound goal rate flat at 6.4 to 6.6%). This matches the shot-recording drift flagged in the data audit; any rebound feature needs per-season centring or a recording-era term.
7. The starter flag is post-game data. Whether a relief change is an injury or a performance pull is not recorded.

## Definitions used throughout

- Pull = a gap of at least 3 s inside a period (shootout excluded) in which a team has no goalie shift on the ice (union of that team's goalie shifts, period windows from the PERIOD_START / PERIOD_END events). Gap-length sensitivity is in 1k. A goalie change (second goalie id) shows a gap of 0 s in all but 3 cases, so it is not mistaken for a pull.
- Failure cases of the rule: (a) shifts have 1 s resolution so start / end times are +/- 1 s; (b) 2021-22 shows 3.6% unconfirmed gaps (shift-chart noise); (c) simultaneous pulls by both teams are not separated; (d) the pre-pull strength state comes from the last event with the goalie in net, which can predate a penalty that began after it; (e) the deficit counts goals at or before the pull second, so a pull at the same second as a goal is assigned the post-goal score.
- Pull end cause: a goal within 1 s of the return (goal_for / goal_against; any goal against while pulled is an empty-net goal), the period end, a stoppage / faceoff / penalty event within 1 s, or in-play return.
- Delayed-penalty (DP) pull: a `DELAYED_PENALTY` event owned by the opponent within [start - 3 s, end + 1 s], or the pull ends within 3 s of a PENALTY called on the opponent. Exception: a team trailing in the last 5:00 of P3 is treated as an EN-style pull whatever follows (about 3.6% of such pulls end at an opponent penalty call and cannot be separated).
- EN goals per game follows the G7 gate: non-shootout goals with no goalie id (goals into an empty net), both teams.

"""

SEC7 = """
## 7. Candidate constructions (no fit, no preference)

Each line is a construction the data would support and the data limitation that rules any of it out. The PM chooses; these are not recommendations.

**Goalie pull (stage 8a)**
- Empirical lookup of pull time keyed by (deficit 1 / 2 / 3+, penalty-on flag), sampling from the observed seconds-remaining distribution (1a, 1b). Support: trail1 5v5 first pulls n = 1,158 (3 seasons), trail2 783, trail3+ 200; penalty-on cells are 15 to 60 each (UNDERPOWERED). Limit: pooled across teams.
- Deterministic threshold per deficit (about 2:00 / 3:00 / 4:10) plus noise equal to the observed IQR (about 45 s for trail1). Limit: a single threshold cannot reproduce the observed spread (trail1 p10 to p90 of about 65 to 160 s); the 1d table shows trail1 teams are 88% pulled by 5:00 left and 96 to 97% by 3:00.
- Discrete-time hazard (per game second, features: deficit, seconds left, penalty-on, pulled-before flag). Score state must be the pre-event state and closed-loop gated (CBB L23/L27). Limit: team- or coach-specific pull timing has about 36 first pulls per team over three seasons (UNDERPOWERED); only league-level behaviour is identifiable.
- Re-pull after a goal against: 20 to 22% of pulls ended by a goal against are followed by another pull in the same period, median lag 14 to 18 s (1e). Construct as a separate stage-state rule or fold into the hazard model via the pulled-before flag. Limit: the shift chart has the goalie back at the goal's clock time, so 're-pull' is a new gap, not a continuous pull.
- Delayed-penalty pulls (0.65 to 0.71 per game, median 13 s, mostly P1 and P2 leading or tied) as a rider on the stage-1 penalty process: pull with probability p whenever the penalty process raises a delayed penalty. Limit: the pbp DELAYED_PENALTY event is logged for only 42 to 62% of them, so the delayed-penalty rate itself cannot be learned from that event; it must be inferred from pulls ending at an opponent penalty call, and the stage-1 penalty process has no delayed-penalty concept to hang it on.
- Empty-net scoring once pulled: (i) reuse the shot-attempt / SOG / goal cascade with EN_FOR / EN_AGAINST as strength states (the events exist: 7,975 EN_FOR and 2,426 EN_AGAINST unblocked attempts, 3 seasons); (ii) a stand-alone constant per pulled-team-minute (EN against 0.28 to 0.30 per pulled minute counting all pulled time, 0.34 to 0.37 excluding delayed-penalty pulls; EN for about 0.13); (iii) shot rate from the cascade and conversion fixed near 1.0 on SOG into an empty net (observed goal per SOG 0.9993 / 1.000). Limit: EN_FOR goals are 204 to 214 per season, and EN_AGAINST attempts are scarce for team-level responsiveness checks.

**Overtime (stage 8b)**
- 3v3 as a strength state inside the cascade with its own rate offsets (combined 113 attempts, 73 SOG, 12.8 goals per 60). Limit: only 495 3v3 goals in three seasons: any team or goalie responsiveness inside 3v3 is UNDERPOWERED, so strength must come from the 5v5 cascade parameters.
- Direct OT-goal time hazard (constant, or rising by minute: pooled 0.166, 0.209, 0.248, 0.213, 0.286 goals per minute; minutes 4 and 5 are 89 and 94 goals, UNDERPOWERED). Limit: the rise includes the survivor effect of penalty-induced PP time and cannot be separated from it at this sample size; the hazard also averages over 4v3 and 4v4 time.
- OT penalties as an extra stage-1 process in OT (23 to 29 penalties per 100 OT games, 4v3 PP at 14.3 goals per 60 on 68 goals; 4v4 after offsetting minors 6.7 per 60 on 12 goals). Limit: both are UNDERPOWERED; either reuse the regulation penalty process or accept 3v3 only with a fixed non-3v3 share (about 15%).
- Playoff OT is 5v5 continuous (periods 4+; 5v5 OT exposure 7.8k to 14.9k s per season, 319 / 542 / 353 attempts, 14 / 17 / 14 goals): reuse the regulation 5v5 cascade with no shootout; the sample (15 to 24 OT games per season) only permits a consistency check. Limit: 'ties resolve through the OT and shootout models' means PO games need no shootout branch at all.
- Home advantage in OT and SO: OT winner home share 54.7% (n = 583) and SO winner home share 50.2% (n = 279); the OT split is within about one SE of the regulation-decided home share (53 to 54%).

**Shootout (stage 8c)**
- Constant p = 0.31 per attempt with the rules mechanics (3 rounds, then sudden death; home shoots first 80 to 90%; the ordering effect is nil: first shooter 31.3%, second 30.8%). Limit: none beyond sample.
- Shooter x goalie logit with partial pooling. Limit: see data limitation 5. Shooter dispersion is 1.21 over 72 shooters, and the goalie dispersion is 0.91 over 72 goalies, so a goalie effect is not detectable. Shooter and goalie ids are present for 100% of attempts (null count 0).
- Roster-level shooter strength (use only the top three or so skaters by projected shootout use). Limit: pregame shootout shooter order is not published; the three shooters are chosen in game.

**In-game goalie change (stage 8d)**
- Per team-game Bernoulli relief (6.2 to 7.5% RS) with a score-state timing rule (57 to 60% when trailing by 3 or more; 48% of changes occur within a second of an opponent goal; 29 to 37% at a period start). Limit: the cause (performance or injury) is not recorded, and 92 to 96% of pulled starters do not return.
- Hazard on goals against while in net, applied after each goal against (closed-loop gate required). Limit: 163 to 197 events per season is enough for a league-level table only; goalie-specific rates are UNDERPOWERED.
- Fixed relief share of SOG (2.9%). Limit: wrong if the engine is later used per game, but it is the construction that stage-6 saves already see through the starter flag.

**Rebounds and faceoffs (stage 7)**
- Rebound as a post-attempt branch: after each saved SOG, with probability p(class, state) a same-team attempt follows within 3 s. Support: 19,839 proxies after a saved SOG (goal per SOG 0.192), 7,636 after a block (0.153) and 4,934 after a miss (0.170). Limit: the proxy share and goal rate shift by season (limitation 6), the 1 s clock resolution hides ordering at dt = 0 (1,972 cases, goal rate 20%), and blocked-prior proxies are not physical rebounds.
- Rebound as a feature (time since own previous attempt) inside the shot-attempt and goal-given-shot models rather than a branch. Limit: same recording drift; the shot-type field has no rebound flag.
- Faceoff win as a team-level logit (home advantage, team strength). Support is strong: team win-share SD across teams is 0.024 to 0.027 against a 0.007 to 0.008 binomial SD (ratio 3.1 to 3.7), odd / even split correlation 0.73 to 0.88, cross-season 0.55 to 0.67. Limit: player-level matchup needs on-ice centre identification (faceoff winner / loser ids are present on every faceoff), which has to come from shifts.
- Faceoff location after each stoppage kind (icing, offside, goal, penalty): counts per game are 56.5 to 56.9 (RS), 17.0 N / 20.3 home-O / 19.3 home-D, 43.5 of them at 5v5, 10.0 at 5v4. Limit: zone-by-state home-win shares (5j) mix which side holds the man advantage with home / away, so they should not be read as a causal zone effect without a power-play-team view.
"""

parts = [(OUT / "part_a.md").read_text(encoding="utf-8"), (OUT / "part_b.md").read_text(encoding="utf-8"),
         (OUT / "part_c.md").read_text(encoding="utf-8"), (OUT / "part_d.md").read_text(encoding="utf-8")]
doc = HEAD
doc += "\n## 1 and 4. Goalie pull, empty net, and in-game goalie changes (part A tables; section numbers 1x are item 1, 4x are item 4)\n" + parts[0]
doc += "\n## 2 and 3. Overtime and shootout (part B tables; 2x are item 2, 3x are item 3)\n" + parts[1]
doc += "\n## 5. Rebounds and faceoffs (part C tables)\n" + parts[2]
doc += "\n## 6. Gate targets (part D)\n" + parts[3]
doc += "\nMatch result: all 36 comparisons (reg_tie_rate, ot_rate, so_rate, en_goals_per_game x 3 seasons x all / RS / PO) agree with the gate target files to within 0.0005 (differences are exactly 0 at the printed precision). No mismatch to list. Note `ot_rate` in the gate files is the share decided in OT, excluding shootouts.\n"
doc += SEC7
(ROOT / "docs" / "tests" / "stage8_step0_audit_2026-10-21.md").write_text(doc, encoding="utf-8")
print(len(doc))
