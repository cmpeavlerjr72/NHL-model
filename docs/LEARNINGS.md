# Learnings

PM-owned, append-only. Each entry ends with "For the sim:". Entries L1-L12 are imported from the sister projects; NHL-native entries start at L13.

- **L1 (CBB L2) League-mean drift.** Rating scales drift season to season. For the sim: centre every rating on its own snapshot's league mean.
- **L2 (CBB L3/L10) Shared game latent.** Independent team draws make SD(margin) = SD(total). For the sim: both teams share a game-level latent (pace/event rate); check score correlation in G5.
- **L3 (CBB L23/L27) Score-state feedback.** A post-event score feature tripled margin variance in a closed loop. For the sim: pre-event state only, and a closed-loop gate for any engine-fed feature.
- **L4 (CBB L32/L44/L45) Train/serve skew.** For the sim: every retrain passes a parity stage proving the served feature equals the trained feature.
- **L5 (CBB L22) Silent zero fills.** For the sim: feature builders raise on a missing column; never fill 0.
- **L6 (CBB L41) Binary features.** For the sim: feed a 0/1 tree feature as a draw, never as a probability.
- **L7 (CBB L38) Shrinkage compresses spread.** For the sim: compare prediction SD to realised SD, not just MAE.
- **L8 (CFB INV-45) Leaks look like edges.** Beat close 64% with zero CLV was a post-game feature joined one period off. For the sim: leak test every external feed; presume leaked any edge without CLV.
- **L9 (CFB) Settle at the posted line.** De-vigged fair lines created phantom pushes on 45% of sides. For the sim: grade at the posted book line.
- **L10 (CFB/CBB) Verified finals only.** pbp-accumulated scores were corrupt; 54 unplayed games slipped into a graded set. For the sim: two-source verified finals table.
- **L11 (CFB) Sample weights can be colliders.** Drive-proportional weights inflated INT 2.1x. For the sim: no event-count-proportional sample weights on per-event models without a check.
- **L12 (CBB L43) Workers misjudge time.** For the sim (process): every brief requires reading the clock from `Get-Date` and never ending a turn with a job running.
- **L13 NHL event recording drift.** Giveaways 15.6 -> 29.9/game and takeaways 14.0 -> 9.5 between 2023-24 and 2024-25 (recording change); SOG 57.6 -> 47.9/game while goals hold 6.1-6.4 and attempts 114-127 (blocks and misses up). For the sim: shot-type and discretionary-event rates are season-specific; league-mean centring per snapshot is mandatory, and pooled-season targets are banned in gates.
- **L14 Coordinates flip by period.** Raw x follows `homeTeamDefendingSide`, which flips every period. For the sim: use `x_norm/y_norm` / `sx, sy` from the events table, never raw x/y.
- **L15 Blocked-shot zone is the blocker's.** BLOCK events are owned by the shooting team, coordinates in the shooter's frame, but `zoneCode` is relative to the blocking team. For the sim: never use `zone` for blocks.
- **L16 Goalie GA excludes empty-net goals.** For the sim: goalie save props and goalie talent use GA ex-EN; game totals include EN goals.
- **L17 NHL scores are negatively correlated and over-tied.** 2024-25: home/away score correlation -0.115 and a 20.8% regulation-tie rate. Team-rate Poisson gives -0.04 and 15.9%, and the positive-dependence families (bivariate Poisson, shared gamma latent) cannot represent negative dependence at all (their fits hit the bound). The cause is game-state behaviour: score effects, play late in tied games, and empty-net goals. For the sim: the event engine has to produce these from pre-event game state (score effects in shot generation, a goalie-pull model, and late-tie behaviour). G5 correlation and G7 regulation-tie rate are the gates that catch it.
- **L18 Odds feeds mix pregame and in-game prices.** ESPN core `/odds` returns an "ESPN Bet - Live Odds" item beside the pregame one (e.g. BUF -3000 in-game). For the sim: every lines ingester whitelists the pregame provider and fails if it can't tell which item is pregame. A "close" taken from a live item would fabricate CLV.
- **L19 Historical "as-of" pages can be rebuilt from current data.** Daily Faceoff date pages for 2022 show today's goalies and team names (Lane F3). For the sim: a third-party historical page is never treated as pregame-known until a spot-check against known facts passes.
- **L20 Delayed penalties cause goalie pulls.** About 80% of penalties recorded with a goalie pulled follow a delayed-penalty signal. The penalty causes the pull, not the reverse. For the sim: a penalty's pre-event state is the state at the signal, or a sim that never pulls loses about 6% of penalties.
- **L21 A season dummy cannot extrapolate.** 2024-25 had 8% fewer penalties than 2023-24, and a last-training-season dummy over-predicted every arm by 10% (SS-R1). For the sim: league levels drift (L1, L13), so rate models carry an as-of in-season league level, not a season indicator.
- **L22 Penalty rates are seasonal within a season.** October runs high and January low (SS-R2: January +11% in every arm), and a season-to-date level inherits October's excess. For the sim: as-of league levels need a de-seasonalised exposure or a season-phase term, and bias is checked by month, not only overall.
