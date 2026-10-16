# Totals lines sources: experiments (append-only)

This is not a sim model. It covers the source-validation tests for the totals closing line, which is used for CLV and the market scorecard (D10, D11, D21).

---

## LT-R1: price-adjusted totals agreement, ESPN BET vs DRatings (INV-25; pre-registered 2026-10-16 by the PM, before any run)

### Question

Once price is accounted for, do ESPN BET and the DRatings consensus imply the same probability of the over? D11 found the two choose different main lines in about 45% of games.

### Data

- Seasons 2023-24 and 2024-25, regular season and playoffs, where both sources have a closing total with prices on both sides.
- Use DRatings no-vig close and ESPN BET close.
- Sources that fail the two-way vig check (D11: sums outside a plausible band) are excluded and counted.

### Conversion to a common line

1. For each source and game, compute the no-vig P(over) at its own line. Pushes on integer lines are handled exactly: no-vig P(over | no push).
2. Bring both sources to the DRatings line L_D. If the lines differ by 0.5 or 1.0, shift with a lookup of P(T = k | consensus line = L) and P(T >= k | L). T is the final total goals as the market settles it: a shootout adds 1 to the winner (verified finals, INV-14). The lookup comes from 2021-22 + 2022-23 DRatings lines and verified finals only, so it is out-of-sample for both test seasons. Lines that differ by more than 1.0 are reported and not converted.

### Metrics and pass rule (per season; both seasons must pass)

- **Equal-line bucket (no conversion):** median |P_E - P_D| <= 0.02, and mean signed P_E - P_D within +/-0.01.
- **Converted bucket:** the same two thresholds.
- **Reported:** by month, by line value, and by line gap (0.5 / 1.0). Also report each source's calibration against outcomes: mean P(over) vs over rate, with SE, by season.
- **Consequence, fixed now:**
  - PASS: DRatings is the consensus totals CLV source, and ESPN BET is confirmed as a consistent single book at its own line.
  - FAIL: totals CLV uses DRatings alone, labelled single-source, and ESPN BET totals are graded only as their own market (D11 stays as written).

### The '-68' mean price (D11)

Explain it from the data before any of the above is read. The working hypothesis is an arithmetic mean of American prices of mixed sign (for example -110 and +100), which is not a price. If so, report the correct summary instead: the mean implied probability, or the median American price.

### Results

(append below this line)

### LT-R1 results (Lane T, run 2026-10-16 10:19; `scripts/exp_totals_agreement_v1.py`; full report `docs/tests/lines_totals_lt_r1_2026-10-16.md`)

Choices fixed before reading results: ESPN vig band 1.00-1.10; pmf conditioned on the DRatings line L_D; lookup cell needs n >= 30. '-68': mean of mixed-sign American prices (equal-line bucket n = 1,617: mean -69.6, 78% minus at -117.7, 22% plus at +104.3, median -115); mean implied probability 0.5288 (about -112).

| Season | Bucket | n | median abs diff | mean signed (SE) | Pass |
|---|---|---|---|---|---|
| 2023-24 | equal | 789 | 0.0059 | +0.0018 (0.0004) | yes |
| 2023-24 | converted | 550 | 0.0089 | -0.0022 (0.0010) | yes |
| 2024-25 | equal | 814 | 0.0061 | -0.0006 (0.0004) | yes |
| 2024-25 | converted | 577 | 0.0077 | +0.0006 (0.0006) | yes |

Outcome: **PASS** (both seasons, both buckets). Consequence per spec: DRatings is the consensus totals CLV source; ESPN BET confirmed as a consistent single book at its own line. Exclusions: 60 ESPN games without a total price (2023-24), 0 vig outliers, 7 converted games with no lookup. Underpowered: conversions into L_D = 7.0 (n = 42, mean -0.06).
