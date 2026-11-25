# E2E tests as ground truth: how to design them and how to judge them (2026 practice)

Sources: four research files written for this report (`research-e2e-design.md`, `research-e2e-adequacy.md`, `research-e2e-unhappy.md`, `research-e2e-current.md`). Each one has full URLs.
Tags: **[INFERENCE]** marks synthesis that no source states directly. The judge thresholds are synthesis and need calibration on real suites.

## 1. Bottom line

- **Coverage alone means little.** A suite counts as ground truth only when every *obligation* passes three checks:
  - it is derived from the requirements, never from the code;
  - it is hit by a test whose assertion **discriminates**, so it fails if the code took any other action;
  - an *executed* artefact proves this: a killed mutant, a reached branch, or a fail-to-pass run.
- **What has changed since 2024:**
  - Agents now write specs and tests. Their main failure is **oracles copied from observed behaviour, bugs included**. Repair loops also reach green by **weakening assertions or deleting tests** (arXiv 2410.21136, 2605.01471; TestingBot on Playwright Test Agents).
  - LLM judges are correlated: 9 judges give about 2 effective votes, and unanimous verdicts are wrong about 9% of the time (arXiv 2605.29800). Judges are also swayed by comments and test titles, by up to 26.7 pp (EACL 2026). **Judge agreement is not evidence.**
  - Mutation testing is now practical through **targeted LLM mutants**, scoped to a diff or a concern. Meta runs this as ACH (2025) and JiTTests (2026), with precision around 0.95 after filtering.

## 2. Designing a strong e2e suite from requirements

### 2.1 Requirement → clauses → obligations
1. **Write clauses in EARS.** Use `WHEN <trigger> THE SYSTEM SHALL <response>` for happy paths and `IF <unwanted trigger> THEN THE SYSTEM SHALL <response>` for every unhappy path. Each clause has one trigger, one condition set and one observable outcome. Every conditional clause also gets its complement (else) clause.
2. **Ambiguity becomes a blocking question, never a guess.** Tool defaults push the other way: spec-kit says "make informed guesses" and allows at most 3 clarifications. Override them. Tests that depend on an unanswered question are written as `blocked-on Q<n>`.
3. **Enumerate coverage items with the 29119-4 / ISTQB techniques.** Each technique has a coverage formula, so "systematic" can be computed:

| Technique | Coverage item | Target |
|---|---|---|
| Equivalence partitioning | valid and invalid partitions per input | Each Choice = 100% |
| Boundary values | min−1 / min / max / max+1 (3-value for high risk) | 100% |
| Decision table / cause-effect | feasible rule columns | 100%, plus MC/DC pairs for compound conditions |
| State transition | valid transitions; invalid ones for high risk; 1-switch for retry/back/undo | 100% 0-switch |
| Scenario / use case | main, alternate and exception flows | each flow |
| Combinatorial (PICT) | environment and config pairs | t=2, t=3 on high-risk sub-models |
| Error guessing / fault checklist | double submit, refresh, back, two tabs, session expiry, offline, Unicode, DST | each applicable item |
| Property / model-based | stateful commands + invariants (fast-check / Hypothesis), EARS-derived properties | ≥1 per stateful feature |
| Metamorphic | relations for outputs hard to pin (search, sort, export) | ≥2 relations |

4. **Walk the 14-class unhappy taxonomy for every clause.** Each class is covered by test IDs or marked `N/A: reason`; blank fails. The classes:
   - invalid input
   - missing / empty
   - boundary overflow
   - unauthenticated / unauthorised
   - not found
   - conflict / duplicate
   - dependency down
   - dependency slow
   - dependency garbage
   - partial failure
   - own timeout
   - race
   - resource exhaustion
   - retries exhausted

### 2.2 The oracle
Every unhappy test names **one primary action**: `default | error | delegate | user-message | emit`. It then asserts four layers, U/P/S/N:

| Layer | What | How |
|---|---|---|
| **U** user-visible | exact UI text by role (`alert`, `status`), exact status + machine-readable error code (RFC 9457 `type`), input preserved | Playwright web-first `expect`, `request` fixture |
| **P** persisted | state after settle, read via reload or public API (raw DB only if no public read path) | API read-back, `expect.poll` |
| **S** side-effect channel | log / span `ERROR` / tracker event / DLQ / outbox / mail / webhook, with severity and correlation id | OTel in-memory or collector exporter, Tracetest, mail sink, WireMock journal, queue inspection |
| **N** negative | nothing else happened: no write, no second charge, no email, exactly N retries and no N+1 | row counts, `exactly(0)` on fakes, poll after a positive completion signal |

Outcome-specific rules:
- **Fallback/default:** seed data so the real answer differs from the default, then assert the exact default.
- **Delegation and retry:** assert call count and order from a request journal, the same idempotency key on every attempt, and the terminal action after the last attempt.
- **Expected errors** (validation, not-found, authz) emit zero error-tracker events. **Unexpected errors** emit exactly one.
- **Every fault test proves its trigger fired.** Use a journal hit or a toxic counter. A stub that never matched makes the test invalid.
- **Reachability:** put a "sometimes" assertion on each rare unhappy branch (the Antithesis pattern), so the run proves it got there.

### 2.3 Fault injection: inject at the outermost layer that can produce the failure
- Browser: Playwright `route.abort/fulfill`, the `page.clock` API.
- Network: Toxiproxy (`down`, `latency`, `timeout`, `limit_data`), WireMock/Mountebank faults.
- In-process: failpoints (Go `gofail` / pingcap `failpoint`, Rust `fail`).
- Infrastructure: Chaos Mesh / IOChaos.
- Owned dependencies run **real** (testcontainers, or a database branch per PR). Fakes sit only at third-party edges, and each fake is kept honest by a contract test (Pact V4, bi-directional).
- At least one real-backend test per error class.

### 2.4 Determinism and hygiene
- Each test is isolated and seeds its own data via API in its own tenant. Per-PR database branching or per-worker containers is the 2026 norm.
- Control both the browser clock and the server clock.
- Locators use role, label or test-id.
- No fixed sleeps: only web-first `expect` and `expect.poll`.
- Global after-each: fail on uncaught page errors and unexpected 5xx responses.
- Retries only **classify** a test as flaky. Flaky tests go through automated quarantine (owner, ticket, still run, auto-reinstate), and **a quarantined test covers nothing**.

### 2.5 Agent-generated suites
- The plan carries the exact expected value per channel *before* generation. The generator never reads expectations off the running app.
- **Assertion lock.** These need human approval:
  - a weakened matcher (`toBe(5)` → `toBeTruthy()`)
  - a changed expected value
  - an added `skip`/`fixme`
  - a deleted test

  This applies to Playwright's healer above all: its prompt says "do the most reasonable thing possible to pass".
- Momentic's model: protected pre- and post-conditions that the agent cannot edit, and scripted steps on critical paths.

### 2.6 Deliverable: the traceability matrix
`Clause | kind | coverage items (P/B/D/S/T/I/F/E/G) | test id | oracle U·P·S·N | determinism (seed·clock·fault) | risk`.
- Every clause has ≥1 test, and every test has ≥1 clause.
- Coverage % per technique; anything under 100% carries a named question or risk waiver.

## 3. Judging a suite: the independent judge

### 3.1 Independence
- The judge is a different agent from the writer.
- **Blind derivation:** it builds the obligation list from the requirements alone, before it opens the suite or the code.
- **It reads assertion code with comments, titles and `// spec:` headers stripped.**
- A second independent derivation helps *recall* of obligations, never the verdict.

### 3.2 Procedure
0. **Stability.** Run the suite 3×. Any flake makes the verdict WEAK until fixed. Quarantined or `skip`/`fixme` tests count as absent.
1. **Blind obligations.** Each obligation records id, clause, precondition, stimulus, expected U/P/S/N, forbidden effects and risk. Ambiguities become questions, never answers taken from the code.
2. **Map tests → obligations** by stimulus and assertion. Unmapped obligations are **GAP-MISSING**; orphan tests are noted.
3. **Grade each oracle** on the required action's channel:
   - O3: exact value + forbidden effects asserted;
   - O2: right channel, coarse check;
   - O1: passes unless it crashes;
   - O0: none.

   Smells cap a test at O1: conditionals, swallowed exceptions, first-party mocks, sleeps.

   **Discrimination test:** would the test still pass if the code took a *different* unhappy action (default instead of error, log instead of DLQ, 4 retries instead of 3)? If yes, it fails.
4. **Executed coverage, e2e only.** Collect branch coverage from the running instrumented system:
   - Node: V8 / `NODE_V8_COVERAGE` + c8
   - Go: `go build -cover` + `GOCOVERDIR`
   - Python: coverage.py `--branch --save-signal`
   - Rust: `-C instrument-coverage`

   Shut down gracefully so counters flush. An uncovered branch tied to an obligation is **GAP-UNREACHED**. A covered branch tied to no obligation is a spec question.
5. **Executed mutation, scoped to the diff and to covered, non-arid lines.**
   - Extreme pass first: remove function bodies or return defaults. A survivor marks a pseudo-tested function, **GAP-PSEUDO**.
   - Then decision and boundary operators (ROR, LCR, AOR, UOI), plus 1–3 **targeted LLM mutants per unhappy obligation**: swap the action, drop a side effect, use the wrong sink. Filter by compile, dedupe and equivalence.
   - Count only **oracle kills**, where an assertion failed. A crash, timeout or broken locator is an incidental kill.
   - Each survivor is either equivalent (with a written reason) or a **GAP-ORACLE** naming the assertion that would kill it.
6. **Spec mutation.** Write 2–4 per obligation: negate, shift a boundary, drop a conjunct, swap the action, swap the destination, drop a "must not". Each must be distinguished by ≥1 test. Confirm ≥20% of these by running a code mutant.
7. **F→P.** If a pre-feature baseline exists, every new-behaviour test must fail on the baseline and pass on HEAD.
8. **Agent-suite audit.** Diff assertions against the last human-approved version. Any weakened matcher, changed expected value, new skip or deleted test is a coverage loss.

### 3.3 Verdict rubric
The verdict is the **worst row**; no averaging. Thresholds are [INFERENCE], anchored on Stryker's 80/60 bands and Google's survivor-as-finding practice.

| Criterion | STRONG | GAPS | WEAK |
|---|---|---|---|
| Obligations with ≥1 mapped test | 100% | ≥80% | <80% |
| Unhappy obligations at O3 on the required channel | 100% | ≥70% | <70% |
| "Must not" clauses with an absence assert | 100% | ≥50% | <50% |
| e2e branch coverage of in-scope code (excl. arid) | ≥90% + every miss justified | ≥70% | <70% |
| Pseudo-tested functions in scope | 0 | ≤2, filed | >2 |
| Mutation score in scope (equivalents removed) | ≥85% and 0 unexplained decision/boundary survivors | 60–85% | <60% |
| Oracle kills / all kills | ≥80% | ≥60% | <60% |
| Spec mutants distinguished | 100% | ≥80% | <80% |
| Flaky / quarantined tests | 0 | 0 | any |

- A row that could not be measured reads `not measured: <reason>`, and the verdict can then be at best GAPS.
- Gaps are reported as **"obligation X needs assertion Y on channel Z"**, never as a bare percentage.

## 4. Discredited or outdated
- Line coverage as an adequacy measure. Coverage correlates only weakly with fault detection once suite size is controlled (Inozemtseva & Holmes).
- A single mutation-score gate over the whole codebase. Mutation is now diff- or concern-scoped.
- "Equivalent mutants make mutation impractical." Equivalents run at 2–3%; the real cost of LLM mutants is non-compiling mutants, which a filter removes.
- Panels of LLM judges as independent review.
- Judges reading test names and comments.
- Coverage-feedback generation loops as proof of adequacy. TestForge reaches about 34% mutation score.
- Permanent retries; manually curated flaky lists; shared staging databases.
- Self-healing without an assertion lock.
- Given-When-Then as the *requirement* grammar. EARS has replaced it; GWT remains for examples.

## 5. Caveats
- The judge thresholds are synthesis. Calibrate them on 2–3 real suites before using them as a hard gate.
- Running mutation through e2e is slow. Diff scope, extreme mutation first, and coverage-guided test selection keep the cost bounded. mutmut 3 against a separate server process was not verified; the fallback is patch-apply mutants in a worktree.
- The correlated-judge result comes from NLI and preference tasks, not code; applying it to test judging is [INFERENCE].
- Not opened: Octomind, the MDPI Gherkin benchmark, the Schemathesis 4 paper, the NASA MC/DC tutorial text, and several vendor pages. Each file lists its own.
