# Verdict rubric

**Verdict = the worst row.** Never average. One WEAK row makes the suite WEAK.

Two verdicts use this table:
- **design** (`--stage design`, before the change is implemented): rows R1, R2, R3, R8, R9 and R11.
- **final** (`--stage evidence`): every row that applies.

The thresholds are a synthesis, not a published standard. They are anchored on Stryker's default 80/60 bands and on Google's practice of treating every surviving mutant in changed, covered code as an actionable finding. Calibrate them on real suites before using them as a CI gate.

| # | Criterion | STRONG | GAPS | WEAK |
|---|---|---|---|---|
| R1 | Obligations with ≥1 mapped test (`blocked`/`na` excluded, listed separately) | 100% | ≥80% | <80% |
| R2 | Unhappy obligations graded O3 on the required action's channel | 100% | ≥70% | <70% |
| R3 | `must-not` obligations with an absence assertion | 100% | ≥50% | <50% |
| R4 | e2e-only branch coverage of in-scope code, arid lines excluded | ≥90%, and every uncovered branch justified | ≥70% | <70% |
| R5 | Pseudo-tested functions in scope (extreme-mutant survivors) | 0 | ≤2, each mapped to a gap | >2 |
| R6 | Mutation score in scope, equivalents removed | ≥85%, and 0 unexplained survivors on decision or boundary lines | 60–85% | <60% |
| R7 | Oracle kills / all kills | ≥80% | ≥60% | <60% |
| R8 | Spec mutants distinguished | 100% | ≥80% | <80% |
| R9 | Flaky, quarantined, skipped-without-`blocked-on` or deleted tests | 0 | 0 | any |
| R10 | New-behaviour tests (`expect_before: fail`) that are fail-to-pass: failed before the change, by assertion or `fail-missing` (from `freeze.json`, else step 8's baseline), and pass on the patch | 100% | ≥90% | <90% |
| R11 | Tests whose run before the change matched `expect_before` (`fail`, `pass` or `either`; `freeze.json`) | 100% | ≥90% | <90% |
| R12 | Frozen tests modified, skipped or deleted after the freeze (`freeze.json` given) | 0 | — | any |
| R13 | Obligations at their required evidence level (`evidence.md`) | 100% | ≥90% | <90% |

How each row is applied:
- **Measurement failures.** A row in the stage's verdict that could not be measured (no build, coverage would not flush, mutation tooling failed) reads `not measured: <reason>`. The verdict is then at best GAPS. Rows outside the stage's verdict never cap it.
- **Stage rows.**
  - The design stage reports R4–R7, R10, R12 and R13 as `not measured: design stage`. Its R2 cannot use mutants or coverage, so it requires the other two conditions below, and "proves the fault fired" means the test asserts its trigger proof before the request and that assertion held in the run before the change. Its R9 counts only what the source shows: quarantined tests and `skip`/`fixme` without a `blocked-on Q<n>` reason.
  - `--fast` leaves R4–R7 out of the verdict (`not measured: fast`). R2's third condition is then met by the test's failure before the change; unhappy obligations whose tests could not fail before (unchanged-behaviour `pass`, `either`, `fail-missing`) are left out of R2 and listed as owed. R13 counts E4 from failures by assertion before the change only. Obligations that can reach E4 only by a mutant kill (those whose tests are `either`, `fail-missing` or unchanged-behaviour `pass`) are left out of R13 and listed as `(n owed: mutation)`; the periodic full run settles them.
  - R10 without a freeze or a baseline, and R11 and R12 without a freeze, read `not measured: no freeze` (or `no baseline`). They are then outside the verdict and do not cap it.
- **Added tests.** Tests added after the freeze are not R12 losses. They are judged like any other test; R10 and R11 do not cover them, and they reach E4 only by a mutant kill.
- **Open questions.** `GAP-QUESTION` obligations (open `Q`) do not count against R1–R3. R4, R6 and R8 likewise leave out the uncovered branches, survivors and spec mutants that an open `Q` explains, and their value states `(n tied to open Q)`. Any open `Q` caps the verdict at GAPS, because the requirement itself is incomplete.
- **Unhappy-path grades (R2).** R2 counts an unhappy obligation as O3 only when all three hold:
  - the assertion discriminates against every other action type;
  - its fault test proves the fault fired;
  - the obligation has a killed mutant or a covered branch.
- **Gap reports.** Each gap is written as `GAP-<TYPE> O<n> (<clause>): needs <exact assertion> on channel <channel>[; surviving mutant M<n> (<what it changes>)]`. Never report a percentage alone.
