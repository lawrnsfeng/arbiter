# Verdict rubric

**Verdict = the worst row.** Never average. One WEAK row makes the suite WEAK.

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
| R10 | New-behaviour tests that are fail-to-pass against the baseline (only when a baseline exists) | 100% | ≥90% | <90% |

How each row is applied:
- **Measurement failures.** A row that could not be measured (no build, coverage would not flush, mutation tooling failed) reads `not measured: <reason>`. The verdict is then at best GAPS. `--static-only` makes R4–R7 and R10 `not measured: static-only`.
- **Open questions.** `GAP-QUESTION` obligations (open `Q`) do not count against R1–R3. Any open `Q` caps the verdict at GAPS, because the requirement itself is incomplete.
- **Unhappy-path grades (R2).** R2 counts an unhappy obligation as O3 only when all three hold:
  - the assertion discriminates against every other action type;
  - its fault test proves the fault fired;
  - the obligation has a killed mutant or a covered branch.
- **Gap reports.** Each gap is written as: `O<n> (<clause>) needs <exact assertion> on <channel>`. Never report a percentage alone.
