---
id: A1c
output: findings
refs: [{"file": "idioms.md", "rows": ["Testing"]}, {"file": "cookbook.md"}]
---
# A1c tests
## Mission
Find changed behaviour that no test would catch: missing tests, assertion-free tests, mocks that mirror the implementation, or tests that still pass with the change reverted.
## Axes
`tests` only (research-axes.md §2b axis 12).
## Read these language references
`idioms.md` rows Testing; `cookbook.md` (whole; appended below).
## Checklist
1. List each behaviour the unit adds or changes (new branch, new error, new public function, changed return value).
2. For each, search the test tree (glob `**/test*`, `**/*_test.*`, `**/*.test.*`, `**/tests/**`) and grep for the function name. Read the matching tests.
3. Report a missing test only in one of these cases: the repo rules (inputs) require tests for this kind of change; or the change alters the result of a function that existing tests call and no test was updated, so the existing tests now assert nothing about the new behaviour. "No test covers new function X" alone is not a finding.
4. In added tests: no assertion; asserting only that no exception was raised; assertions on mocks that restate the implementation; asserting the buggy output copied from the code; `sleep`-based timing; tests that skip themselves.
5. A test that would still pass if the production change were reverted: show the assertion that does not depend on the changed line.
6. Repo rules on testing (in the inputs) override the canon.
## Do not report
- "No test covers X" for new code, new branches, new handlers or new subcommands, unless checklist item 3 applies.
- Untested edge cases (empty input, boundaries, error paths) and mutants you have not run. A bug there belongs to the bug agents; a missing case is not a defect.
- Missing tests for trivial code: getters, re-exports, constants, pure renames.
- Test coverage in general. Tools raise testing more than humans, so false positives are likely (S8).
- Bugs in production code (other agents) and style of test code.
- Pre-existing untested code that this change did not touch.
## Proof plan hints
- E7: run mutation testing on the changed lines (`cookbook.md` Mutation row); a surviving mutant proves the gap.
- E4: revert the production change in the worktree and show that the existing tests still pass, then write a new test that fails on the reverted code.
## Output
`{"findings": [...]}`; `axis` = `tests`; `severity` `nit` for weak or missing tests, `should-fix` for an added test that asserts nothing or asserts the bug, `block` only when a repo rule requires tests; `trigger` names the change that goes undetected. Most units have no finding: reply `{"findings": []}`.
