# Sim Guardrails: NHL gates and debugging philosophy

Created 2026-10-15. Companion to `cfb-props-sim/docs/SIM_GUARDRAILS.md` and `CBB-clean-sheet/docs/SIM_GUARDRAILS.md`, whose core principle applies verbatim here.

**Core principle (non-negotiable):** post-hoc multipliers, caps, clips, calibration curves, or blends applied to engine output defeat the purpose of having models. If a sub-model produces biased output, fix the sub-model. The gates below exist so we detect bias at the right level, and the first response to a failed gate is "which sub-model is producing the wrong distribution", never "what adjustment closes the gap".

---

## 1. Inherited cautionary inventory

- **CFB-Monte (2024):** stacked magic multipliers (1.35x red-zone TD, 0.85/0.95 caps) and goal-line clipping produced unders on ~95% of bets.
- **CBB-Monte (2025-26):** absences, not patches: no league centring on a drifting rating scale, no home court, no shared pace, no fitted dispersion; margin distribution twice too wide; a post-hoc win-probability calibration curve on the tournament fork.
- **cfb-props-sim (2026):** sim margins 1.6x over-dispersed vs reality; a leaked pregame feature (INV-45) that beat the close 64% with zero CLV; grading against de-vigged lines created phantom pushes.

## 2. Reference targets

Targets are not typed into this document. They are built per season by `scripts/build_gate_reference.py` into `data/reference/gate_targets_{season}.parquet` from verified data, because several move year over year (scoring, PP opportunities, shot volume). The first data audit fills a summary table here.

## 3. Gates

Every gate is evaluated on a held-out season and at every level listed. Tolerances in `docs/gates.yaml` are provisional until the seed-noise study replaces them with measured paired standard errors; until then a miss is a miss. A gate report is one section per gate with target, sim, actual, delta, and a literal PASS / FAIL / UNDERPOWERED / NEEDS-INSTRUMENTATION status, written by `scripts/eval_gates.py`.

| Gate | Quantity | Levels | Failure points at |
|---|---|---|---|
| G1 | Time on ice by strength state per game (5v5, PP, PK, 4v4, 3v3, EN); penalties and PP opportunities per team-game | overall, by team, by referee era/season | penalty / strength-state process |
| G2 | Shot attempts per 60 (Corsi), unblocked (Fenwick), and shots on goal per 60 | by strength state, by team (for/against), by score state | shot-generation model |
| G3 | Shot quality: location/type mix, expected goals per shot | by strength state, by team | shot-location / type model |
| G4 | Goal given shot on goal: Sv% and goals vs xG | by goalie quintile x shooter quintile cell, by strength state, by danger zone | goal model, goalie talent prior |
| G5 | Dispersion: total-goals distribution P(total=k) for k=0..10+, margin distribution, SD ratios (each with its accuracy and dispersion components reported separately), correlation of the two team scores, PIT histogram | overall, by favourite band | shared game latent, dispersion of shot/goal models |
| G6 | Home ice: home win %, home goal differential, same games | overall, by season | home feature wiring |
| G7 | End game: regulation tie rate, OT win split, shootout rate, empty-net goals per game, goalie-pull timing, period scoring shares | overall, by trailing margin | goalie-pull model, OT 3v3 model, shootout model |
| G8 | Player layer: TOI per player by role (F1-F4 lines, D1-D3 pairs, PP1/PP2, PK) mean and SD; share of team SOG by top-1 and top-3 shooters; per-player SOG / points / goalie saves distribution tails | by role, by team, by final-margin band | deployment model, usage allocation, player rate shrinkage |
| G9 | Accuracy: ML Brier and calibration by decile; total-goals and margin bias; puck-line cover calibration | overall, by month, by goalie-confirmation status | aggregate symptom; check G1-G8 first |
| G10 | Market scorecard where lines exist: Brier vs de-vigged market, ROI by edge bucket at posted odds, CLV sign agreement | by market, by venue, by season | report only; LEAK-SUSPECT if surprise corr > 0.15 and CLV agreement < 0.53 |

Meta-gates (always on):

- `created_at < puck_drop` on every backtest row, enforced by the artifact writer.
- Every external feature passes `scripts/leak_test_pregame_features.py` (|change-form corr| <= 0.15) before entering a feature table.
- Grading truth is verified against a second source (NHL API boxscore vs schedule/standings final vs pbp-accumulated) before any gate is read. Truncated or corrupt pbp feeds are excluded from pbp-derived targets, never patched.
- The 2025-26 season is sealed in code until selection on the earlier folds is complete.
- Minimum seed count for any ROI or gate read is set by the seed-noise study, not assumed.

---

## 4. Known risks to watch (NHL-specific)

- **Starting goalie.** The single largest pregame input, often confirmed late. Backtests must use the pregame-known goalie or be labelled oracle. Live runs need a confirmation feed and a re-run trigger.
- **Score effects.** Trailing teams out-shoot leaders. Modelled via pre-event score state only; any engine-fed state requires a closed-loop gate.
- **Empty-net goals and goalie pull.** Decide puck lines and totals; G7 is broken out by trailing margin and time remaining.
- **Integer outcomes.** Totals at 5.5 / 6.5 and the -1.5 puck line are sensitive to the whole total-goals distribution, not its mean; G5 checks P(total=k) cell by cell.
- **Two-team correlation.** Getting total variance right while the score correlation is wrong is the CFB INV-56 failure; G5 checks correlation separately.
- **Allocation under a correct total.** Team totals right while the favourite/underdog split is wrong (CFB INV-141). G6 and G9 favourite bands check the split.
- **Deployment.** Line combinations change nightly; PP unit membership drives points props far more than even-strength usage. G8 breaks out PP units.
- **Event vocabulary / coordinate drift.** NHL API event types, coordinate conventions (rink side by period) and shift-chart coverage must be audited per season with a test that fails on an unknown type.
- **Back-to-backs and travel.** Affect both skaters and the goalie choice (backup starts).

---

## 5. When gates fail

Do: trace the metric to the responsible sub-model; check that model's calibration on its own holdout; check the feature pipeline is delivering the right inputs at sim time; check the distribution shape, not just the mean; check whether the "bias" is actually the profitable side of a market inefficiency before chasing it to zero.

Don't: apply a multiplier; cap or clip a probability; add a conditional boost for hard cases; stack adjustments for different reasons onto one quantity; fit a calibration curve on the output; blend toward the market. If a model's architecture cannot represent the correct conditional distribution, rebuild the model.

A paired-loop veto fires when a line flips PASS -> FAIL, or when a failing line moves further from target beyond both noise floors (multi-draw seed floor and paired game bootstrap).

---

## 6. Revision log

- 2026-10-15: created from the CFB and CBB guardrails. Gates and tolerances provisional pending the first data audit.
