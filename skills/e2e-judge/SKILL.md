---
name: e2e-judge
description: Independently judge whether an e2e test suite is strong enough for given functional requirements. Re-derives the obligations blind from the requirements and their approved examples (happy, boundary, decision, state, the 14 unhappy-path classes, must-not clauses), maps the suite onto them by stimulus and assertion with comments and titles stripped, and grades each oracle O0-O3 on the required action's channel. Two stages - design, right after the suite is written and before the change exists (tests must fail for the right reason; the suite is then frozen), and evidence, after the change (e2e-only branch coverage, targeted mutants, spec mutants, fail-to-pass from the freeze, frozen-suite tampering, and one evidence record per obligation bound to the patch). Returns STRONG / GAPS / WEAK with each gap as the exact missing assertion. Read-only on the repo. Use when asked whether e2e/acceptance tests cover a requirement, are strong enough, or prove a change; design a suite with e2e-design instead.
argument-hint: "<requirements path | issue URL | #N> [--suite PATH...] [--stage design|evidence] [--fast] [--freeze PATH] [--base REF] [--out DIR]"
---

# e2e-judge

Decide whether the suite is ground truth for the requirements. Agreement between judges, test titles, comments and the designer's own matrix are **not evidence**. Only executed artefacts or a quoted assertion count.

References:
- `../e2e-design/references/obligations.md`: the format.
- `../e2e-design/references/unhappy.md`: §10 taxonomy, §0–§9 oracles.
- `../e2e-design/references/techniques.md`: technique details, §2–§4.
- `references/adequacy.md`: coverage commands per stack in §2, mutation in §4, spec mutation in §5, smells in §6.
- `references/judging-current.md`: overrides `adequacy.md` where they conflict.
- `references/rubric.md`: the verdict.
- `references/evidence.md`: the evidence ladder, `freeze.json`, `evidence.json`, the evidence table.

## Hard rules
- Never edit the reviewed repo's tracked files, and never commit. Every write goes under `$OUT`. Mutants and builds run only in worktrees under `$OUT`.
- Never derive an expected behaviour from the implementation, the tests or the designer's files.
- Never ask the user. Ambiguities become `Q`s, and the verdict says so.

## Setup
- **Requirements:** a path, `#N`, or an issue URL (`gh issue view <N> --json title,body,comments`). Its `## Examples` and `## Entry points` sections, when present, are requirement text: each example and each entry point needs ≥1 blind obligation.
- **Slug:** the requirement title in kebab-case, at most 5 words.
- **`$OUT`:** `--out`, else `/tmp/e2e-judge/<slug>-<UTC %Y%m%dT%H%M%S>`. Create `$OUT/raw/`.
- **Suite:**
  - `--suite` paths;
  - else the files whose test titles start with `O<n>` (`O<n>:`, `test_o<n>_`, `TestO<n>`);
  - else the repo's e2e directories (Playwright `testDir`, `tests/e2e`, `e2e/`, the integration tier).
- **Base:**
  - `--base`;
  - else the merge-base with `git symbolic-ref refs/remotes/origin/HEAD`, falling back to `master`, then `main`.

  If `base...HEAD` has no non-test changes, there is no baseline: without `--freeze`, skip step 8 and set R10 to `not measured: no baseline`.
- **Scope:** non-test source files changed in `base...HEAD`. If that set is empty, use the non-test source files that the suite's coverage hits in step 5.
- **Stage** (`--stage`, default `evidence`):

  | Stage | When | Steps | Verdict rows |
  |---|---|---|---|
  | `design` | the suite is written, the change is not | 1, 2D, 3, 4, 7 without the code-mutant confirmation, 10, 11; writes `freeze.json` | design (`rubric.md`) |
  | `evidence` | after the change | 1–11; step 8 reads `--freeze` when given | final |
  | `evidence --fast` | after the change, cheaply | as `evidence`, without steps 5 and 6 or step 7's code-mutant confirmation | final, without R4–R7 |

  `--freeze` is the `freeze.json` path a design stage wrote; it enables step 2's frozen-suite check, R10 and R11 from the freeze, and R12.

## Procedure
1. **Blind derivation.** Read the requirements only. Do not open the suite, the code, `*.obligations.json`, `*.matrix.md` or the `--freeze` file yet; step 2 reads the freeze.
   - Write `$OUT/obligations.blind.json` in the `obligations.md` schema:
     - EARS clauses with complements;
     - questions;
     - the channel inventory, reading only config and infrastructure files (compose, env, routes, queue names) for this;
     - obligations from every technique in `../e2e-design/references/techniques.md` §2–§4;
     - all 14 unhappy classes per clause;
     - each `must-not` clause.
   - Then a second pass over the same requirements, aimed at **recall only**: list obligations the first pass missed, and add them. A second pass never removes an obligation.
2. **Stability.** Create the worktree with `git worktree add --detach $OUT/wt HEAD`. Then apply the working tree's suite state to it: copy in every file that `git status --porcelain --untracked-files=all --no-renames -- <suite paths>` lists as untracked, added or modified, and delete the ones it lists as deleted, so an uncommitted suite is judged as it stands. Uncommitted changes outside the suite paths are not copied: if `git status --porcelain` shows any, the evidence says "judged HEAD product code". Run the suite 3× there, using the repo's e2e command.
   - Right after the copy, before any build, record the patch-id of what is judged: `git -C $OUT/wt add -A -- <suite paths> <scope files> && git -C $OUT/wt diff --cached <base> | git patch-id --stable` (the worktree's own index).
   - Record pass, fail, skip and duration per test.
   - Any test that changes outcome across runs is `GAP-FLAKY`.
   - A test that is quarantined, or skipped/`fixme` without a `blocked-on Q<n>` reason, covers nothing and counts against R9. A test skipped with a `blocked-on Q<n>` reason covers nothing but is not a defect.
   - If the suite cannot start, record the error, mark R4–R7 and R10 `not measured`, and continue statically.
   - **Frozen suite (with `--freeze`).** Diff every frozen file against its copy in the freeze (`diff -u <freeze dir>/<copy> <path>`). A frozen test whose body changed, that was skipped or deleted, or whose file is gone is `GAP-TAMPERED` and counts against R12. Added tests are judged like any other.

   **2D. Run before the change (design stage, instead of step 2).**
   - Build `$OUT/wt` as in step 2 and run the suite once against the code as it is, before the change.
   - Record `before` per test, per `evidence.md`. An assertion failure is recorded with the channel it asserts on. A build unit that does not compile because a symbol the change adds is missing is `fail-missing: <symbol>`. A collection, import, fixture, timeout or harness error, or a compile error for any other reason, is `fail-other`.
   - Step 4 sets `expect_before` and checks it, once tests are mapped.
   - After step 10, copy every suite file to `$OUT/frozen/<path>` and write `$OUT/freeze.json`: `base` is the commit the run used; `design_commit` is HEAD when `git status --porcelain -- <suite paths>` is empty, else null; each file's `blob` is `git hash-object <path>`.
3. **Assertion audit (agent-written suites).** Run `git log -p base..HEAD` and `git diff HEAD` on the suite files. Every one of these, in `base..HEAD` or in the working tree, is reported as a coverage loss in the report (`in <commit>` or `in working tree`). With `--freeze`, audit step 2's frozen-suite diff the same way (`since freeze`):
   - a weakened matcher (`toBe(x)` → `toBeTruthy()`/`toBeDefined()`, exact → `contains`);
   - a changed expected literal;
   - an added `skip`/`fixme`/`xfail` whose reason is not `blocked-on Q<n>`;
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
   - **Smell cap.** Conditionals, loops, swallowed exceptions, first-party mocks or fixed sleeps cap the grade at O1 (`adequacy.md` §6). Exception: in a `property` or `metamorphic` test, a loop over generated or parametrized inputs, or a stateful model's conditionals, is not a smell when every iteration reaches an unconditional assertion.
   - **Discrimination check.** For every unhappy obligation, take each other action type (`default`, `error`, `delegate`, `user-message`, `emit`). If an assertion would still pass with that action, the grade is at most O2.
   - Unhappy obligations below O3 are `GAP-ORACLE`.
   - An obligation whose `status` is `blocked-on Q<n>`, with that `Q` still open, is `GAP-QUESTION`, not `GAP-MISSING`.
   - **`expect_before` (every stage).** For each mapped test, set `expect_before`: `pass` when every obligation it maps to is behaviour the requirements call unchanged ("still", "keeps", "remains"); `either` when every obligation it maps to is a `must-not` (an absence the code before the change may already satisfy); else `fail`. A new-behaviour test counts as failing for the right reason on an assertion about a mapped obligation's primary channel, or on `fail-missing` for a symbol the change adds. An `either` test that passed before the change reaches E4 only by a targeted mutant kill.
   - **Before-run check (design stage).** A test whose 2D result does not match its `expect_before` is `GAP-FAILREASON` and counts against R11: a new-behaviour test that passes proves nothing about the change, and one that fails for another reason has not been shown to test it.
   - Only now open the designer's `*.obligations.json`, if any. List the obligations the designer has but the blind pass missed, and add them as `origin: designer` after checking each against the requirements text. Never use the designer's mapping as evidence.
5. **Coverage (e2e only).** Build the system instrumented in `$OUT/wt`, using the stack's recipe in `adequacy.md` §2:
   - Go: `go build -cover -coverpkg=./...`, `GOCOVERDIR=$OUT/raw/cov`;
   - Python: coverage.py `--branch` with `sigterm = true` or `--save-signal`;
   - Node: `NODE_V8_COVERAGE` + c8;
   - Rust: `-C instrument-coverage`;
   - browser: Playwright `page.coverage`.

   Then:
   - Run the suite once and stop the system gracefully so the counters flush.
   - Report branch coverage for the in-scope files, with arid lines excluded (logging only, generated code). Where the stack gives no branch data (Go: block coverage; Rust stable: region coverage), report that measure and name it in R4's value.
   - An uncovered branch tied to an obligation is `GAP-UNREACHED`, unless that obligation is `GAP-QUESTION`: then it counts as tied to an open `Q` in R4.
   - A covered branch tied to no obligation becomes a `Q`: the code does something the spec never mentions.
6. **Mutation (in scope, covered lines only).** Write each mutant as `$OUT/raw/mutants/M<n>.patch`, then run them in this order:
   - (a) **Extreme.** One per in-scope function: return the zero or default value, or remove the body. At most 40.
   - (b) **Operators.** ROR, LCR, AOR and UOI on every decision and boundary line. At most 60.
   - (c) **Targeted.** 1–3 per unhappy obligation: swap the action for another action type, drop the side effect, write to the wrong sink, retry N±1 times.

   Budget: drop duplicates and mutants that fail to compile. If more than 150 remain, keep every risk-H mutant, then sample the rest evenly.

   Mutation tool:
   - If the stack's tool can run the e2e command against the mutated server, it may run (a) and (b): StrykerJS with the command runner, cosmic-ray (`test-command`), go-mutesting `--exec`, or gremlins / cargo-mutants with the e2e driver in a Go / Rust test that builds and spawns the mutated server. mutmut 3 cannot: it runs pytest in-process.
   - Otherwise, and always for (c), use patch-apply: for each mutant, `git -C $OUT/wt apply $OUT/raw/mutants/M<n>.patch`, rebuild, run the tests mapped to the mutated file (else the whole suite), then `git -C $OUT/wt apply -R $OUT/raw/mutants/M<n>.patch`.
   - Run every mutant under `timeout` set to 3× the slowest step-2 suite run, with a minimum of 60 s. Record that value in the report's evidence.

   Classify each outcome:
   - an assertion failed: **oracle kill**;
   - crash, 5xx page, timeout or locator not found: **incidental kill**;
   - all passed: **survived**.

   For each survivor, either write a one-line equivalence argument, mark it tied to open `Q<n>` when it changes only behaviour that an open `Q` leaves undecided, or record `GAP-ORACLE` (decision, boundary or targeted mutant) or `GAP-PSEUDO` (extreme mutant), with the assertion that would kill it.
7. **Spec mutants.** For each obligation, write 2–4 `SM<n>`:
   - negate the condition;
   - shift a boundary by one;
   - drop a conjunct;
   - swap the action;
   - swap the sink;
   - drop a `must-not`.

   Decide statically whether ≥1 test would fail. A missed spec mutant whose change an open `Q` leaves undecided is tied to that `Q`, not missed. Confirm ≥20% of the "distinguished" decisions by implementing the matching code mutant in step 6's loop.
8. **Fail-to-pass.** Tests whose `expect_before` is `either` (must-not only) are left out: passing before the change is allowed for them.
   - **With `--freeze`:** a new-behaviour test is fail-to-pass when its `before` is `fail-assertion` or `fail-missing` and it passed every step-2 run. Run no baseline. Tests added after the freeze have no `before` and are left out.
   - **Without, when a baseline exists:** record the reviewed commit, `REV=$(git rev-parse HEAD)`. Then `git worktree add --detach $OUT/base <base>`, `git -C $OUT/base checkout $REV -- <tracked suite files>`, and apply the step-2 suite changes (copies and deletions) there as well. Run the tests that map to obligations of new behaviour, and classify each result as in 2D. Only `fail-assertion` and `fail-missing` count as failing before the change; `fail-other` gets no credit.
   - A new-behaviour test that passed before the change is miscredited: it does not cover the new obligation.
9. **Evidence records (evidence stage).** Write `$OUT/evidence.json` per `evidence.md`, one record per obligation, while `$OUT/wt` still exists:
    - `patch`: `head`, `base`, and the patch-id step 2 recorded. `head` reads `<sha>+worktree` when step 2 copied uncommitted suite files.
    - `observed`: the values the mapped test saw, from its failure messages, logs or artifacts. When it exposes none, replay the obligation's stimulus once against the system started as in step 5 and record each channel. Write `<not exposed>` only when neither works; that channel is not asserted.
    - `level`: E2 when mapped; E3 when the mapped test passed every step-2 run; E4 when it also failed by assertion before the change (step 8) or killed an oracle-graded mutant aimed at this obligation (step 6); E5 when an artifact from the run shows the UI end state after the user action.
    - An obligation below its `required` level is `GAP-EVIDENCE`, counts against R13, and is listed under `### Owed` with the cheapest step that would raise it.
10. **Verdict.** Apply `references/rubric.md` row by row, for the stage's verdict.
11. **Clean up.** `git worktree remove --force $OUT/wt`, and the same for `$OUT/base` if it was created. Keep `$OUT/raw` and `$OUT/frozen`.

## Outputs
- `$OUT/obligations.blind.json`;
- `$OUT/judge.json`: the obligations with the judge fields from `obligations.md`, plus `"stage": "design|evidence"`, `"rubric": {"R1": {"value": "...", "band": "STRONG|GAPS|WEAK|not measured: ..."}, ...}, "verdict": "STRONG|GAPS|WEAK"`;
- design stage: `$OUT/freeze.json` and `$OUT/frozen/`;
- evidence stage: `$OUT/evidence.json`;
- `$OUT/report.md`.

The final message relays `report.md` verbatim:
```
## e2e-judge (<stage>): <slug> → STRONG | GAPS | WEAK
Obligations: a (b unhappy, c must-not, d blocked on questions) · Tests: e (f orphans) · Out: $OUT
Patch: <head sha>[+worktree] · base <sha> · patch-id <id>          (evidence stage)
| Row | Value | Band |
|---|---|---|
| R1 … R13 (rows outside the stage's verdict read `not measured: <stage>`) |
### Gaps (worst first)
- GAP-ORACLE O7 (C3): needs `expect(jobsCount()).toBe(0)` on channel db:jobs; surviving mutant M12 (drop the 401 early return's no-write guard).
### Open questions
- Q1: <text>
### Assertion audit
- <file>: <weakened/deleted/skip> in <commit> | in working tree | since freeze
### Freeze                                     (design stage)
- <n> tests frozen at <base>: <a> fail by assertion as expected, <b> unchanged-behaviour tests pass; freeze: $OUT/freeze.json
### Evidence                                   (evidence stage; format in evidence.md)
| Example | Observed on this patch | Level | Proof |
### Owed                                       (evidence stage)
- O<n> (<clause>): at E<k>, needs E<m>: <cheapest step>
```
