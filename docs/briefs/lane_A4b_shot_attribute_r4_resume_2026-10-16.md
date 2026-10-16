# Lane A4 brief (resume): SL-R4 after D28

Same lane, same rules and core cap. Read D28 in `ARCHITECTURE_DECISIONS.md` and the PM ruling block appended under SL-R4 in `docs/models/shot_attribute/experiments.md`.

1. Record the restated D13 guard result: fold-1 checks read on L3c minus L0s, plus the oracle read. Write it into `grade_fold1.json` with an explicit `d13_guard_basis: "L3c-minus-L0s (D28)"` field, then set `d13_guard_pass` to that result. Do not change the original field's history: add a `d13_guard_pass_original: false`.
2. Run `pred2` and the blind fold-2 grade. Then the bias checks, with EN strata reported and not gated (D28), the ES responsiveness band, and the decision as pre-registered.
3. If L3c is selected, run the closed loop exactly as SL-R4 says. Otherwise skip it.
4. Append to the same report, under a "Resume after D28" heading, plus a results block and ledger row. Commit, push, verify.

Message to the PM: under 300 words.
