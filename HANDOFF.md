# Handoff

PM-owned. Newest block first.

## SUMMARY FOR USER 2026-10-21 (day session, 11:45-17:00, PM on Fable at your request)

**Headline:** Three stages were fixed today by one idea. The in-season effect strength (the as-of response scale from the goalie work) now carries the shot-location model (stage 4, SL-R7), the block model (stage 5, SB-R5) and the goalie, all with response ratios inside the band on the next season. The engine runs from penalties through goals with real sub-models at stages 1, 3, 4, 5 and 6; only the miss model and the empty-net levels are flat stand-ins. Stage 8 (goalie pull, overtime, shootout) is built and wired but not accepted: its gates exposed a compression of regulation margins upstream, traced to goal conversion by score state, and the goal model's repair closes part of it. That repair, and a pull-timing level, are next.

**Decisions D41-D53** (in `ARCHITECTURE_DECISIONS.md`)

| # | Decision |
|---|---|
| D41 | Engine carries the goal model C1s (box-score starter, labelled oracle goalie), the miss stand-in, and the block stand-in with own 4v4 / 3v3 groups |
| D42, D43 | SL-R7 passed. Stage 4 model L1x-as adopted (provisional). The burn-in spike of the as-of scale was listed, then fixed by a prior floor (D44) |
| D44 | The prior floor at f = 0.5 is the as-of scale's construction; incumbents unchanged in effect. Engine default set serves L1x-as and C1s |
| D45, D46 | Stage 8 part A: pull hazard P1 selected and wired. Two of my spec checks were impossible offline and moved to the closed loop. The loop failed G7: pull timing needs an in-season level, and the margin compression (INV-71) was found |
| D47, D52 | SB-R5 passed offline and in the closed loop. Block model B1a-as adopted (provisional); the B0 stand-in is retired |
| D48 | INV-71 diagnosed: trailing teams' shots convert about 8% too often relative to tied play; half from the goal model's pooled score dummies, a fifth from the block stand-in. G-R4 and a 55:00 gate (G5b) pre-registered |
| D49 | Miss score term: no effect after the tier level; closed with no change |
| D50 | Overtime 3v3 level adopted (the long-listed INV-35 cell passes). Shootout mechanics wired but not selected: my 5 pp gate was below its noise floor (L39) |
| D51 | Same defect on the goal round's by-bucket check; restated at 2 SE before the holdout was read |
| D55 | Second diagnosis: half of the remaining tie gap is a one-season deviation of 2024-25, half is period-3 goal conversion by score state (trailing over-converts, leading by one under-converts) that a score term pooled over periods cannot fix. The 55:00 gate is now read over both seasons |
| D53, D54 | Goal model C1s-sap (as-of score levels plus period terms) selected offline, but it fails its closed loop (the 55:00 tie gate and the power-play save % gate), so it does not ship. The goal model stays C1s. The block and overtime repairs are on by default. The remaining tie-share gap (about 2 points, at the one-season noise floor) goes to a second diagnosis |

**Needs you:** nothing right now. Keep Windows logged in for the loggers and the Monday 06:00 weekly pull.

**Open items, in order**
1. INV-82: pre-register the period-specific score terms (period-3 conversion by score state, tied period-2 conversion) for the goal, block and miss models, with bands sized by redraw first. Lane D2's diagnosis (D55) found the 55:00 gap is half a one-season deviation and half this defect; the 55:00 gate is now read pooled over both folds.
2. EG-R2 (INV-72): the as-of pull-timing level (2024-25 teams pulled 78 s per game vs 64-68), a re-pull lag term, the shootout past-round-3 check at 2 SE pooled, then G7 re-read.
3. INV-70: a delayed-penalty state in the engine (the offline penalty hazard has one; the engine does not). Needed for 11 s per game of pulled time.
4. INV-68 (in-game goalie changes, 2.9% of shots, needed for saves props) and INV-69 (stage 7: rebounds, faceoffs).
5. INV-73 (reconcile the loop's goalie spread with the offline response ratio), INV-76 (grader label artefact), INV-61 (live-season drift of the stage-4 "for" ratio), INV-42, INV-34, INV-12, INV-7.

**AWS:** approved for the session, $60 cap. Lane O4 served the queue for an hour; no request was filed and $0.00 was spent (every heavy step ran locally in under 10 minutes). Zero instances verified at 12:47.

**PM errors today (disclosed):** five spec defects, each caught before a result was misread: an impossible offline pulled-time check (D45), an "ES group" wording for blocks and misses at empty net (D46), and three gates set below their one-season noise floor (D50, D51, D54; now L39 and the G5b tolerance is corrected to 2 SE). Lane H8b's standalone report file could not be written by its tool; its content is in the experiments results block.

**Worker incidents (disclosed, none harmful):** Lane A7 and Lane E3 each stopped only their own processes after checking command lines. Lane E2's wrapper script exited non-zero after all work had finished. Every push printed the Windows credential-manager "Key not valid" warning and every push was verified with `git ls-remote`.

## SUMMARY FOR USER 2026-10-16 (day session, 09:20-14:10)

**Headline:** The cascade now runs end to end in the engine. Stages 1, 3 and 6 have provisional models: penalties, shot attempts, and the goal model with goalie talent. Stages 4, 5a and 5b run on labelled flat stand-ins. The day's main finding: team and goalie rating effects fade season to season, so any effect strength fixed from past seasons over-reacts next season. An as-of (in-season) effect strength now fixes this for goalies, and stage 4 gets one more round with it.

**Decisions D18-D40** (in `ARCHITECTURE_DECISIONS.md`)

| # | Decision |
|---|---|
| D18 | Stage 1 re-levelled: H3''-LC2 + T2. INV-29 is closed, so team power-play ratings are unblocked |
| D19-D20 | Stage 3: A3g-c is the provisional model. 3v3 moves to the overtime model (stage 8) |
| D21, D25 | DRatings puck-line sign flagged, not repaired. Suspect games are excluded, and a near pick'em sensitivity is reported |
| D22 | Totals sources agree. DRatings is the consensus closing total |
| D23 | Blocks are decided before location. Block coordinates mark the block point, not the shot origin |
| D24-D31 | Stage 4: five rounds. Location drifts across recording eras. A tree model's size can't set the response strength. The stop rule went to you |
| D32 (you) | The response check is a slope across rating tenths. Stand-ins are allowed in the engine |
| D33 | Stages 1 and 3 pass the new check. Stage 3 over-reacts by about 15%, within the band, and is on watch |
| D34, D37 | Block and miss team effects parked. Their flat stand-ins carry the stage |
| D35, D38 | PM errors, caught and fixed. The era level could pass its own check by construction. Overtime rows were leaking regulation score effects |
| D36, D40 (you) | Goal model C1s adopted, using the in-season goalie effect strength |
| D39, D40 (you) | Stage 4 gets one more round (SL-R7), using the in-season effect strength |

**Needs you:** nothing right now. Keep Windows logged in for the live loggers. The weekly pull runs on Mondays at 06:00.

**Open items, in order**
1. INV-59, SL-R7. Pre-register it first thing, then give it to an Opus worker.
2. INV-60, one engine lane:
   - wire the C1s goal model in place of the goal stub;
   - move the L0s stand-in level to M1 K500 (INV-57);
   - give the B0 stand-in its own 4v4 and 3v3 groups (INV-54);
   - add the S0t miss stand-in;
   - run the plumbing loop.
3. INV-53, next applications: blocks, then the stage-3 over-response.
4. INV-42 (stage-3 4v4 hazard) and INV-34 (seasonal profile shape).
5. INV-12: retry the Kalshi fee schedule.
6. Stage 7 (rebounds, faceoffs) and stage 8 (goalie pull, OT, shootout; includes INV-35), after INV-60.

**AWS:** $0 spent today, and no instances exist.

**Worker incidents (disclosed, none harmful)**
- Lane G briefly printed fold-2 numbers in an intermediate document, and fixed it within a minute. No choice depended on it.
- Lane M ran a stray `python3` Store stub, which hung its own shell. It stopped only that process.
- Lane B left a stray empty shell, and stopped it itself.
- PM:
  - two spec errors (D28, D35) and one reasoning error (D27, corrected in D29);
  - a board-row edit slip, fixed in f80f961;
  - two shell heredoc parse failures, after which nothing was written.

## SUMMARY FOR USER 2026-10-15 (evening session, 18:40-22:40)

**Headline:** P2 is under way. The engine core is built, and stage 1 (penalties / strength state) is a provisional incumbent: H3'' (a LightGBM penalty hazard) plus the T2 type model. Stage 3 (shot attempts) has a leading arm, A3g, that passes its core checks; two thin strength states, 4v4 and 3v3, still fail. A PM spec error in the league-level construction was found and fixed for attempts (D16).

**Decisions this session**

| # | Decision |
|---|---|
| D12 | SS-R1 is not confirmed. Its G1 pass came from two biases cancelling (season-level drift +10%, delayed penalties -6%) |
| D13 | SS-R2 fixed the delayed-penalty state, but every arm failed the bias checks (January +11%) |
| D14 | SS-R3 added a season-phase profile. H3'' was accepted with the January 2025 bias listed, conditional on a clean G1 |
| D15 | G1 passed CLEAN, so H3'' is the provisional stage-1 incumbent. Team PP use is blocked by INV-29 (the sim over-responds to team ratings) |
| D16 | PM spec error: a league level expressed as a ratio to last season is biased under a trend. LC-1 (an absolute level) replaces it |
| D17 | SA-R2: A3g leads stage 3, but G2 fails at 4v4/3v3. LC-1 fails its parity check for penalties, so stage 1 stays on the old level, with that listed |

Also this session:
- SS-R4: the team ratings are fine.
- SS-R5: the type model T2 replaces T1. It cuts the team-PP over-response by about 2/3, but the drawn-rating spread ratio of 1.25 still fails the 0.8-1.2 band.
- The rules changed at your request: Opus workers are used where the work needs them, with no daily cap. AWS goes through an operator lane (Lane O), and any step projected over 15 min files a box request.

**Needs you**
- Stay logged in to Windows tonight. The DRatings pull (`NHL-Model-dratings-pull`) should finish around midnight, then build its table and unregister itself. The live loggers also need you logged in.

**Open items, in order**
1. INV-32, SA-R3: fix the 4v4/3v3 attempt hazard, merge the T2 engine sibling into `sim.py` behind a flag, and re-run G2 on H3''+T2.
2. INV-33: LC-2 penalty level. Run the parity check first, then re-run SS-R3c and re-measure INV-29.
3. INV-24 close-out: commit the final `lines_dratings_v1.parquet`, push raw to HF, and decide on the 38 SBRO-vs-DRatings puck-line sign mismatches. Then INV-25.
4. INV-16 (weekly pull schedule) and INV-21 (Control R2), both deferred.

**AWS:** the operator chain is built and was smoke-tested on a c7i.large (pytest in 93 s from launch). No requests came in tonight, because every run finished locally in about 17 min or less. Spend was $0.004 of the $60 cap, and zero instances are running (checked 21:51 and by the PM at 21:42). See `docs/ops/aws_operator_O_2026-10-15.md`.

**Worker incidents (disclosed)**
- Lane I stopped Lane H's replay diagnostic (PID 15152) without checking its command line. The replay was re-run by Lane P, and the reported numbers were confirmed exactly (99.993% / 98.134%). A process-control rule is now in the worker rules.
- Lane H4 ran a projected 17-min job locally instead of filing a box request. It cost nothing, and the rule is now "file before launching".
- PM: a spec error in SS-R2's level definition (D16), caught by Lane S.
- Several pushes printed "fatal: Key not valid for use in specified state" (a Windows credential-manager warning). Every push was verified with `git ls-remote`.


## SUMMARY FOR USER 2026-10-15 (end of session)

**Headline:** P0 is done and P1 has its yardstick. 7,100 games are ingested, audited and independently verified, live goalie and market logging is scheduled, and the Control yardstick is set (A0, D9). Next is the P2 event engine.

**Decisions this session**

| # | Decision |
|---|---|
| D1-D2 | CBB methodology; Opus PM, no Fable workers |
| D3 | Event-level engine with a Control yardstick |
| D4, D7 | Lines venues are Kalshi, DKeX and historical closes; no paid odds yet |
| D5 | GitHub, HF `mvpeav/nhl-sim-data`, AWS with a $60 cap per session |
| D6 | NHL API stays primary, for personal research only |
| D8 | Forward loggers; backtests labelled "oracle goalie" |
| D9 | Control A0 is the yardstick; the gates it fails are the event engine's bar |

**Late-session add (16:47-17:20):** deep lines hunt (F1/F2 Sonnet, F3 Opus). Free open/close lines now exist for every season (D10). The ESPN core 2023-25 ingest is done (D11). The ML cross-check vs DRatings passes; totals differ by ESPN BET's choice of main line, so DRatings is the consensus total source.

**Needs you**
- Keep Windows logged in during game days so `NHL-Model-live-log` runs (09:00-23:30, every 30 min).
- Later, for INV-19: decide on a fold-2 (2024-25) closing-line source once the market scorecard matters.

**Open items, in order**
1. INV-22: P2 kickoff in a FRESH PM session. Spec GameState and the strength-state/penalty sub-model, with an Opus worker for the engine core.
2. INV-24: full DRatings + SBRO pulls, run unattended (about 70 min/season), then INV-25.
3. INV-16: schedule the weekly resumable `pull_games.py`, which re-tries the shift-chart gaps.
4. INV-21: Control R2 (deferred).

**Worker incidents (disclosed)**
- Lane A: one audit run hung (missing `__main__` guard); the worker killed only its own process tree. The blocked-shot owner was mis-assigned at first and rebuilt before the audit.
- Lane D: the first ESPN launch got 403 (User-Agent); the worker stopped only its own processes and cached nothing.
- Lane E: the A4 arm blew up numerically on the first fold-2 pass. The repair was chosen on fold 1 before any fold-2 scores existed, and it is disclosed in the R1 doc.
- PM: two worker-written User-Agent strings contained the user's email and were sent to NHL API, Daily Faceoff, Kalshi and DKeX for about 1.5 hours. Removed; the string is generic now. The old string remains in git history (private repo).

## (earlier, superseded) SUMMARY FOR USER 2026-10-15

**Headline:** NHL-Model scaffolded with the CBB rules (Opus PM, no Fable). Two P0 lanes running: data ingest/audit and lines-source audit.

**Done with you**
- GitHub remote `cmpeavlerjr72/NHL-model` connected, pushed and verified.
- HF dataset `mvpeav/nhl-sim-data` created (private); AWS approved, $60/session cap confirmed.

**Needs you**
- Possibly a fresh DraftKings Predictions HAR capture (Lane B will say which pages).

**Open items, in order**
1. Lane A report -> PM reviews audit, writes gate reference / Control engine specs.
2. Lane B report -> PM decides lines sources (D4 follow-up).

**Worker incidents (disclosed)**
- PM (2026-10-15): two worker-written User-Agent strings contained the user's email and were sent to NHL API, Daily Faceoff, Kalshi and DKeX for about 1.5 hours. Removed; the string is generic now. The old string remains in git history (private repo).
