# Lane K brief: INV-12, verify the Kalshi fee schedule for NHL markets

Model: Haiku. No sub-agents. Read-only web lookups only: no login, no account endpoint, no order. At most 1 request every 2 seconds to any Kalshi host. If the fee PDF returns 429 again, back off (30 s, 2 min, 5 min) at most 3 times, then use other public Kalshi pages (help centre, fee schedule page, rulebook, the API's series `fee_type` / `fee_multiplier` fields).
Rules: `CLAUDE.md` and `docs/ops/worker_rules_2026-10-16.md`. Context: `docs/ops/lines_sources_audit_2026-10-15.md` (line 42: `quadratic` vs `quadratic_with_maker_fees`; 0.07*P*(1-P) taker, unverified).
Commit attribution line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

Find out, with the source URL and retrieval time for each:
1. The current taker fee formula and coefficient for `quadratic` series, the rounding rule (per order, rounded up to the cent?), and any cap.
2. The maker fee for `quadratic_with_maker_fees` series (KXNHLGAME).
3. The `fee_type` and `fee_multiplier` (or equivalent) fields for every `KXNHL*` game/prop series from the public `/series` endpoint, as a table.
4. Any change date in the past 18 months, so historical backtests use the fee in force at the time.

Write `docs/ops/kalshi_fees_K_2026-10-16.md`. Propose (do not apply) a one-line correction for `docs/ops/data_sources.md`. Commit only your doc; push; verify with `git ls-remote`. Message to the PM: under 250 words. Say plainly what stayed UNVERIFIED.
