# Lane K: Kalshi fee schedule for NHL markets (INV-12)

Author: Lane K (Haiku worker). Date: 2026-10-16. Scope: read-only public lookups. No login, no account or order endpoint touched.
Request pacing: at most one request every 2 s to any Kalshi host. Rate-limit handling: see section 0.

## Summary

| Item | Status |
|---|---|
| 1. Taker formula, coefficient, rounding, cap | **UNVERIFIED** against primary source. The fee PDF was 429 on every attempt. Secondary search-engine summary only (section 1). |
| 2. Maker fee for `quadratic_with_maker_fees` | Maker multiplier **0.25 of the standard rate** is stated in the official API schema text. Coefficient and maker rounding are **UNVERIFIED** from the PDF. |
| 3. `fee_type` / `fee_multiplier` for every KXNHL series | **VERIFIED** from the public `/series` endpoint (70 series, table below). |
| 4. Fee change dates in past 18 months | **No KXNHL series or event fee change found** in `/series/fee_changes` and `/events/fee_changes` (show_historical=true). History returned only goes back to 2025-10-04, so the full 18-month window is **not fully covered**. |

## 0. Access log

- Kalshi PDF `https://kalshi.com/docs/kalshi-fee-schedule.pdf`: HTTP 429 (text/html) on every attempt. Attempts at approx 14:21, 14:23:24, 14:25:27, after a 5 min backoff (~14:30 scheduled, run 14:28 and 14:29:42 UTC re-checks). Three backoffs (30 s, 2 min, 5 min) were used, then the fallback pages.
- `https://kalshi.com/fee-schedule` (linked from the changelog): 429.
- Fallback pages used, all 200: `https://docs.kalshi.com/getting_started/fee_rounding` (14:21 UTC), `https://docs.kalshi.com/llms.txt`, `https://docs.kalshi.com/llms-full.txt` (fetched 2026-10-16, ~14:25 UTC), `https://help.kalshi.com/trading/fees` (help article dated April 19, 2026), `https://api.elections.kalshi.com/trade-api/v2/series?category=Sports` (3,994 series, no cursor), `.../series/fee_changes?show_historical=true`, `.../events/fee_changes?show_historical=true`.
- Official API reference pages (fetched as .md): `docs.kalshi.com/api-reference/exchange/get-series-fee-changes.md`, `.../market/get-series-list.md`, `.../events/get-event-fee-changes.md`.
- Raw responses were held in the Windows temp directory and not committed.

## 1. Taker fee formula (item 1), UNVERIFIED

- Primary source for the formula is the fee PDF, which could not be read.
- Help center (https://help.kalshi.com/trading/fees) states the complete Fee Schedule and "the math behind the fees" are at the bottom of the Kalshi website. It gives no formula.
- Secondary only: a WebSearch summary (not a primary page) reported the PDF as taker = round-up(0.07 x C x P x (1-P)) with P in dollars, rounded up to the next cent, and maker = 0.0175 in place of 0.07. This matches the coefficient in `docs/ops/lines_sources_audit_2026-10-15.md` line 42 but has **not** been confirmed from the PDF. Do not use it as a verified input.
- Conflict to resolve: the official `fee_rounding` page (below) describes the trade fee as ceil to $0.000001, not to the cent. The two cannot both be right for every fill. A PDF read is required.
- Cap: none found in any fetched page. UNVERIFIED.

## 1b. Rounding (official, VERIFIED from `fee_rounding` page, retrieved 2026-10-16 ~14:21 UTC)

- trade_fee = ceil to $0.000001 of the model fee.
- Rounding fee brings balance to the user's precision (direct member $0.0001; non-direct member $0.01), carried in an accumulator per order.
- Rebate in increments of target precision, capped so net fee >= 0.
- Net fee = trade fee + rounding fee - rebate.
- Worked example on the page: $0.00363825 model fee becomes $0.003639 trade fee, and the balance moves -$0.06 for a -$0.055 revenue buy, so trade + rounding = $0.005.

## 2. Maker fee (item 2)

- API schema for `FeeType` (get-series-list and get-series-fee-changes): `quadratic_with_maker_fees` uses the General Trading Fees table with the maker-fee section. `quadratic_with_combo_maker_fees` is "the same maker-fee structure with a 0.5 maker multiplier instead of 0.25". So the standard maker multiplier is 0.25. This is from the official schema text.
- Changelog (llms-full, entry dated August 22, 2026): "The maker fee uses a fee multiplier of 0.5, rather than the standard 0.25" for combo trades under the quoter swap. The same entry says maker fees were scheduled to be enabled at 5:00 AM ET, August 20, 2026, and the quoter fee swap at 11:59 PM, August 21, 2026. Whether those went live as scheduled is not confirmed here.
- Coefficient for the maker term relative to the taker formula, and maker rounding: UNVERIFIED (PDF needed).

## 3. KXNHL series fee fields (item 3), VERIFIED

Source: `GET https://api.elections.kalshi.com/trade-api/v2/series?category=Sports&include_product_metadata=true`, retrieved 2026-10-16 ~14:24 UTC. Filter: ticker starts with KXNHL. 70 series.
Counts: 65 `quadratic`, 5 `quadratic_with_maker_fees`. All 70 have `fee_multiplier = 1`.

Maker-fee series: KXNHL, KXNHLWEST, KXNHLEAST, KXNHLSERIES, KXNHLGAME.

| ticker | fee_type | fee_multiplier | title |
|---|---|---|---|
| KXNHL | quadratic_with_maker_fees | 1 | Stanley Cup |
| KXNHL1P | quadratic | 1 | NHL 1st Period Winner |
| KXNHL1PBTTS | quadratic | 1 | NHL Both Teams to Score in 1st Period |
| KXNHL1PSPREAD | quadratic | 1 | 1st Period Spread |
| KXNHL1PTOTAL | quadratic | 1 | NHL 1st Period Total |
| KXNHL1STTEAM | quadratic | 1 | All NHL First Team |
| KXNHL2OT | quadratic | 1 | NHL Double Overtime |
| KXNHL2P | quadratic | 1 | NHL 2nd Period Winner |
| KXNHL2PBTTS | quadratic | 1 | NHL Both Teams to Score in 2nd Period |
| KXNHL2PSPREAD | quadratic | 1 | 2nd Period Spread |
| KXNHL2PTOTAL | quadratic | 1 | 2nd Period Total |
| KXNHL30COMEBACK | quadratic | 1 | NHL 3-0 Series Comeback |
| KXNHL3P | quadratic | 1 | NHL 3rd Period Winner |
| KXNHL3PBTTS | quadratic | 1 | NHL Both Teams to Score in 3rd Period |
| KXNHL3PSPREAD | quadratic | 1 | NHL 3rd Period Spread |
| KXNHL3PTOTAL | quadratic | 1 | 3rd Period Total |
| KXNHL4NATIONS | quadratic | 1 | 4 nations face off |
| KXNHLADAMS | quadratic | 1 | NHL Jack Adams Award |
| KXNHLANYGOAL | quadratic | 1 | Pro Hockey Goalscorer |
| KXNHLAST | quadratic | 1 | Pro Hockey Assists |
| KXNHLATLANTIC | quadratic | 1 | NHL Atlantic Division Winner |
| KXNHLCALDER | quadratic | 1 | NHL Calder Memorial Trophy |
| KXNHLCENTRAL | quadratic | 1 | NHL Central Division Winner |
| KXNHLDRAFTPICK | quadratic | 1 | Pro Hockey Draft Pick |
| KXNHLDRAFTTOP | quadratic | 1 | Pro Hockey Top Pick |
| KXNHLEAST | quadratic_with_maker_fees | 1 | Eastern Conference Championship |
| KXNHLEXPANSION | quadratic | 1 | NHL Expansion |
| KXNHLF10G | quadratic | 1 | NHL Goal in First 10 Minutes |
| KXNHLFINALSEXACT | quadratic | 1 | NHL Championship Series Score |
| KXNHLFIRSTGOAL | quadratic | 1 | NHL First Goal |
| KXNHLGAME | quadratic_with_maker_fees | 1 | NHL Game |
| KXNHLGOAL | quadratic | 1 | NHL Goalscorer |
| KXNHLHART | quadratic | 1 | NHL Hart Memorial Trophy |
| KXNHLLINDSAY | quadratic | 1 | NHL Ted Lindsay Winner |
| KXNHLMETROPOLITAN | quadratic | 1 | NHL Metropolitan Division Winner |
| KXNHLMVP | quadratic | 1 | NHL Hart Memorial Trophy Winner |
| KXNHLNEXTGM | quadratic | 1 | Next NHL GM |
| KXNHLNEXTTEAM | quadratic | 1 | NHL Next Team |
| KXNHLNORRIS | quadratic | 1 | NHL James Norris Memorial Trophy |
| KXNHLOT | quadratic | 1 | NHL Overtime |
| KXNHLOVERTIME | quadratic | 1 | NHL Overtime |
| KXNHLPACIFIC | quadratic | 1 | NHL Pacific Division Winner |
| KXNHLPLAYOFF | quadratic | 1 | Playoff Qualifier |
| KXNHLPLAYOFFGOALS | quadratic | 1 | NHL Playoffs Goal Leader (by Round) |
| KXNHLPRES | quadratic | 1 | NHL President's Trophy Winner |
| KXNHLPSEASONGOALS | quadratic | 1 | Player Goals Scored in Season |
| KXNHLPTS | quadratic | 1 | Pro Hockey Points |
| KXNHLRECORDWORST | quadratic | 1 | Worst NHL Record |
| KXNHLRETIRE | quadratic | 1 | NHL Retire |
| KXNHLRICHARD | quadratic | 1 | NHL Maurice "Rocket" Richard Trophy |
| KXNHLROSS | quadratic | 1 | NHL Art Ross Trophy |
| KXNHLSAVE | quadratic | 1 | Goaltender Saves |
| KXNHLSAVES | quadratic | 1 | Pro Hockey Saves |
| KXNHLSEASONGOALS | quadratic | 1 | Player to score X Goals in Season |
| KXNHLSEASONPPTS | quadratic | 1 | Season Player Points |
| KXNHLSEASONPTS | quadratic | 1 | NHL Season Point Totals |
| KXNHLSERIES | quadratic_with_maker_fees | 1 | NHL Series Winner |
| KXNHLSERIESGAMES | quadratic | 1 | NHL Series Total Games |
| KXNHLSERIESOT | quadratic | 1 | NHL Series Overtime |
| KXNHLSERIESSCORE | quadratic | 1 | NHL Series Exact Score |
| KXNHLSERIESSPREAD | quadratic | 1 | NHL Series Game Spread |
| KXNHLSERIESTOTALGOAL | quadratic | 1 | NHL Series Total Goals |
| KXNHLSERIESTOTALGOALS | quadratic | 1 | NHL Series Total Goals |
| KXNHLSPREAD | quadratic | 1 | NHL Spread |
| KXNHLTEAMTOTAL | quadratic | 1 | NHL Team Goals Scored During Game |
| KXNHLTOTAL | quadratic | 1 | NHL Total Goals |
| KXNHLVEZINA | quadratic | 1 | NHL Vezina Trophy |
| KXNHLWEST | quadratic_with_maker_fees | 1 | Western Conference Champion |
| KXNHLWINS | quadratic | 1 | NHL wins |
| KXNHLWSTREAK | quadratic | 1 | Longest NHL win streak in regular season |

Note: `KXNHLGAME` (the moneyline/game series the sim targets) is `quadratic_with_maker_fees`, multiplier 1. The `category=Sports` query returned no cursor; completeness of the KXNHL filter is therefore taken from that single response (3,994 sports series). A search outside the Sports category was not run.

## 4. Fee change dates (item 4)

- `GET /series/fee_changes?show_historical=true` (retrieved 2026-10-16 ~14:24 UTC): 107 entries, scheduled_ts from 2025-10-04 to 2026-09-03. Types: 64 quadratic_with_maker_fees, 39 quadratic, 4 quadratic_with_combo_maker_fees. **Zero** entries with an NHL series ticker.
- `GET /events/fee_changes?show_historical=true`: 22 event overrides, none on NHL events.
- The endpoint's history begins 2025-10-04. Changes earlier than that (back to 2025-04, the 18-month window) are not visible here. **Not verified** for 2025-04 to 2025-10-04.
- Changelog dates in the 18-month window relevant to fees: Sep 21, 2025 (fee_changes endpoint added); Oct 1, 2025 (fee_changes returns user-facing names); Mar 3, 2026 (fee rounding docs); May 28, 2026 (balance precision for direct members); August 2026 (maker fee enablement, combo quoter swap, which affects combo markets only). None are documented as changing KXNHL* series fee types.

## Open items (UNVERIFIED)

1. Taker coefficient (0.07?), rounding granularity (per-order cent vs $0.000001), cap. Needs the PDF at https://kalshi.com/docs/kalshi-fee-schedule.pdf when the rate limit clears, or the fee-schedule page.
2. Maker coefficient and maker rounding for `quadratic_with_maker_fees`.
3. Fee history before 2025-10-04.
4. Whether any NHL series sits outside `category=Sports`.

## Proposed correction for docs/ops/data_sources.md (not applied)

Kalshi fees: per-series `fee_type` (quadratic / quadratic_with_maker_fees, fee_multiplier 1 for all 70 KXNHL series, verified 2026-10-16) from `GET /series`; trade fee rounds up to $0.000001 per fill (fee_rounding page); taker/maker coefficients from kalshi-fee-schedule.pdf still UNVERIFIED (429 on 2026-10-16), and the audit's 0.07*P*(1-P) stays unconfirmed.

## Attribution note

The brief asked for an Opus attribution line. The harness attribution for this lane is Claude Haiku 5.5, which is the model that ran this lane, so the commit uses that line.
