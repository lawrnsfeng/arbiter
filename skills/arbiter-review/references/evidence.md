# Evidence ladder

Source: `research/research-decompose-verify.md` §3a–3c, copied verbatim. Source ids (S4…S33) refer to that file's Sources table.

## 3. Verification ladder

### 3a. Evidence levels (cheapest first)

| Lvl | Evidence | Typical cost | What a **positive** proves | What a **negative** means |
|---|---|---|---|---|
| E0 | Reading only (LLM reasoning) | ~0 | Nothing on its own. Intrinsic self-correction often makes answers worse. Debate does no better than self-consistency at equal cost (S19). | — |
| E1 | Compiler / type checker / linter output on the cited line | seconds | Type, borrow, unused or misuse errors, with certainty | The tool can't see it. Not proof the code is OK. |
| E2 | SAST rule hit plus dataflow trace (`--dataflow-traces`), new against `--baseline-commit` | seconds to minutes | Source→sink path exists syntactically | Rule gap. Note: feeding SAST output to an LLM **as context** dropped precision to 2.8% (Hybrid-Review, S5). Use SAST as an oracle, not as a prompt. |
| E3 | Throwaway snippet / REPL run of the exact expression | seconds | Language-semantics claims ("this returns None", "slice aliases") | The claim is false. Drop it. |
| E4 | **Reproduction test:** fails on HEAD, passes on a minimal fix | minutes | Behavioural bug, with certainty. Generated tests used as a filter **doubled** SWE-Agent precision (S16). | Unreproduced ≠ false. BRT Agent produced plausible repro tests for only 28% of 80 real Google bugs (S17). Downgrade the finding to "suspected", don't delete it. |
| E5 | Dynamic checker: `-race`, Miri, TSan/ASan, `-X dev` | minutes (Miri and TSan are slow) | Race, UB or leak on an executed path. ASan "perfect verification" is the Naptime approach (S14). | Path not executed (S24, S27). Drive it with E4 or E6. |
| E6 | Property test / fuzz with a minimized counterexample | minutes, time-boxed | Edge-case bug, with a shrunk input | Absence within the time box only |
| E7 | Mutation testing on the diff (`--in-diff`, `--incremental`) | minutes to hours | "Tests don't cover X": surviving mutant = concrete proof | Killed mutants ≠ good assertions. Equivalent mutants are noise. Meta's LLM equivalence detector scored P 0.79 / R 0.47 raw (S18). |
| E8 | Benchmark A/B with statistics (benchstat ≥10 runs, criterion baseline) | minutes | Perf regression or win, with a significance figure | Noise. LLMs show near-zero recall on perf bugs (S4), so perf findings **require** E8. |
| E9 | Integration / e2e (Playwright, containers) | 10+ minutes | Cross-boundary behaviour | Environment drift |

### 3b. Finding class to required proof

| Finding class | Minimum proof to report as "confirmed" | Stronger | Cost | Notes |
|---|---|---|---|---|
| Logic / functional bug | E4 repro test | E6 counterexample | M | The oracle must come from **spec, docs, caller contract**, not from the code under test. Buggy code steers LLM tests into asserting the bug (S20). Pass-oriented generators "validate bugs" (S21). |
| Edge case / input validation | E3 snippet or E6 | E4 regression test with the minimized input | L–M | Go fuzz stores the failing input as a regression seed automatically (S25). |
| Data race / concurrency | E5 `go test -race` / TSan / Miri report with both stacks | E4 stress test (`-count=100`) | M–H | Report the race output verbatim. No output = "suspected". |
| Memory / UB (unsafe Rust, FFI) | E5 Miri or ASan | E6 fuzz under ASan | H | Miri's own README: no UB found ≠ sound (S27). |
| Resource leak | E5 `-X dev` ResourceWarning plus tracemalloc site | E4 | L | S33 |
| Security (injection, authz) | E2 dataflow trace **plus** E3/E4 exploit-style input reaching the sink | E6 | M | RepoAudit's validator (path-condition satisfiability) reached 78.43% precision (S15). |
| Performance regression | E8 with benchstat/criterion delta and p-value | profile | M | Never report from reading alone (S4). |
| API / semver break | E1-class tool: `cargo semver-checks`, `apidiff`, `griffe check` | E4 compile of a caller fixture | L | Deterministic, high precision. |
| Type error | E1 `tsc --noEmit` / pyright strict / clippy | — | L | |
| Weak / missing tests | E7 surviving mutant on changed lines | E4 test that kills it | M–H | Run on the diff only (S29, S30). |
| Dead code / unused export | E1 compiler warning, or `codegraph callers` = 0 plus a grep for dynamic use | — | L | |
| Idiom / style | E1 linter rule ID, or a cited canon rule plus exact line | — | L | No execution possible. Label "convention" and cite the rule. |
| Design / clean code | Concrete counterfactual (what breaks or costs more, shown by a caller or a change scenario) plus a graph fact (fan-in, cycle via `codegraph cycles`, layering violation via import-linter / depcruise rule) | — | L–M | Label "judgment". Never gate merge on it alone. |

### 3c. Verifier rules (evidence-backed)

1. **Fail-before / pass-after.** A repro test counts only if it fails on HEAD for the claimed reason (assertion message matches) and passes on a minimal patch. This is the SWT-Bench / BRT definition (S16, S17).
2. **Separate writer and judge.** The agent that claims the bug must not grade it. External signals (exit code, sanitizer report) are the oracle (S19).
3. **Spec-first oracle.** The test author sees signature, docstring and caller contract, not the buggy body (S20).
4. **Tests are read-only.** The verifier may add tests but never edit or delete existing ones. Agents delete or modify tests to pass (S22).
5. **Independent trajectories.** Sample several independent verification attempts rather than one long one (Naptime principle 5, S14). Aggregate several reviews, then filter (S5).
6. **Report the artifact.** Every confirmed finding carries the command, exit code and trimmed output, or the test file path.


## Accepted proof rungs per axis (arbiter gate)

A verified functional finding reaches the main report only with a `confirmed` proof at one of its axis's accepted rungs. Otherwise it is listed as suspected and never blocks. Performance findings without E8 are dropped. E2 (SAST hit) is supporting evidence only and never suffices alone.

| Axis | Accepted rungs |
|---|---|
| logic | E3, E4, E6 |
| edge | E3, E4, E6 |
| errors | E3, E4 |
| resources | E4, E5 |
| concurrency | E4, E5 |
| security | E3, E4 (E2 alone never suffices) |
| privacy | E3, E4 |
| performance | E8 |
| api | E1, E4 |
| data | E4, E9 |
| tests | E4, E7 |
| deps | E1 |
| observability | E4 |
| ops | E1 |
| portability | E1, E4 |
| a11y | E1 |
| spec | E4, E9 |

Evolvability axes (`maintainability idiom design docs`) need no execution proof. They need a `rule` plus either a `precedent` (`path:line` in the repo) or a `rule` that is a linter rule id. Their severity is capped at `should-fix`, except a deep-mode `code_judo: true` finding with a `confirmed` E1 measured fact.

## Effort → allowed rungs

| Effort | Rungs the proof agent may attempt |
|---|---|
| quick | E1, E3 |
| standard | E1, E2, E3, E4, E5, E6, E8 |
| deep | E1–E9 |
