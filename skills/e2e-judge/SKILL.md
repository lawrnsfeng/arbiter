---
name: e2e-judge
description: Independently judge whether an e2e test suite is strong enough for given functional requirements. Re-derives the obligations blind from the requirements (happy, boundary, decision, state, the 14 unhappy-path classes, must-not clauses), maps the suite onto them by stimulus and assertion with comments and titles stripped, grades each oracle O0-O3 on the required action's channel (default return, error, delegation, user message, emission to a sink), then proves it with executed evidence - e2e-only branch coverage, diff-scoped and LLM-targeted mutants, spec mutants, fail-to-pass against the baseline. Returns STRONG / GAPS / WEAK with each gap as the exact missing assertion. Read-only on the repo. Use when asked whether e2e/acceptance tests cover a requirement or are strong enough; design a suite with e2e-design instead.
argument-hint: "<requirements path | issue URL | #N> [--suite PATH...] [--base REF] [--out DIR] [--static-only]"
---

# e2e-judge

Decide whether the suite is ground truth for the requirements. Agreement between judges, test titles, comments and the designer's own matrix are **not evidence**. Only executed artefacts or a quoted assertion count.

References:
- `../e2e-design/references/obligations.md`: the format.
- `../e2e-design/references/unhappy.md`: §10 taxonomy, §0–§9 oracles.
- `references/adequacy.md`: coverage commands per stack in §2, mutation in §4, spec mutation in §5, smells in §6.
- `references/judging-current.md`: overrides `adequacy.md` where they conflict.
- `references/rubric.md`: the verdict.

## Hard rules
- Never edit the reviewed repo's tracked files, and never commit. Every write goes under `$OUT`. Mutants and builds run only in worktrees under `$OUT`.
- Never derive an expected behaviour from the implementation, the tests or the designer's files.
- Never ask the user. Ambiguities become `Q`s, and the verdict says so.

## Setup
- **Requirements:** a path, `#N`, or an issue URL (`gh issue view <N> --json title,body,comments`).
- **Slug:** the requirement title in kebab-case, at most 5 words.
- **`$OUT`:** `--out`, else `/tmp/e2e-judge/<slug>-<UTC %Y%m%dT%H%M%S>`. Create `$OUT/raw/`.
- **Suite:**
  - `--suite` paths;
  - else the files whose test titles start with `O<n>` (`O<n>:`, `test_o<n>_`, `TestO<n>`);
  - else the repo's e2e directories (Playwright `testDir`, `tests/e2e`, `e2e/`, the integration tier).
- **Base:**
  - `--base`;
  - else the merge-base with `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `master`, then `main`.

  If `base...HEAD` has no non-test changes, there is no baseline: skip step 8 and set R10 to `not measured: no baseline`.
- **Scope:** non-test source files changed in `base...HEAD`. If that set is empty, use the non-test source files that the suite's coverage hits in step 5.

## Procedure
1. **Blind derivation.** Read the requirements only. Do not open the suite, the code, `*.obligations.json` or `*.matrix.md` yet.
   - Write `$OUT/obligations.blind.json` in the `obligations.md` schema:
     - EARS clauses with complements;
     - questions;
     - the channel inventory, reading only config and infrastructure files (compose, env, routes, queue names) for this;
     - obligations from every technique in `e2e-design/references/techniques.md` §2;
     - all 14 unhappy classes per clause;
     - each `must-not` clause.
   - Then a second pass over the same requirements, aimed at **recall only**: list obligations the first pass missed, and add them. A second pass never removes an obligation.
2. **Stability.** Run the suite 3× in a worktree, `git worktree add --detach $OUT/wt HEAD`, using the repo's e2e command.
   - Record pass, fail, skip and duration per test.
   - Any test that changes outcome across runs is `GAP-FLAKY`.
   - A test that is quarantined, skipped without a `blocked-on Q<n>` reason, or `fixme` covers nothing.
   - If the suite cannot start, record the error, mark R4–R7 and R10 `not measured`, and continue statically.
3. **Assertion audit (agent-written suites).** Run `git log -p base..HEAD` on the suite files. Every one of these in `base..HEAD` is reported as a coverage loss in the report:
   - a weakened matcher (`toBe(x)` → `toBeTruthy()`/`toBeDefined()`, exact → `contains`);
   - a changed expected literal;
   - an added `skip`/`fixme`/`xfail`;
   - a deleted test.
4. **Map and grade.**
   - **Strip first.** Copy each test with comments, titles, docstrings and `// spec:` headers removed. Grade the stripped copy.
   - **Map** each test to blind obligations by **stimulus and assertions**.
   - Unmapped obligations are `GAP-MISSING`. Tests that map to nothing are listed as orphans.
   - **Grade** each (test, obligation) pair:
     - O3: exact value on the required channel, plus the forbidden effects asserted;
     - O2: right channel, coarse check;
     - O1: passes unless it crashes;
     - O0: nothing.
   - **Smell cap.** Conditionals, loops, swallowed exceptions, first-party mocks or fixed sleeps cap the grade at O1 (`adequacy.md` §6).
   - **Discrimination check.** For every unhappy obligation, take each other action type (`default`, `error`, `delegate`, `user-message`, `emit`). If an assertion would still pass with that action, the grade is at most O2.
   - Unhappy obligations below O3 are `GAP-ORACLE`.
   - Only now open the designer's `*.obligations.json`, if any. List the obligations the designer has but the blind pass missed, and add them as `origin: designer` after checking each against the requirements text. Never use the designer's mapping as evidence.
5. **Coverage (e2e only).** Build the system instrumented in `$OUT/wt`, using the stack's recipe in `adequacy.md` §2:
   - Go: `go build -cover -coverpkg=./...`, `GOCOVERDIR=$OUT/raw/cov`;
   - Python: coverage.py `--branch` with `sigterm = true` or `--save-signal`;
   - Node: `NODE_V8_COVERAGE` + c8;
   - Rust: `-C instrument-coverage`;
   - browser: Playwright `page.coverage`.

   Then:
   - Run the suite once and stop the system gracefully so the counters flush.
   - Report branch coverage for the in-scope files, with arid lines excluded (logging only, generated code).
   - An uncovered branch tied to an obligation is `GAP-UNREACHED`.
   - A covered branch tied to no obligation becomes a `Q`: the code does something the spec never mentions.
6. **Mutation (in scope, covered lines only).** Write each mutant as `$OUT/raw/mutants/M<n>.patch`, then run them in this order:
   - (a) **Extreme.** One per in-scope function: return the zero or default value, or remove the body. At most 40.
   - (b) **Operators.** ROR, LCR, AOR and UOI on every decision and boundary line. At most 60.
   - (c) **Targeted.** 1–3 per unhappy obligation: swap the action for another action type, drop the side effect, write to the wrong sink, retry N±1 times.

   Budget: drop duplicates and mutants that fail to compile. If more than 150 remain, keep every risk-H mutant, then sample the rest evenly.

   Mutation tool:
   - If the stack's tool (StrykerJS command runner, mutmut, gremlins, cargo-mutants) can run the e2e command against the mutated server, it may run (a) and (b).
   - Otherwise, and always for (c), use patch-apply: for each mutant, `git -C $OUT/wt apply M<n>.patch`, rebuild, run the tests mapped to the mutated file (else the whole suite), then `git -C $OUT/wt apply -R M<n>.patch`.

   Classify each outcome:
   - an assertion failed: **oracle kill**;
   - crash, 5xx page, timeout or locator not found: **incidental kill**;
   - all passed: **survived**.

   For each survivor, either write a one-line equivalence argument or record `GAP-ORACLE` (decision, boundary or targeted mutant) or `GAP-PSEUDO` (extreme mutant), with the assertion that would kill it.
7. **Spec mutants.** For each obligation, write 2–4 `SM<n>`:
   - negate the condition;
   - shift a boundary by one;
   - drop a conjunct;
   - swap the action;
   - swap the sink;
   - drop a `must-not`.

   Decide statically whether ≥1 test would fail. Confirm ≥20% of the "distinguished" decisions by implementing the matching code mutant in step 6's loop.
8. **Fail-to-pass (when a baseline exists).**
   - `git worktree add --detach $OUT/base <base>`, then `git -C $OUT/base checkout HEAD -- <suite files>`.
   - Run the tests that map to obligations of new behaviour. Each must fail on the baseline.
   - A test that passes there is miscredited: it does not cover the new obligation.
9. **Verdict.** Apply `references/rubric.md` row by row.
10. **Clean up.** `git worktree remove --force $OUT/wt`, and the same for `$OUT/base` if it was created. Keep `$OUT/raw`.

## Outputs
- `$OUT/obligations.blind.json`;
- `$OUT/judge.json`: the obligations with the judge fields from `obligations.md`, plus `"rubric": {"R1": {"value": "...", "band": "STRONG|GAPS|WEAK|not measured: ..."}, ...}, "verdict": "STRONG|GAPS|WEAK"`;
- `$OUT/report.md`.

The final message relays `report.md` verbatim:
```
## e2e-judge: <slug> → STRONG | GAPS | WEAK
Obligations: a (b unhappy, c must-not, d blocked on questions) · Tests: e (f orphans) · Out: $OUT
| Row | Value | Band |
|---|---|---|
| R1 … R10 |
### Gaps (worst first)
- GAP-ORACLE O7 (C3): needs `expect(jobsCount()).toBe(0)` on channel db:jobs; surviving mutant M12 (drop the 401 early return's no-write guard).
### Open questions
- Q1: <text>
### Assertion audit
- <file>: <weakened/deleted/skip> in <commit>
```
