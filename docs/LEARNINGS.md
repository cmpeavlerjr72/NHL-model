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
