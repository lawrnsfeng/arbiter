---
name: e2e-design
description: Design and write a ground-truth e2e test suite from functional requirements (issue, spec, PRD or EARS list). Decomposes requirements into EARS clauses and obligations, applies ISO 29119-4/ISTQB techniques (partitions, boundaries, decision tables, state transitions, flows, pairwise, properties), walks a 14-class unhappy-path taxonomy, and gives every test a four-part oracle (user-visible, persisted, side-effect, negative) that names the exact required action - default return, error, delegation, user message or emission to a sink. Outputs obligations.json, a traceability matrix and runnable tests. Use when asked to design, plan or write e2e/acceptance tests for a requirement; judge an existing suite with e2e-judge instead.
argument-hint: "<requirements path | issue URL | #N> [--design-only] [--slug NAME]"
---

# e2e-design

Turn requirements into an e2e suite that can serve as ground truth.

**Ground rule.** Expected outcomes come from the requirements only, never from the code or the running app. A test that encodes observed behaviour can encode a bug.

References, read in this order:
- `references/obligations.md`: the format. Follow it exactly.
- `references/techniques.md`: technique details.
- `references/unhappy.md`: oracles, fault injection, the 14-class taxonomy.
- `references/current-practice.md`: EARS, agent-generated suites, reliability, properties. Where it conflicts with the other files, it wins.

## Inputs
1. Load the requirements:
   - a file path: read it;
   - `#N` or an issue URL: `gh issue view <N> --json title,body,comments`;
   - otherwise the text given.
2. Set the slug:
   - `--slug` if given;
   - else the requirement title in kebab-case, at most 5 words.
3. Read the repo enough to find:
   - the public surface: routes, UI pages, CLI;
   - the existing e2e harness and how the system starts;
   - the channel inventory (`obligations.md`).

   Do not read the implementation of the feature under test to decide expected values.

## Harness choice
Take the first rule that applies:
1. An e2e harness exists (Playwright config, `tests/e2e`, `e2e/`, an integration tier with containers): use it. Follow its fixtures, naming and run command.
2. The feature has a browser UI: Playwright Test in `e2e/`, with its own `package.json`, plus `playwright.config.ts`:
   - `fullyParallel: true`
   - `retries: 2` (classification only)
   - `trace: 'on-first-retry'`
   - a `webServer` entry that starts the system.
3. Otherwise (an API, CLI or worker): the repo's own test runner in `tests/e2e/`. It drives the built system as a separate process through its public interface only: HTTP, CLI or queue. Never import the code under test.

Owned dependencies (DB, queue, cache) run real, via testcontainers or the repo's compose file. Only third parties are faked, at the network edge: WireMock, MSW or Playwright `route`.

## Procedure
1. **Clauses.** Split every requirement sentence into atomic EARS clauses `C<n>` (`obligations.md`), keeping the verbatim quote. Add the complement clause for every conditional clause.
2. **Questions.** Log every ambiguity as `Q<n>`: inclusive or exclusive bounds, exact error text or code, whether a specified body, message or record is exact or a minimum (extra fields allowed), an unspecified unhappy action, an unnamed sink.
   - Interactive session: ask them all in one batch, then record the answers.
   - Running as an agent, or unanswered: leave `answer: null` and mark the dependent obligations `blocked-on Q<n>`.
   - Never guess. This overrides any spec tool's "make an informed guess" default.
3. **Channel inventory.** List every sink and store the feature can touch.
4. **Coverage items.** For each clause, apply the techniques in `techniques.md` §2–§4:
   - EP partitions;
   - BVA: 3-value for risk H, otherwise 2-value;
   - decision table columns for ≥2 interacting conditions, with MC/DC pairs for compound conditions;
   - a state table for lifecycles: 0-switch; invalid transitions for risk H; 1-switch for retry, back and undo;
   - main, alternate and exception flows;
   - a PICT model for environment and config, at t=2, or t=3 on risk H;
   - one stateful property test per stateful feature;
   - ≥2 metamorphic relations where exact output is impractical.

   Each item becomes an obligation.
5. **Unhappy taxonomy.** For every clause, walk all 14 classes in `unhappy.md` §10. Each class becomes obligations, or `na: <reason>` in the matrix. Leave none blank. Apply the fault checklist from `techniques.md` §2.9 the same way.
6. **Oracles.** Fill `expect.U/P/S/N` for every obligation, following these rules:
   - **Primary action.** Unhappy obligations name exactly one action and assert it on its primary channel (`obligations.md` Actions).
   - **Discrimination.** The assertion must fail if the code had taken any other action.
   - **Fallbacks.** Seed data so the real answer differs from the default.
   - **Delegation and retry.** Assert count and order from a request journal, the same idempotency key on every attempt, and no attempt N+1.
   - **Errors.** Assert status plus the machine-readable code. Error bodies carry no stack traces, SQL or internal hosts.
   - **Error tracker.** Expected errors (validation, not-found, authz) produce zero tracker events. Unexpected errors produce exactly one.
   - **Sinks.** Assert on the sink with a bounded poll. Negative async checks wait for a positive completion signal first.
   - **Negative oracle.** `N` covers every channel in the inventory.
   - **Fault proof.** Every injected fault records `trigger_proof`: a journal hit, a toxic counter, a failpoint hit.
   - **Open questions.** No assertion, parametrized case or property/model rule may pin behaviour that depends on an open `Q`. Move that input into the blocked obligation's skipped test.
7. **Assemble tests.**
   - Each test has one When action, or one command sequence.
   - Each test has at most one invalid or unhappy obligation.
   - Titles follow `obligations.md`. Write `<slug>.obligations.json` and `<slug>.matrix.md` (below) before any test code.
8. **Determinism.** Every test:
   - seeds its own data through the API or a factory, in its own tenant or a per-run database;
   - uses `page.clock` and a server clock for time;
   - uses role, label or test-id locators;
   - waits only with web-first `expect` or `expect.poll`, never fixed sleeps;
   - runs alone, in any order, in parallel.

   One global after-each fails on uncaught page errors and unexpected 5xx responses.
9. **Reachability.** Every unhappy branch needs proof that the run reached it. Use the fault's `trigger_proof`. If none is observable, the test asserts a log line, span or metric that only that branch emits. Never add code to the system under test for this.
10. **Write the tests** (skip with `--design-only`):
    - Obligations marked `blocked-on Q<n>` are written as skipped tests with reason `blocked-on Q<n>`: Playwright `test.fixme`, pytest `pytest.mark.skip(reason=...)`, Go `t.Skip`.
    - Never weaken a matcher, change an expected value or delete a test to get green. When a test fails, the code or the requirement is wrong: report it.
11. **Run** the suite 3× with the repo's command.
    - A test that fails with the system behaving per spec is fixed in the test's setup, never in its expected value.
    - A test that fails because the system violates the spec is a finding. Keep it failing, list it in the report, and do not fix the product code.
    - Any flake is fixed at its root cause. Retries do not count as a fix.

## Outputs
Place these beside the tests, in the harness's e2e directory, or `tests/e2e/` when the harness has none:
- `<slug>.obligations.json`, in the `obligations.md` schema, with the top-level `tests` array;
- `<slug>.matrix.md`;
- the test files.

Final message, in exactly this skeleton:
```
## e2e-design: <slug>
Clauses: a (b derived) · Obligations: c (d unhappy, e must-not) · Tests: f · Blocked: g · NA: h
Technique coverage: EP x% · BVA x% · DT x% · ST x% · flows x% · taxonomy x% (per matrix)
### Open questions
- Q1: <text> (blocks O4, O5)
### Spec violations found (tests left failing)
- O7 <title>: expected <...>, got <...>
### Run
<command> · 3 runs · pass p / fail q / skipped r · flaky: none | <list>
Files: <paths>
```

## Rules
- Every clause maps to ≥1 obligation, and every obligation maps to ≥1 test or is `blocked`/`na` with a reason. Orphans fail.
- Every boundary is tested at min−1, min, max and max+1, with inclusivity cited from the spec or raised as a `Q`.
- No first-party endpoint is mocked. Owned dependencies run real.
- Every error class has ≥1 test against the real backend.
- The designer never judges its own suite. Hand it to `e2e-judge` (agent `e2e-judge`) for the verdict.
