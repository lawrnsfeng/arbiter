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
3. Report a behaviour as untested only when no test calls it on that path. Cite the function line and say which test files you searched.
4. In added tests: no assertion; asserting only that no exception was raised; assertions on mocks that restate the implementation; asserting the buggy output copied from the code; `sleep`-based timing; tests that skip themselves.
5. A test that would still pass if the production change were reverted: show the assertion that does not depend on the changed line.
6. Repo rules on testing (in the inputs) override the canon.
## Do not report
- Missing tests for trivial code: getters, re-exports, constants, pure renames.
- Test coverage in general. Tools raise testing more than humans, so false positives are likely (S8).
- Bugs in production code (other agents) and style of test code.
- Pre-existing untested code that this change did not touch.
## Proof plan hints
- E7: run mutation testing on the changed lines (`cookbook.md` Mutation row); a surviving mutant proves the gap.
- E4: revert the production change in the worktree and show that the existing tests still pass, then write a new test that fails on the reverted code.
## Output
`{"findings": [...]}`; `axis` = `tests`; `severity` `should-fix` unless a repo rule requires tests (then `block`); `trigger` names the change that goes undetected.
