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
