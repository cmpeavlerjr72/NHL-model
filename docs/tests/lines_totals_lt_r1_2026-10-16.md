# LT-R1 / INV-25: price-adjusted totals agreement, ESPN BET vs DRatings

Run 2026-10-16 10:19:52-10:19:53 -04:00 (home box, 1 s). Script `scripts/exp_totals_agreement_v1.py`; outputs `results/lt_r1/` (gitignored: `step1_minus68.json`, `lookup_pmf.csv`, `agreement_rows.csv`, `breakdowns.csv`, `calibration.csv`, `summary.json`). Spec `docs/models/lines_totals/experiments.md` LT-R1, applied as written. No network. Data: `lines_dratings_v1` (`novig_close` rows), `lines_espn_core_v1` (provider 58, close), `data/reference/verified_finals_v2` (SO winner already +1: all 364 SO games have |margin| 1, so T = home + away).

Choices the spec left open, fixed before the results were read: ESPN two-way vig band 1.00-1.10 (the D11 band); lookup pmf conditioned on the DRatings line L_D (the "consensus line"; conditioning on L_E reported as a sensitivity only); a lookup cell needs n >= 30 games to be converted into (otherwise "converted_no_lookup", counted).

## 1. The '-68'
Arithmetic mean of ESPN BET over prices (American) in the equal-line bucket, 2023-24 + 2024-25 full data: n = 1,617, mean -69.6 (the cross-check's -68 on 112 games is the same quantity). It is a mean of mixed-sign prices: 78.4% are minus money (mean -117.7), 21.6% are plus money (mean +104.3). The median price is -115. The correct summary is the mean implied probability 0.5288, i.e. about -112. Companion buckets: ESPN line 0.5 lower, n = 480, mean -131.8, all minus; ESPN 0.5 higher, n = 655, mean +101.3 (96% plus), mean implied 0.4797 (about +108). The hypothesis is confirmed.

## 2. Exclusions
| | 2023-24 | 2024-25 |
|---|---|---|
| DRatings games with a verified final | 1,400 | 1,397 |
| ESPN BET total or a price missing | 60 | 0 |
| ESPN two-way vig outside 1.00-1.10 | 0 | 0 |
| ESPN over/under lines differ | 0 | 0 |
| Gap > 1.0 | 0 | 0 |
| Converted, no lookup (L_D cell n < 30: 5.0, 7.5) | 1 | 6 |

Lookup (2021-22 + 2022-23, DRatings close line, n games): 5.0: 14, 5.5: 637, 6.0: 1,054, 6.5: 1,003, 7.0: 92, 7.5: 1 (`lookup_pmf.csv`).

## 3. Agreement (P_E at L_D minus P_D)
| Season | Bucket | n | median abs | mean signed (SE) | Pass |
|---|---|---|---|---|---|
| 2023-24 | equal | 789 | 0.0059 | +0.0018 (0.0004) | yes |
| 2023-24 | converted | 550 | 0.0089 | -0.0022 (0.0010) | yes |
| 2024-25 | equal | 814 | 0.0061 | -0.0006 (0.0004) | yes |
| 2024-25 | converted | 577 | 0.0077 | +0.0006 (0.0006) | yes |

Thresholds: median <= 0.02, |mean| <= 0.01. **Pass rule met in both seasons: PASS.** Sensitivity (pmf conditioned on L_E): converted medians 0.0078 / 0.0075, means -0.0001 / -0.0009; same verdict.

Gap breakdown, converted bucket (mean signed): 2023-24 gap -0.5: -0.0139 (n 206), +0.5: +0.0048 (n 343); 2024-25 gap -0.5: -0.0013 (n 271), +0.5: +0.0024 (n 305); gap +-1.0: n = 1 per season, not interpretable. The 2023-24 gap -0.5 mean exceeds 0.01 as a sub-bucket; it is driven by conversions into L_D = 7.0 (n = 39 in 2023-24, 3 in 2024-25: mean -0.058 / -0.089, lookup n = 92, underpowered, not a finding). Excluding the 7.0 cell the converted mean is +0.0020 / +0.0011 and the 2023-24 gap -0.5 mean is -0.0015. No threshold was set for sub-buckets. By line value (equal bucket) 5.5 and 6.5 medians are 0.005-0.006 in both seasons. By month, converted medians run 0.006-0.011 with no month above 0.02 (months with n < 20: May-June, underpowered; Oct-Dec and Apr-May 2024-25 behave like the rest). Full tables in `breakdowns.csv`.

## 4. Calibration against outcomes (mean no-vig P(over | no push) vs over rate among non-pushes; SE binomial)
| Season | Source | n | mean P | over rate | z |
|---|---|---|---|---|---|
| 2023-24 | DRatings @L_D | 1,335 | 0.5068 | 0.4906 | 1.18 |
| 2023-24 | ESPN BET @L_E | 1,340 | 0.5036 | 0.4873 | 1.19 |
| 2023-24 | ESPN converted @L_D | 1,274 | 0.5071 | 0.4914 | 1.13 |
| 2024-25 | DRatings @L_D | 1,324 | 0.5013 | 0.4909 | 0.75 |
| 2024-25 | ESPN BET @L_E | 1,397 | 0.4996 | 0.4860 | 1.02 |
| 2024-25 | ESPN converted @L_D | 1,318 | 0.5010 | 0.4894 | 0.84 |

SE about 0.014 per cell, so none is distinguishable from calibrated; both sources sit 0.01-0.016 above the over rate in both seasons (same sign, within noise; would need more seasons to say anything about an over bias).

## 5. Consequence (fixed in the spec)
PASS: DRatings is the consensus totals CLV source, and ESPN BET is confirmed as a consistent single book at its own line. D11's restriction (ESPN BET totals are not "the" consensus line) stays true as a statement about line choice.

## Caveats
Pass covers the two test seasons only; the lookup is empirical and thin for L_D = 5.0 and 7.0 (7.0 conversions are underpowered); "DRatings no-vig close" is a derived field whose prices are rounded to integer American odds (sum of implied = 1 in all games). 2023-24: 60 games without an ESPN BET total are excluded (not imputed).

Proposed PM text: D-entry "INV-25 closed: PASS in both seasons (medians 0.006-0.009, means within +-0.0022); '-68' was a mean of mixed-sign American prices (correct summary: mean implied 0.529, about -112)."
