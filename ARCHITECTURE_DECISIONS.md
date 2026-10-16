# Architecture decisions

PM-owned, append-only. Each decision: date, decision, reason, evidence, status.

## D1 (2026-10-15): Methodology inherited from CBB-clean-sheet

Decision: adopt the CBB-clean-sheet rules (bake-offs, no hand tuning, bottom-up cascade, multi-level evidence, honest backtests, worker discipline) for the NHL project.
Reason: user instruction; those rules were written from the CFB-Monte and CBB-Monte postmortems.
Status: ADOPTED.

## D2 (2026-10-15): PM is Opus 5.5; no Fable workers

Decision: the PM runs on Opus 5.5. Workers run on Opus (engine core, at most 1 per day), Sonnet (pipelines, graders, audits) or Haiku (lookups). No agent uses Fable. Every Agent call names its model explicitly.
Reason: user rule 2026-10-15, weekly Fable allowance nearly exhausted. Revisit only on the user's word.
Status: ADOPTED.

## D3 (2026-10-15): Event-level engine with a Control yardstick

Decision: the served engine will be an event-level Monte Carlo (FRAMEWORK_PLAN section 1); a team-rate Control engine is built first as its yardstick. Every sub-model inside it is chosen by bake-off.
Reason: player props need deployment and usage inside simulated game states; the Control engine guards against complexity that does not pay.
Status: ADOPTED (shape only; components OPEN).

## D4 (2026-10-15): Lines venues

Decision: grade against Kalshi, DKeX and historical closing lines (source TBD by audit). Read-only; no agent places orders.
Reason: user answer 2026-10-15.
Status: ADOPTED; historical source OPEN.

## D5 (2026-10-15): Hosting and compute

Decision: GitHub `cmpeavlerjr72/NHL-model` (main); private HF dataset `mvpeav/nhl-sim-data` for bulk data; AWS spot compute approved, operator-lane only, per-session spend cap $60 (user-confirmed).
Reason: user approval 2026-10-15.
Status: ADOPTED.

## D6 (2026-10-15): NHL API stays primary, personal-use posture

Decision: keep `api-web.nhle.com` / `api.nhle.com/stats` as the primary source despite NHL.com's site terms barring scraping (no published terms for the stats API; Lane B audit). Personal research only: polite rate, disk cache, never re-fetched, never redistributed (the HF dataset stays private).
Reason: user decision 2026-10-15.
Status: ADOPTED; risk recorded in `docs/ops/data_sources.md`.

## D7 (2026-10-15): No paid historical odds yet

Decision: do not buy The Odds API now. Backtests grade on accuracy first; free ESPN pickcenter and Kalshi `/historical` are used wherever they cover. Revisit once the Control engine exists.
Reason: user decision 2026-10-15; CLAUDE.md accuracy-first phase.
Status: ADOPTED.

## D8 (2026-10-15): Forward logging, and "oracle goalie" backtests

Decision: scheduled read-only loggers capture Daily Faceoff goalie status (with fetched_at), Kalshi NHL market snapshots and DKeX NHL board snapshots from today forward. 2021-26 backtests use box-score starters and are labelled "oracle goalie" (no bulk pregame goalie history exists).
Reason: Lane B audit; user approved scheduled tasks 2026-10-15.
Status: ADOPTED.

## D9 (2026-10-15): Control R1 ruling: A0 is the yardstick

Decision: A0 (independent Poisson, as-of ridge ratings, unpenalised home term, no goalie term) is the yardstick. No richer arm beat it beyond the noise floor on fold 2 (all diffs vs A0 have 95% intervals spanning 0). Under the R1 decision rule it is adopted with its gate failures listed as the bar the event engine must clear:

| Gate | Control A0 (fold 2) | Actual 2024-25 |
|---|---|---|
| G5 total SD ratio | 1.082 | 0.95-1.05 band |
| G5 home/away score correlation | -0.036 | -0.115 |
| G5 P(total=4) | off 1.99 pp | - |
| G7 regulation-tie rate | 15.9% | 20.8% |
| G6/G9 home win | 52.8% | 56.5% |

A4 is the variant repaired after a numerical blow-up on the first fold-2 pass. The repair was chosen on fold 1 and no fold-2 scores were computed before it, and it is disclosed in `docs/tests/control_r1_2026-10-15.md`. It did not win either way.
Reason: `docs/tests/control_r1_2026-10-15.md`, commits d2ed7fa..56ff992.
Status: ADOPTED (yardstick). Control R2 (extend edge-hit grids; a dependence family allowing negative correlation and excess ties) is DEFERRED (INV-21). The event engine is the priority.

## D10 (2026-10-15): Historical lines sources (resolves INV-19)

Decision, for each season (all free, read-only, polite crawl):

| Season | Primary | Second source (cross-check / multi-book) |
|---|---|---|
| 2021-22, 2022-23 | SportsbookReviewsOnline season HTML (consensus open/close ML and total, close PL) | DRatings per-game pages (open + 10-book close) |
| 2023-24 | ESPN core API `/odds` (9-12 books, open/close ML) | DRatings |
| 2024-25 (fold 2) | ESPN core API `/odds`, ESPN BET pregame item only (open/close ML, PL, total) | DRatings (open + 10-book close incl. Circa, South Point) |
| 2025-26 (sealed) | ESPN core / ESPN site pickcenter (DK open+close) | free `minmaxxxer/nhl-closing-odds-2025-26` |

- ESPN core returns a second "ESPN Bet - Live Odds" item holding in-game prices. Ingest keeps ONLY the pregame provider item and fails if it is ambiguous.
- Not used, because terms or robots forbid them: SBR live pages (ToS bans bots), Action Network API (robots Disallow /), OddsPortal.
- Sign-up options are recorded for the user and are not needed now: OddsPapi free key (timestamped ticks, depth unknown), API-Sports.
- Before any ROI is read, the primary and second sources must agree within tolerance on overlapping games (L10-style two-source verification).

Reason: Lane F1/F2/F3 hunt, `docs/ops/lines_hunt_F{1,2,3}_2026-10-15.md` (2a28c22, e3d1190, ece8f09). PM spot-check: ESPN core sample 2025-01-15 shows ML open -170/+145, close -185/+155, total 6.5 -> 5.5.
Status: ADOPTED. Supersedes the "no free 2024-25 source" finding in INV-19. D7 (no paid odds) stands.

## D11 (2026-10-15): Ruling on the ESPN core ingest and the DRatings cross-check (INV-23)

The pre-set cross-check (`docs/tests/lines_crosscheck_espn_dratings_2026-10-15.md`, 112 games of 2024-25) returned:

- **Moneyline close: PASS.** Median no-vig difference 0.0057, max 0.027. ESPN BET moneyline open and close is the primary 2024-25 and 2023-24 moneyline source.
- **Puck line: consistent.** 96.4% identical lines. Use ESPN BET.
- **Total line: FAIL**, and the result stands as recorded. Only 54.5% of lines are identical, and every miss is exactly 0.5 goal, with ESPN BET's price moving to match (over priced around -131 when its line is 0.5 lower, around +109 when 0.5 higher). ESPN BET chooses a different main total than the 10-book consensus; it is not a data error. Ruling:
  - ESPN BET totals are graded only as their own market, at their posted line and price (L9). They are never used as "the" consensus total line, and never for CLV against another book's line.
  - The consensus total line for 2024-25 comes from the full DRatings pull (INV-24).
  - A price-adjusted agreement test (no-vig P(over) at a common line) is pre-registered as INV-25 before any total CLV is read. The "-68" mean over price in the equal-line bucket is not a valid American price and must be explained in INV-25.
- **2023-24 non-ESPN-BET books:** Bet365, Titanbets, Unibet and DraftKings close moneylines (and some Betfair, SugarHouse and PointsBet rows) have both sides at plus money (sums 0.80-0.98). Their close equals current, and they are incoherent as two-way moneylines. They are excluded (`close_ml_vig_ok=False`). The usable multi-book 2023-24 moneyline consensus is about 4 book families.
- Two 2023-24 playoff games have no pregame item. They are excluded from market grading.

Status: ADOPTED. Evidence: 55f86d6.

## D12 (2026-10-15): SS-R1 ruling; strength-state stays TESTING, SS-R2 pre-registered

Lane H (1b3abfe) built the GameState engine core (rulebook penalty mechanics; the replay agrees with pbp on 99.993% of seconds, gap-aware) and ran SS-R1.

- The literal rule picks H3 (LightGBM hazard) and T1. H3 beats H2 by +0.42 log-lik/game (13 SE).
- H3's G1 PP-opportunity pass is compensated: season-level drift is +10%, missing delayed-penalty states are about -6%, and the regular-season cell fails. Under the bottom-up rule that is not a pass, so no arm ships.
- SS-R2 is pre-registered in `docs/models/strength_state/experiments.md`. It moves the pre-event state to the delayed-penalty signal, adds an as-of in-season league level, and extends the rating grid. It also adds pre-registered bias checks, and its G1 is split by regular season vs playoffs.
- The gap-aware replay measure binds the 99% bar; the strict measure is always reported.

Reason: `docs/tests/strength_state_ss_r1_2026-10-15.md`.
Status: ADOPTED. SS-R2 runs on the next day's Opus slot (INV-26).

## D13 (2026-10-15): SS-R2 ruling; SS-R3 seasonality profile pre-registered

SS-R2 (9b14319) removed the delayed-penalty artefact. Goalie-pulled penalty rows fell from 6.36% to 1.54%, and that artefact accounted for 0.27 of H3's 0.42-nat lead over H2. H3' still wins offline. Every arm fails the pre-registered bias checks (January +11%, about 4 SE; H3' +3.08% overall), so G1 was not run. strength_state stays TESTING.

- The cause is within-season seasonality, which a season-to-date level cannot see. SS-R3 adds a training-only season-phase profile and a de-seasonalised level.
- Forking-paths guard: the SS-R3 checks are also reported on fold 1, and no SS-R4 is pre-authorised.
- SS-R3 goes to Sonnet. It re-runs the existing pipeline with one added offset, and needs no Opus judgement (CLAUDE.md fit-for-purpose rule).

Reason: `docs/tests/strength_state_ss_r2_2026-10-15.md`. Status: ADOPTED (INV-27).

## D14 (2026-10-15): SS-R3 ruling: H3'' accepted with its listed bias, conditional on a clean G1

SS-R3 (f1e6399) results:

- The season-phase profile fixed the overall level (H3'' +1.45%, against its SS-R2 twin's +3.08%) and removed the fold-1 monthly bias.
- Fold-2 January 2025 still fails narrowly in every arm (+8.3% to +9.0%, limit +/-8%, monthly SE about 2.6%). That dip is specific to 2024-25 and cannot be predicted from pregame information.

Decision, using the D13 option:

- H3'' plus T1 is the stage-1 arm, with the January bias listed. The acceptance is final only when closed-loop G1 passes its regular-season cells cleanly (a decomposition shows no offsetting biases). H2'' runs as the comparator.
- There is no SS-R4. Per-month penalty bias joins the live monitoring list.

Reason: `docs/tests/strength_state_ss_r3_2026-10-15.md`. Status: ADOPTED (INV-28).

## D15 (2026-10-15): Stage 1 (strength state) provisional incumbent: H3'' + T1

The closed-loop G1 (b513691) passes the regular-season cells, with a CLEAN decomposition (H3'' PP opportunities 2.625 vs 2.564; no component near the 0.15 tolerance).

Decision:

- H3'' (LightGBM penalty hazard, with the in-season level and the season-phase profile) plus T1 is the provisional stage-1 incumbent. Stage 3 builds on its timeline.
- Open defect INV-29: the sim's response to team penalty ratings is about 1.5-1.8x the actual quintile spread. Until a pre-registered fix passes, no team-level penalty or PP-opportunity quantity is used for markets or props.
- Monitoring items are listed in the strength_state experiments ruling.

Reason: `docs/tests/strength_state_g1_ssr3_2026-10-15.md`. Status: ADOPTED.

## D16 (2026-10-15): League-level construction defect (PM spec error); LC-1 replaces it in every stage

SA-R1 (d379f58, c9542c8) found that the in-season league level the PM specified in SS-R2 is biased under any trend. It is a ratio to the previous season, entered as a fixed offset over cells pooled across training seasons. The cells absorb the mean of the earlier seasons' rates, so test predictions are off by the gap between that mean and last season's rate. This gave about -5% on attempts. Fold-1 evidence: a fixed reference moves A0 from -2.03% to +0.22%.

- LC-1 (absolute as-of de-seasonalised level, coefficient 1, with a per-training-season parity test) replaces it everywhere.
- SA-R2 re-runs stage 3 with LC-1 and adds strength-group level arms, for the fold-1 PK drift.
- SS-R3c re-levels the stage-1 incumbent. D15 stays in force until SS-R3c rules. Any G1 result produced on the old level (incl. SS-R5) is re-checked under LC-1 before it lifts a block.

Reason: `docs/tests/shot_attempt_sa_r1_2026-10-15.md`. Status: ADOPTED.

## D17 (2026-10-15): SA-R2 and SS-R3c rulings

- **SA-R2 (e1abf1e).** A3g (LightGBM with separate ES/PP/PK as-of levels) is the leading stage-3 arm. It passes every fold-2 bias check, the responsiveness band, and the core G2 cells, CLEAN. 4v4 (+4.2%) and 3v3 (+6.6%) attempts per 60 fail G2, and they gate as written. shot_attempt stays TESTING, with SA-R3 (4v4/3v3 fix, G2 on H3''+T2) next.
- **SS-R3c.** It stopped at the LC-1 parity test on the penalty level (about +/-2%). The parity test binds on the level-only arm. LC-1 passes for attempts and fails for penalties, because penalty seasonality is strong. Stage 1 stays on its old level under D15, with the D16 defect listed. LC-2 for penalties is next.

Reason: `docs/tests/shot_attempt_sa_r2_2026-10-15.md`, `docs/tests/strength_state_ss_r3c_2026-10-15.md`. Status: ADOPTED.

## D18 (2026-10-16): LC-2 ruling; stage 1 re-levelled to H3''-LC2 + T2; INV-29 closed

- **Parity.** No construction passes the 0.5% line on the genuine-prior seasons. The pre-registered fallback took L2b (14-day half-life discounted ratio estimator), max |parity| 0.93% (fold-2 train 2023-24), mean +0.13% / +0.29%. The pre-registration said a parity miss is listed, not blocking, and gave the reason before any number existed. That stands: the failure is listed, not waived after the fact.
- **Adoption.** H3''-LC2 + T2 meets the SS-R3c rule as written: fold-2 bias checks pass (overall +1.56%; January 2025 +7.6%, down from +8.8%, still listed), LL vs H3'' -0.0015 (SE 0.0023), G1 RS PASS and CLEAN. It replaces H3'' + T2 as the stage-1 incumbent, CONFIRMED-INCUMBENT (provisional). The D16 level defect is closed for stage 1.
- **INV-29 closes.** The closed-loop spread ratios are 1.10 / 1.11 (RS taken / drawn) and 1.13 / 1.19 (all games), all inside [0.8, 1.2]. The gate binds on the point estimate both ways: that is how 1.25 failed it (SS-R5 ruling), and it is how 1.19 passes. The team-PP block from D15 is lifted. 1.19 sits near the edge, so it is a live-season monitoring item.
- **Profile defect is a separate item (INV-34), not a blocker.** With the oracle level, the fold-1 test months run -7.5% (October) and +7.8% (April), inside the +/-8% month line but near it. The 14-day memory partly absorbs that profile error. The level is causal and gates passed, so this is not a post-hoc compensation, but the bottom-up rule says the profile is the responsible sub-model. INV-34 is pre-registered later. It is not pre-authorised now.
- **Stage 3.** SA-R3's G2 (Lane S3) runs on the old-level H3'' + T2, the incumbent at its launch, and rules on that. A G2 confirmation on H3''-LC2 + T2 rides with the next stage-3 step. No mid-task change to Lane S3.

Reason: `docs/tests/strength_state_lc2_2026-10-16.md` (3a17280). Status: ADOPTED.

## D19 (2026-10-16): SA-R3 ruling; 3v3 attempts re-scoped to the stage-8 OT model; A3g-c leads stage 3

- **Result.** No arm meets the SA-R3 rule. Every arm fails 3v3 on fold 2 (+4.2% to +6.8%, cell SE about 2.3%, tolerance 3%). The cause is diagnosed: A3g's 3v3 rate rides the shared even-strength level. 5v5 rose across seasons while 3v3 fell, so the test season inherits about +6%. In-sample cells (the c arms) cannot fix out-of-sample drift. A3g-s gives 3v3 its own level and halves the fold-1 miss, but it fails the D13 guard on 4v4, and its 3v3 level is noisy at about 25 team-hours a season.
- **Re-scope, not relaxation.** Regular-season 3v3 is overtime only, and overtime belongs to stage 8 (clock and end-game: OT, shootout, goalie pull) in the bottom-up order. The 3v3 attempt hazard moves there as INV-35. It gates at stage 8 (G2 3v3 cell plus G7), and stage 8 cannot be accepted without it. The stage-3 G2 3v3 cell is reported and listed until then, never dropped. The reason is ownership, stated with the evidence above, not that the cell is close to its line.
- **Stage-3 leader: A3g-c** (b_c = 50, a grid corner, listed). Among the arms that pass every check except 3v3, it is the simplest one that is not worse than A3g by > 2 SE (A2g-c is worse by 7 SE). LL vs A3g is +0.001, inside the 0.0015 floor; A3g itself fails 4v4 offline. It passes 4v4 (+1.5%) and the D13 guard.
- **Condition for CONFIRMED-INCUMBENT (provisional).** G2 for A3g-c on the current stage-1 incumbent H3''-LC2 + T2 (D18), 200 seeds: every G2 cell except 3v3 PASS and CLEAN, and 4v4 passes closed-loop. INV-36.
- **T2 merge** (`sim.py` `per_team_types`, default off, bit-identical both ways) is accepted; `sim_ss_r5.py` is superseded.

Reason: `docs/tests/shot_attempt_sa_r3_2026-10-16.md` (3b68b8f). Status: ADOPTED.

## D20 (2026-10-16): stage 3 incumbent A3g-c (INV-36)

The D19 condition is met. G2 for A3g-c on H3''-LC2 + T2 (200 seeds, b7fb015) passes every non-3v3 cell in the regular season: 5v5 +0.35%, PP -0.49%, PK -2.14%, 4v4 +2.82%, attempts per team-game -0.94%, score buckets. The decompositions are CLEAN, responsiveness passes (1.135 / 1.122), and every status is the same at 100 and 200 seeds. The stage-1 path is bit-identical to Lane L2's G1. shot_attempt becomes **CONFIRMED-INCUMBENT (provisional): A3g-c**.

Listed:
- 3v3 +5.25% (INV-35, gates at stage 8).
- 4v4 sits 0.18 pt inside its line. The components share a sign, so there is no compensation; it is a live-season monitoring item.
- b_c = 50 is a grid corner.
- Playoff PK per-state decomposition 14.63 vs 13.32 per 60 (UNDERPOWERED).
- The EN pair (-1.69 / +0.97) is re-checked at stage 8.

Reason: `docs/tests/shot_attempt_g2_inv36_2026-10-16.md`. Status: ADOPTED.

## D21 (2026-10-16): INV-24 close-out; DRatings puck-line sign is flagged, not repaired

- **INV-24 closes.** `lines_dratings_v1.parquet` validates: 5,598 games, all of them NHL game_ids; nothing on or after 2025-07-01; the UTA->ARI remap covers 246 games. One game is missing: 2024020984. Raw is on HF (45d2b04, cbc164c).
- **Puck-line sign.** Of the 38 SBRO-vs-DRatings sign mismatches, SBRO's puck-line sign matches its own moneyline favourite in 34 cases and DRatings' in 6. The two sources' moneylines agree on the favourite in 36 of 38. So the DRatings puck-line sign field (the mode across books) is the suspect field.
- **Ruling:**
  - A v2 table flags every DRatings game whose puck-line favourite differs from its own no-vig ML favourite (`pl_sign_suspect`), over all 5,598 games, not just the SBRO overlap.
  - Flagged games are excluded from puck-line grading and CLV.
  - The sign is not inferred or rewritten. Settling at a line we reconstructed would grade against a price nobody posted.
  - ML and totals are unaffected.
- The flag is built by Lane O3 as INV-38.

Status: ADOPTED.

## D22 (2026-10-16): LT-R1 / INV-25 PASS; DRatings is the consensus totals CLV source

- **Agreement.** The price-adjusted totals test passes in both seasons. Median |P_E - P_D| is 0.006-0.009, and every mean signed difference is within +/-0.0022 (thresholds 0.02 / 0.01). Under the pre-set consequence:
  - DRatings no-vig close is the consensus totals CLV source for 2021-25.
  - ESPN BET is a consistent single book at its own line.
  - D11's "never as the consensus line" stands for ESPN BET.
- **The '-68'** was an arithmetic mean of mixed-sign American prices, not a price. The correct summary is a mean implied probability of 0.529, about -112.
- **Listed.**
  - Converting into a DRatings line of 7.0 is underpowered: lookup n = 92, and the 2023-24 0.5-below sub-bucket mean is -0.014. Totals CLV in games at a 7.0 line is reported separately until a larger lookup exists.
  - The worker fixed three open choices before reading results, and disclosed them: vig band 1.00-1.10, lookup conditioned on the DRatings line, minimum cell 30. They are accepted.
  - Both sources run 0.01-0.016 above the observed over rate. That is not significant (z 0.75-1.19), and it is a monitoring item for the market scorecard.

Reason: `docs/tests/lines_totals_lt_r1_2026-10-16.md` (470a1a4). Status: ADOPTED.

## D23 (2026-10-16): SL-R1 ruling; Fenwick cascade order; mix drift is a level problem; xG_ref stays fixed

- **Blocks rule (b) applies (pre-registered).** Block coordinates are block points: defencemen's blocked attempts sit at a median of 26 ft against 51-53 ft unblocked, and type is recorded on 0% of blocks. The cascade order is now: attempt -> blocked? -> (unblocked) location x type -> SOG / miss -> goal. The block decision is the front of stage 5 and may not use location. FRAMEWORK_PLAN item 4/5 order is updated to match.
- **No SL-R1 arm is eligible.** Every arm over-predicts xG_ref per unblocked attempt on 2024-25 by +3.9% and the high-danger share by +1.7 pp. The cause is a drift in the recorded mix: the ES high-danger share went 14.5 / 14.8 / 12.75 / 12.2%, with a step at the 2023-24 boundary (October 2023 already 12.3%). Goals per unblocked attempt barely moved, 0.0627 to 0.0602. This is L27 for a mix: no arm had a league-level mix term.
- **Tuning deviation, accepted with a label.** The spec said the L24 spread ratio is reported per grid cell. The worker excluded out-of-band cells instead (w = 0.7, b = 1,000 rather than the LL-best w = 1.0, b = 300, which sits at 1.214). The LL gap is 0.00007 nats per attempt and no arm was eligible anyway. SL-R2 pre-registers the exclusion rule explicitly.
- **xG_ref stays fixed per fold, not season-levelled.** It is a fixed weighting that summarises the mix. Levelling it by season would hide exactly the mix error it exists to measure. The fact that goals did not fall with the mix is stage 6's problem: goal-given-location will need its own as-of conversion level, and stage 4's mix level and stage 6's conversion level each pass their own parity test. A closed-loop goals gate (G4 / G6) then checks the pair for compensation. If the location shift is a recording change, a per-cell conversion from training rows would under-predict goals by roughly what a non-levelled mix over-predicts. That is a compensating pair, banned by the bottom-up rule.
- **Venue arm dropped.** The arena factor stopped carrying over (season-to-season correlation 0.62, then 0.10), and the L0 arena slope is indistinguishable from 0, so the SL-R1 ratio gate is unreadable. Arena residuals stay reported only.
- **Next: SL-R2,** pre-registered in `docs/models/shot_attribute/experiments.md`.

Reason: `docs/tests/shot_attribute_sl_r1_2026-10-16.md` (436da19). Status: ADOPTED.

## D24 (2026-10-16): SL-R2 ruling; era level E kept with a GameState flag; L0m is not adoptable; SL-R3 = baseline-started booster

- **The level works.** It is worth +0.87 nats/game over L0 (z 24), 92% of the oracle's gain. No as-of construction passes parity; the oracle passes. The fallback took E, the recording-era intercept. Kept, with two caveats listed:
  - for fold 2, E's judged parity is in-sample, because era 2 is only 2023-24;
  - fold 1 cannot test it.

  The era flag goes into GameState (CLAUDE.md: rule-era flags live in GameState). The era boundary 2023-24 is fixed now. Any later boundary needs its own evidence, and is not fitted.
- **No arm is eligible.**
  - L0m passes every bias check (xG +1.97%), but it is flat by construction. The matchup-specific rule forbids a flat incumbent, so L0m cannot be adopted.
  - L1m fails PK (+3.2%) and over-responds (1.69), the same over-response as SL-R1. The GLM rating terms stay unproven.
  - L3m fails PP tier shares and EN-for, and it is already off on its own training rows. The diagnosis is a construction defect: a booster started from the pooled, ES-dominated mix and stopped at 35 rounds. That is not a data finding.
- **SL-R3** is pre-registered as a single construction fix: L3b, a booster started from the levelled L0m distribution. It is not a new search.
- **L0m as a plumbing run.** SL-R3 also runs L0m through the closed loop as a labelled plumbing check of the Fenwick order and the block-first stub, not as a gate. That way the engine path is proven whatever L3b does.

Reason: `docs/tests/shot_attribute_sl_r2_2026-10-16.md` (9b86012). Status: ADOPTED.

## D25 (2026-10-16): INV-38 closed; puck-line grading excludes suspect games, with an ambiguous-excluded sensitivity

`lines_dratings_v2.parquet` (2e5e4e4) flags 91 close-suspect and 182 close-ambiguous games out of 5,598, with separate open-line flags. The close and open sets overlap in only 8 games, so each graded line uses its own flag.

- **Primary.** Exclude suspect games (D21).
- **Pick'em games.** An ambiguous game (no-vig ML within 0.5 pp of 50%) can legitimately have either side at -1.5, so its flag is not evidence of an error. But 9 of the 38 known mismatches sit there, so every puck-line scorecard also reports a sensitivity with ambiguous games excluded too (273 games, 4.9%).
- **Sign-flip rule.** A puck-line result that flips sign between the two versions is not reported as an edge.

Status: ADOPTED.

## D26 (2026-10-16): SL-R3 ruling; EN rows get the baseline only; 4v4 / 3v3 get their own location baseline; stage-3 4v4 reopened

- **Era flag accepted.** GameState carries the recording era (boundary 2023-24, D24). With the stage-4 option off, output is bit-identical to HEAD; 162 tests pass.
- **L3b stopped correctly** at the in-sample check. EN-for is -0.87% against the 0.5% limit, while ES / PP / PK are within 0.42%. Cause: score and clock deviations learned on ES (late, trailing shots run 7-9% lower xG) leak onto EN-for rows, which are all late and trailing. Nothing on fold 2 was read.
- **SL-R4 is pre-registered as two construction fixes, nothing else:**
  - EN-for and EN-against rows are served the L0m baseline with no tree deviations. EN-for cannot be reached in the sim before the stage-8 goalie pull, and its mix is flat on L0m.
  - 4v4 and 3v3 get their own baseline strata. The L0m plumbing loop showed that pooling them with 5v5 gives 4v4 / 3v3 xG -11% / -6%.

  This is the fourth stage-4 respec, so the D13 forking-paths guard applies: the fold-1 bias checks must pass as well as fold 2.
- **Noise floor.** The baseline-started booster is deterministic: its seed-2 retrain is bit-identical. The floor is 0, labelled, as for the SS-R5 convex fits, and the 2 SE bootstrap criterion carries the decision.
- **Stage-3 4v4 reopened (INV-42).** Under the L0m plumbing loop's goal stub, regular-season G2 4v4 attempts per 60 moved from +2.82% to +3.08%, a marginal FAIL at 200 seeds (PASS at 100). The shift comes through score states, from the stub goal model, not from the location model. But the cell sat 0.18 pt from its line (D20), so it now fails. The fix belongs to stage 3, the 4v4 hazard's own level (as A3g-s did offline at -0.5%). It is pre-registered separately. Until then, the stage-4 gate's G2 re-check reports 4v4 as listed under INV-42 and 3v3 under INV-35, and gates every other cell.

Reason: `docs/tests/shot_attribute_sl_r3_2026-10-16.md` (9d92d31). Status: ADOPTED.

## D27 (2026-10-16): SB-R1 ruling; rating over-response is cross-cutting; shrinkage strength is tuned for calibrated spread, not likelihood

- **SB-R1 (d18a694).** Level M1 (K = 500) passes parity (0.22-0.28 pp; the oracle 0.01). E fails here, because blocks drift within era 1. The level is essential: without it, fold-2 block share is off by -2.2 pp. Every bias check passes for B0, B1 and B2. No arm is eligible:
  - B0 is flat.
  - B1 (1.59 / 1.49) and B2 (1.38 / 1.43) over-respond in ES on fold 2.
  - Fold-1 B1 was in band (0.83 / 1.18), so the fold-1 band did not transfer.
- **Cross-cutting pattern.** As-of team ratings over-respond out of sample in three stages: penalties (INV-29, before LC-2), stage-4 L1 (1.64), and blocks (1.4-1.6). In every case the fold-1 likelihood surface over the shrinkage grid is flat (about 1e-4 nats per row). So likelihood cannot choose the prior strength, and the grids topped out at 3,000. A rating that over-responds out of sample is under-shrunk: it assumes more persistence of team differences than exists.
- **Rule from now on, for every as-of team rating** (adopted here, applied prospectively; not retro-applied to incumbents that passed their bands):
  - The shrinkage grid extends to a 30x range ending at least 10x past the old top.
  - The cell is chosen on fold 1 as the one whose ES spread ratios (for and against) are closest to 1 in |log ratio|, among cells whose fold-1 LL is within 2 SE of the best cell.
  - Likelihood alone never picks the prior strength.
- **SB-R2** applies this rule to B1 and B2. Nothing else changes.

Reason: `docs/tests/block_sb_r1_2026-10-16.md`. Status: ADOPTED.
