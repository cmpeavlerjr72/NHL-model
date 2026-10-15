# Gate report: control_r1_A0_fold2 (season 20242025, segment all)

Generated 2026-10-15 by `scripts/eval_gates.py`. Tolerances `docs/gates.yaml` (provisional). Sim rows 1398000. run_meta: {'engine_tag': 'control_r1_A0_fold2', 'arm': 'A0', 'fold': 2, 'season': 20242025, 'n_seeds': 1000, 'sealed_touched': False, 'oracle_goalie': False, 'frozen_params': 'docs\\models\\control\\r1_frozen_params.json'}

| gate | status |
|---|---|
| G1 | NEEDS-INSTRUMENTATION |
| G2 | NEEDS-INSTRUMENTATION |
| G3 | NEEDS-INSTRUMENTATION |
| G4 | NEEDS-INSTRUMENTATION |
| G5 | FAIL |
| G6 | FAIL |
| G7 | FAIL |
| G8 | NEEDS-INSTRUMENTATION |
| G9 | FAIL |

## G1: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G2: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G3: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G4: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G5: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| P(total=0) | 0.0007 | 0.0007 | 0.01 | PASS | 1398 | stat=-0.0000 |
| P(total=1) | 0.0169 | 0.0136 | 0.01 | PASS | 1398 | stat=0.0033 |
| P(total=2) | 0.0283 | 0.0215 | 0.01 | PASS | 1398 | stat=0.0069 |
| P(total=3) | 0.1027 | 0.1066 | 0.01 | PASS | 1398 | stat=-0.0039 |
| P(total=4) | 0.0960 | 0.1159 | 0.01 | FAIL | 1398 | stat=-0.0199 |
| P(total=5) | 0.1912 | 0.1996 | 0.01 | PASS | 1398 | stat=-0.0084 |
| P(total=6) | 0.1235 | 0.1338 | 0.01 | FAIL | 1398 | stat=-0.0103 |
| P(total=7) | 0.1707 | 0.1617 | 0.01 | PASS | 1398 | stat=0.0090 |
| P(total=8) | 0.0853 | 0.0894 | 0.01 | PASS | 1398 | stat=-0.0042 |
| P(total=9) | 0.0909 | 0.0851 | 0.01 | PASS | 1398 | stat=0.0058 |
| P(total=10) | 0.0939 | 0.0722 | 0.01 | FAIL | 1398 | stat=0.0216 |
| total SD ratio | 2.5059 | 2.3155 | (0.95, 1.05) | FAIL | 1398 | stat=1.0822 |
| margin SD ratio | 2.5981 | 2.5992 | (0.95, 1.05) | PASS | 1398 | stat=0.9995 |
| score correlation | -0.0361 | -0.1151 | 0.05 | FAIL | 1398 | stat=0.0790 |
| KS total goals (p, n_eff=n_real) | 0.1061 |  | >=0.1 | PASS | 1398 | D=0.0323 |

## G6: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| home win % | 0.5275 | 0.5651 | 0.015 | FAIL | 1398 | stat=-0.0376 |
| home goal diff | 0.1567 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1730 |

## G7: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| regulation tie rate | 0.1589 | 0.2082 | 0.015 | FAIL | 1398 | stat=-0.0492 |
| shootout rate | 0.0443 | 0.0551 | 0.01 | FAIL | 1398 | stat=-0.0108 |
| EN goals / game |  | 0.4063 | 0.03 | NEEDS-INSTRUMENTATION | 1398 |  |

## G8: NEEDS-INSTRUMENTATION

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| needs event-level / player-level sim output |  |  |  | NEEDS-INSTRUMENTATION | 0 |  |

## G9: FAIL

| check | sim | real | tol | status | n | note |
|---|---|---|---|---|---|---|
| total bias | 6.1989 | 6.0336 | 0.1 | FAIL | 1398 | stat=0.1652 |
| margin bias | 0.1567 | 0.3298 | 0.08 | FAIL | 1398 | stat=-0.1730 |
| margin slope (actual on pred) | 0.6141 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
| total slope (actual on pred) | 0.0375 | 1.0000 | (0.95, 1.05) | FAIL | 1398 | slope near 1 = calibrated spread; noisy at n~1400 |
