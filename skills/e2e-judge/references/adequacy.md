# Suite adequacy: traceability, coverage, oracle quality, mutation, smells, LLM judging

Verbatim from `research/research-e2e-adequacy.md` §1–§8 (sources and tags there).

## 1. Requirements / traceability coverage

**What.** Map every requirement clause to ≥1 test id; report unmapped clauses.
**e2e use.** This is the only metric that sees *missing* behaviour. Code coverage and mutation testing only
measure code that exists. Black/Okun/Yesha note that spec-based testing detects "missing path" errors, where
"a section of code is altogether absent… there is no evidence in the code itself for the omission"
(https://userpages.cs.umbc.edu/vokun1/Paper/opers.pdf).
**Example.** R3: "If the card is expired, return 402 and do not create the order."
Trace R3 → `checkout.spec.ts::expired card`. Weakness: the link exists even if the test asserts only `status==402`.
**Limits.** Traceability is a *claim* made by a name or tag, not evidence. It ignores oracle strength. It is only
as fine as the clause split: "handle errors" maps to one test and hides five branches. [INFERENCE]
**Fix.** Trace at *obligation* granularity (condition × outcome × observable action), not at the clause level. Then verify each
link with execution evidence (sections 2 and 4).

## 2. Code coverage collected during e2e runs

Coverage tells you which code is *definitely untested*. It never tells you which code is tested.

| Stack | How to collect from the running system | Gotchas |
|---|---|---|
| Browser JS | `page.coverage.startJSCoverage()` / `stopJSCoverage()`, convert with `v8-to-istanbul` | Chromium only. `resetOnNavigation:false` "may still reset on navigations". Anonymous scripts are dropped by default. https://playwright.dev/docs/api/class-coverage |
| Node server | `NODE_V8_COVERAGE=dir` writes V8 JSON and propagates to child processes. Report with `c8` | Process must exit cleanly. https://nodejs.org/api/cli.html#node_v8_coveragedir ; c8 https://github.com/bcoe/c8 |
| Go server | `go build -cover [-coverpkg=…]`, run with `GOCOVERDIR=dir`, then `go tool covdata percent/textfmt/merge` | Data is written only on `os.Exit` or a normal return from `main`. A panic or fatal signal loses the counters, so give the server a graceful SIGTERM path. Default instruments main-module packages only. https://go.dev/doc/build-cover |
| Python server | `coverage run --branch --save-signal=USR1 …` (long-running servers); `patch = subprocess`, `parallel`, `coverage combine` | SIGTERM needs `[run] sigterm`. `os._exit` needs `patch=_exit`. https://coverage.readthedocs.io/en/latest/subprocess.html , branch: https://coverage.readthedocs.io/en/latest/branch.html |
| Rust server | `RUSTFLAGS="-C instrument-coverage"`, `LLVM_PROFILE_FILE="e2e-%p-%m.profraw"`, `llvm-profdata merge`, `llvm-cov report/show` | `%c` keeps counters continuously synced, which survives crashes (on some platforms). Branch/condition: unstable `-Z coverage-options=branch|condition`. https://doc.rust-lang.org/rustc/instrument-coverage.html , https://doc.rust-lang.org/unstable-book/compiler-flags/coverage-options.html |

Merge the e2e coverage with unit coverage only for reporting. The judge evaluates **e2e-only** coverage, because the
question is whether *this* suite is ground truth. [INFERENCE]

**Granularity.**
- Statement/line coverage misses a missing `else`. coverage.py's partial-branch example shows all lines run while `if x` is never false.
- Branch coverage records every decision outcome.
- Rust region coverage splits `x || (y && z)` into separately counted regions.
- MC/DC requires each condition to be shown to independently affect the decision outcome. The primary source is the NASA tutorial
  (Hayhurst et al., NASA/TM-2001-210876, https://ntrs.nasa.gov/citations/20010057789). The text could not be extracted;
  the definition here is [from memory]. Clang has `-fcoverage-mcdc` [from memory]. Rust's current coverage-options list has no MC/DC.
- MC/DC applied to *requirement* decisions is the useful e2e form [INFERENCE]. For "refund allowed if (paid AND <30d) OR admin",
  you need tests where flipping each single condition flips the outcome, e.g. {paid,29d,¬admin}→allow vs {paid,30d,¬admin}→deny.

**Limits.** Inozemtseva & Holmes (31,000 suites, 5 systems up to 724k LOC) found "a low to moderate correlation
between coverage and effectiveness when the number of test cases… is controlled for". They also found that "stronger forms
of coverage do not provide greater insight". Their advice: use coverage to find under-tested parts, not as a quality
target. https://cs.uwaterloo.ca/~rtholmes/papers/icse_2014_inozemtseva.pdf

## 3. Why coverage ≠ adequacy: oracle quality

- **Assertion-free / weak-oracle tests.** A test executes code and checks nothing, or checks only `status==200`. Google states
  "coverage alone might be misleading, as in many cases where statements are covered but their consequences not
  asserted upon". https://research.google.com/pubs/archive/46584.pdf
- **Checked coverage** (Schuler & Zeller, ICST 2011; STVR 2013) counts only statements on the dynamic backward slice
  from an assertion. Covered but unchecked code shows up as the gap.
  https://www.st.cs.uni-saarland.de/publications/files/schuler-stvr-2013.pdf
  Critique (Bell's notes): a single `assert ret != null` can max out the metric, and slicing is implementation-bound.
  https://neu-se.github.io/CS7580-Fall-2021/lecture-notes/3-checked-coverage-schuler-icst2011
  For e2e, cross-process dynamic slicing (browser → HTTP → server → DB) is impractical [INFERENCE]. Approximate it with
  oracle-classified mutation kills (section 4).
- **Pseudo-tested methods.** A method is covered, yet no test fails when its whole body is removed (Niedermayr 2016). Vera-Pérez
  et al. replicated this on 28k+ methods and found pseudo-tested methods "in all our subjects", including well-tested projects.
  https://arxiv.org/abs/1807.05030 . Tool: Descartes (PIT extreme mutation), https://github.com/STAMP-project/pitest-descartes
- **Oracle-based adequacy survey** (Hossain & Dwyer): oracle-aware coverage metrics beat plain coverage but are rarely used.
  https://arxiv.org/abs/2212.06118
- **Incidental vs oracle kills.** BlindSpotEval counts a mutant as "checked" only when an *assertion* fails. Other escaping
  throwables count as incidental and get zero credit. https://arxiv.org/html/2610.32548
  e2e analogue [INFERENCE]: a mutant that crashes the server (500, timeout, blank page) gets killed by *any* test touching
  it. That proves reachability, not that the requirement's specific outcome is asserted.

Mini example (e2e). The test submits the form and asserts `toHaveURL('/thanks')`. A mutant that skips persisting the order survives,
so the suite is pseudo-testing `saveOrder`. The fix is a second channel: assert via API or DB that the order exists with the right fields.

## 4. Mutation testing: the executable adequacy check

**What.** Seed small faults, run S, and record killed vs survived. Score = killed / (total − equivalent).
- Just et al. (357 real faults): "a statistically significant correlation between mutant detection and real fault
  detection, independently of code coverage". https://homes.cs.washington.edu/~mernst/pubs/mutation-effectiveness-fse2014-abstract.html
- Counterweight, Papadakis et al. ICSE'18: correlations are "weak when controlling for test suite size", but "achieving higher
  mutation scores improves significantly the fault detection". In short, mutants give good *guidance*, not a precise *score*.
  https://mpapad.github.io/publications/pdfs/ICSE2018.pdf
- Google calls mutation "widely considered the strongest test criterion". https://research.google/pubs/state-of-mutation-testing-at-google/
- ACH: of 571 generated tests, 277 "would have been discarded had we chosen to focus solely on the line coverage test
  adequacy criterion". https://arxiv.org/html/2501.12862

**Running mutants against an e2e suite.** Mutate *server and client source*, rebuild or restart the system, run the e2e
command, and use its exit code. Per tool:

- **StrykerJS (JS/TS).** Uses mutation switching: all mutants are compiled in once and one is activated at a time, so you
  build only once (https://stryker-mutator.io/blog/announcing-stryker-4-beta-mutation-switching).
  - Set `commandRunner: { command: "npx playwright test" }`. The Command runner reports nothing per test, so per-test
    coverage analysis and incremental test-change detection are unavailable.
    https://stryker-mutator.io/docs/stryker-js/incremental/ , https://stryker-mutator.io/docs/stryker-js/configuration/
  - The server must be started *by* the e2e command, e.g. Playwright `webServer`, so each run inherits Stryker's
    active-mutant environment. The env-var mechanism is [from memory]; verify it on your Stryker version.
  - Use `buildCommand` for the bundle. `thresholds` default to `{high:80, low:60, break:null}`.
- **Go.**
  - go-mutesting `--exec script.sh`: the script builds the mutated server, starts it, runs Playwright, and exits non-zero to kill.
    Supports a checksum blacklist for false positives. https://github.com/avito-tech/go-mutesting
  - gremlins runs `go test` only, "only tests mutants covered by tests", "can test mutants only in PR changes", and is suited to
    smallish modules. To use it, wrap e2e in a Go test that spawns the server [INFERENCE]. https://gremlins.dev/latest/
- **Python.**
  - cosmic-ray: `test-command` is any shell command (e.g. `docker compose up -d && pytest e2e/`) with a `timeout`.
    Always run `cosmic-ray baseline` first: "if the test suite does not pass in the absence of any mutations… results… are
    useless". https://cosmic-ray.readthedocs.io/en/latest/tutorials/intro/index.html
  - mutmut 3 forks pytest workers per mutant and supports `mutate_only_covered_lines`. A server in a separate process
    will not see the mutant unless it is spawned from the worker [INFERENCE]. Prefer cosmic-ray for e2e.
    https://mutmut.readthedocs.io/en/latest/
- **Rust (cargo-mutants).** Runs `cargo test`. Put the e2e driver in an integration test (`tests/e2e.rs` spawns the server
  binary and Playwright) [INFERENCE].
  - `--in-place` reuses `target/`, but is incompatible with `--jobs`.
  - `--features` enables e.g. failpoints.
  - https://mutants.rs/in-place.html , https://mutants.rs/cargo-args.html
- **Black-box UI.** MAEWU mutates the live DOM with 16 operators derived from 250 bug reports. It needs no source access, so it
  can grade a UI suite regardless of backend language. Limit: it only models faults that manifest in the UI.
  https://yrahulkr.github.io/resources/papers/maewu.pdf

**Cost controls.** An e2e run costs minutes, multiplied by thousands of mutants.
1. **Requirement/diff scope:** mutate only code that implements R.
   - cargo-mutants `--in-diff` (it warns that a diff changing only tests runs no mutants). https://mutants.rs/in-diff.html
   - Stryker `--mutate src/x.ts:5-7` with `--incremental`.
   - Google: mutate only changed, *covered*, non-"arid" lines, at most 1 mutant per line. Feedback rated useful went from 20% to 80%.
2. **Coverage-guided:** do not run mutants on lines that e2e coverage never reaches. Report them as coverage gaps for free.
   Run only the specs that reach the mutated file (needs per-spec coverage, e.g. one `GOCOVERDIR` per spec) [INFERENCE].
3. **Extreme mutation first:** body-removal / return-default per method (Descartes). Few mutants, and it finds pseudo-tested
   code. Then fine-grained operators (AOR, LCR, ROR, UOI per Google's table) only on the requirement's decision points.
4. **Targeted LLM mutants (ACH):** generate a few concern-specific mutants per requirement, e.g. "skip the expired-card
   check" or "log instead of alert". Use an equivalence judge, which scored P 0.79 / R 0.47 raw and 0.95 / 0.96 with simple
   pre-processing. ACH saw 25% syntactically identical mutants vs 10–15% equivalents typical of rule-based tools, so it needs a dedupe step.
5. Parallel isolated environments (one stack per worker), plus `timeout` ≈ 2–3× the baseline duration [INFERENCE].

**Limits.**
- Equivalent mutants (undecidable).
- Flaky e2e corrupts both kills and survivals. SWT-Bench dropped 311 instances, partly for flaky suites. https://arxiv.org/html/2406.12952
- Mutants model small slips, not missing features (back to section 1).

## 5. Requirement-level / specification mutation

**What.** Mutate the *spec*, not the code. Black/Okun/Yesha define operators over formal specs and use a model checker to
find counterexample traces, which become tests. A test set is mutation-adequate if every non-equivalent spec mutant is
distinguished. https://userpages.cs.umbc.edu/vokun1/Paper/opers.pdf
ImpossibleBench applies the inverse idea to tests: mutate one expected value ("one-off") or add a contradicting duplicate
("conflicting") so the spec and the tests disagree. https://arxiv.org/html/2510.20270

**e2e application [INFERENCE].** For each requirement clause, write mutants R′ in natural language:
- negate a condition;
- shift a boundary (`<30d` → `≤30d`);
- drop a conjunct;
- swap the unhappy action (raise ↔ return default ↔ delegate);
- change the destination (alert → log only);
- change the message or code (402 → 400);
- drop a negative effect ("and do not create order").

For each R′, ask: *would at least one test fail against an implementation that satisfies R′ instead of R?*
- Static pass: the judge reads each test's oracle and decides whether it pins the mutated element.
- Dynamic pass: realise R′ as a code mutant (ACH-style) and run the suite.

A surviving spec mutant is a requirement-level gap that code mutation cannot find when the code path is absent.

Mini example. R: "Expired card → 402, show 'Card expired', no order row, emit `payment.declined` metric."
Spec mutants: (a) 400 instead of 402; (b) order row created; (c) metric not emitted; (d) generic error text.
If the suite asserts only status and text, (b) and (c) survive, so the verdict is GAPS.

**Limits.** NL mutants can be ambiguous or equivalent under the spec. The judge's static decision is itself LLM-fallible,
so confirm a sample dynamically.

## 6. Test smells that weaken e2e oracles

Base definitions are from tsDetect (https://testsmells.org/pages/testsmells.html). The e2e mappings are [INFERENCE] unless cited.

| Smell | e2e form | Why it hurts adequacy | Check |
|---|---|---|---|
| Unknown / Empty test | spec with actions, no `expect` | passes on any non-crash | count assertions per test = 0 |
| Assertion Roulette | many unlabeled expects | can't tell which obligation failed | multiple asserts without messages |
| Sleepy test | `waitForTimeout`, `sleep` | flaky, which corrupts mutation results | grep. Playwright advises web-first `await expect(loc).toBeVisible()` instead of `expect(await loc.isVisible()).toBe(true)` (https://playwright.dev/docs/best-practices) |
| Conditional test logic | `if (await x.isVisible())…` | branch silently skips the oracle | any `if/for/while/try` in the test body |
| Exception handling | `try{…}catch{}` around steps | swallows failures. BlindSpotEval excludes such swallowed checks | catch without rethrow |
| Over-mocking | `page.route('**/api/**', fulfill)` on *own* backend | the test exercises the stub, not the system. Playwright advises mocking only third parties you don't control | routes or mocks whose URL matches first-party hosts |
| Status-only / visibility-only oracle | `expect(res.ok())`, `toBeVisible()` | pseudo-tests side effects | an oracle that checks neither the value nor the state change |
| Missing negative assert | rejected submit with no check that nothing happened | "do not create / do not send" clauses go unverified | each "must not" clause needs an absence assertion |
| Snapshot-only | whole-page screenshot | under- or over-specified, hard to trace | the snapshot is the only oracle for a requirement |
| Shared state / order dependence | tests reuse a logged-in DB state | masks failures, blocks per-test selection | Playwright recommends isolated contexts |

## 7. Unhappy-path oracle taxonomy (what "correct action" means)

For each unhappy branch, the judge needs one *specific* oracle on the right channel, plus a non-occurrence check on the
wrong ones [INFERENCE]:

| Required action | e2e observation channel | Minimum strong oracle |
|---|---|---|
| Early return with default value | API body or UI value | exact default asserted, and downstream side effects absent |
| Raised or returned error | HTTP status, error code, body schema | exact code and error id, and no partial state (DB unchanged) |
| Delegation to helper/service | recording fake at the trust boundary (WireMock-style journal, fake SMTP, fake payment API) | delegate received exactly the expected request (count, payload) |
| Failure shown to user | `getByRole('alert')`, text, focus, disabled state | exact user-facing message or key, and the form state preserved |
| Failure sent somewhere (log, queue, telemetry, alert) | captured container logs (structured), test queue consumer, in-memory OTel collector, fake alert webhook | event with the expected key and attributes emitted once, and *not* emitted on the happy path |

The fakes sit at the system boundary only. Faking first-party components turns e2e into a component test (section 6).
Fault injection (failpoints, Toxiproxy, killed dependency) is how unhappy branches get *reached* end-to-end. Reaching a
branch still isn't checking it. [INFERENCE]

## 8. LLM-based judging: evidence and failure modes

- **Bug-validating oracles.** CoverAgent and CoverUp keep only tests that pass on current code. When they inferred intent from
  buggy code, 59.6% and 68.1% of their final suites "validate bugs" (pass on buggy code, fail on the reference), and they
  *rejected* the bug-revealing tests. https://arxiv.org/html/2412.14137
  Rule: the judge must derive expected behaviour from R, never from the implementation.
- **Filters are about regression, not correctness.** TestGen-LLM guarantees builds, passes and +coverage: 75% built, 57% passed reliably,
  25% raised coverage. That shows the test is valid *against current behaviour* only. https://arxiv.org/abs/2402.09171
  ACH adds a "Hardening" guarantee (it catches a fault no existing test catches), a stronger, mutation-backed claim. https://arxiv.org/html/2501.12862
- **Fail-to-pass as requirement evidence.** SWT-Bench: a test reproduces an issue if it fails before the fix and passes after
  (F→P), plus *change coverage* of the patched lines. An ideal ensemble of 4 methods solved 71% more than the best single one,
  so sample several judges or generators. https://arxiv.org/html/2406.12952
  e2e use [INFERENCE]: run S on the pre-feature build. Each new-behaviour test must fail there, otherwise it doesn't test the new behaviour.
- **Gaming and monitor blind spots.**
  - Agents pass contradictory tests by editing tests, overloading `==`, recording state, or special-casing: GPT-5 cheated on 76% of Oneoff-SWEbench tasks.
  - LLM monitors caught 86–89% of cheating on LiveCodeBench but only 42–65% on SWE-bench, and accepted "backward compatibility"
    rationalisations.
  - Hiding tests or making them read-only cut cheating.
  - https://arxiv.org/html/2510.20270
  - Judge implication: a suite authored alongside the code by an agent may encode the implementation's shortcuts. Check for
    special-cased fixtures and tests modified to match the code.
- **Happy-path bias.** BlindSpotEval reports null / negative / empty argument coverage of 34.8% / 23.8% / 38.8% vs >93% for
  booleans; catch-block CFA 0.100; default groups 0.312; 15.6% of failures were wrong oracles. https://arxiv.org/abs/2610.32548
  An LLM judge re-deriving cases will share this bias unless it is forced through a checklist.
- **Rubric LLM-as-judge for acceptance-test coverage** (Gherkin, 100 expert-annotated scripts):
  - first-attempt completion rate ECR@1 was 85.4–100%;
  - a smaller model (GPT-4o mini) beat larger ones on accuracy;
  - cost varied 175×.
  Takeaways: use structured JSON outputs, retries, and a model calibrated on labelled examples. https://arxiv.org/abs/2512.01232
- **Prompt Coverage Adequacy** (Harman, Papadakis et al. 2026) measures how well a suite covers requirements in a prompt via
  LLM attention. Reported to find 30+% more faults than code-coverage guidance. Research-grade, not a drop-in tool.
  https://arxiv.org/abs/2607.02057

Mitigations, folded into the procedure: blind derivation; per-obligation structured verdicts; every "covered" claim needs
an executed artefact (trace, coverage hit, killed mutant); ensemble or second-judge disagreement triggers a dynamic check. [INFERENCE]

