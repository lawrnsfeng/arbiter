# Roadmap

Python goes first. Each step names the evidence that motivates it, a change, an acceptance check and its cost.

Cost is given in **model calls**, because arbiter records no token counts yet (adding them is step P0.1).
Measured averages at `standard` effort, from [benchmarks.md](benchmarks.md):

| Workload | Model calls per item | Wall time per item |
|---|---|---|
| Seeded case | about 16 | about 3–4 min |
| Martian PR | 20–106 (median about 40) | 13–47 min |

Rule for every step: change one thing, rerun the narrowest benchmark that covers it, and record the numbers in
`benchmarks.md` with the commit hash. A step that lowers held-out recall by more than 0.05 is reverted.

## Phase P: Python to target

Exit criteria before Phase L starts:

| Benchmark | Target |
|---|---|
| Held-out seeded Python set | precision ≥ 0.80, recall ≥ 0.70, 0 clean-case findings, over 3 runs, with the spread reported |
| Martian sentry, all 10 PRs | F2 Core ≥ 0.60 and precision ≥ 0.60 |
| Verdict | every proven functional bug that breaks the documented contract on a reachable public path blocks |

### P0. Measurement first (no tuning yet)

| # | Change | Why | Acceptance | Cost |
|---|---|---|---|---|
| P0.1 | Record tokens and cost per call in `coverage.json`: the harness's usage output, or a direct API client (see I1) | Budgets in this file are call counts only | `report.json` has tokens per role | none |
| P0.2 | Attribute every main finding to its agents, and compute per-agent precision and recall in `arbiter eval` | Revisions so far were guessed from reading false positives; per-agent numbers say where to cut | Per-agent table printed by `eval seeded run` | none (re-scores existing runs) |
| P0.3 | Split the seeded corpus into **dev** and **held-out**, and never tune on held-out | Briefs were tuned twice on the scoring set (benchmarks §5) | `eval seeded run --split dev\|heldout` | none |
| P0.4 | Run the r2 configuration 3× on the Python cases | Run-to-run variance is unmeasured | Mean and spread for P and R | about 3 × 7 × 16 ≈ 340 calls |

### P1. Core defects the data exposed

| # | Change | Evidence | Acceptance |
|---|---|---|---|
| P1.1 | **Merge rule.** Keep one finding per location, but choose the representative by support: the most finder agents, then a functional axis with a `proof_plan`, then priority. Alternatively, keep findings from different axis families apart and dedup only in the report. | go-02 r2: a weak A3 security claim became the representative and was disputed, which hid the proven shadowed-`err` bug | go-02 and python-03 both correct in the main section; unit test covering both shapes |
| P1.2 | **Severity calibration.** A verified functional finding with a confirmed E3/E4 proof that the documented contract is broken on a reachable public path is `block`, unless the threat model or repo rules say otherwise. The panel may lower severity only with a cited reason. | python-01 and python-02 were proven but rated should-fix, so the verdict was PASS | All 5 functional Python bug cases block; clean cases unchanged |
| P1.3 | **Sandbox `uv sync` on real repos.** Find out why sentry fails with "Could not create temporary file" (suspected cause: the temp dir or a uv cache hard-link across bind mounts `[INFERENCE]`). | No proof that needed sentry's imports could run | sentry `wt` sync exits 0; a pytest-based E4 runs inside sentry |
| P1.4 | **Lint-code → axis map for Python gate hits.** For example, ruff `B006` → edge, `BLE001`/`S110` → errors, `S608` → security, `RUF006`/`ASYNC*` → concurrency. Mapped hits then support or confirm agent findings instead of standing alone as idiom. | 5 of 13 unmatched r2 findings were gate hits filed as idiom | Gate hits merge with the agent finding on the same line |

### P2. Python agent quality

| # | Change | Evidence | Acceptance |
|---|---|---|---|
| P2.1 | Python cookbook recipe for a dropped `asyncio.create_task` reference: an E5 run under `python -X dev` plus `gc.collect()` that shows "Task was destroyed but it is pending" (feasibility unverified) | python-04 line 19 stays "verified but unproven" in every run | python-04 recall 2/2 |
| P2.2 | Evolvability on real code: use the P0.2 per-agent numbers to decide between 3/3 votes for evolvability, a stricter SPEC brief, or moving SPEC findings out of precision scoring | sentry FPs are mostly docs, design, idiom and spec | sentry precision ≥ 0.60 without losing Core hits |
| P2.3 | Python 3.12+ idiom findings must still cite repo precedent; teach A6a the version-gated table only when `requires-python` allows it | python-05 `Generic[T]` hit 2 of 3 runs, 0 of 1 with Haiku | python-05 must 3/3 on Opus and ≥ 2/3 on Haiku |
| P2.4 | Cheap-model profile: route V and P to a stronger model, and finders to Haiku or DeepSeek | Haiku: precision 0.69 but recall 0.62; on Python it missed the injection in python-03 and every idiom or design finding in python-05 | Haiku-finder profile recall ≥ 0.70 on held-out |

### P3. Python datasets, in order of cost

Run each benchmark only after the previous one passes its gate. "Calls" are estimates from the averages above.

| # | Dataset | Ground truth | Python scope | Estimated calls | Gate to move on |
|---|---|---|---|---|---|
| D1 | **Seeded Python v2:** 30 cases, 15 dev and 15 held-out, covering every functional axis plus idiom and design; half derived from real Python bug-fix commits. BugsInPy is a candidate source `[from memory; verify]` | `expected.json` written by the case author, with a throwaway repro per bug | Python only | about 480 per run | Phase P seeded targets |
| D2 | **Martian sentry, all 10 PRs** | Martian golden comments | sentry (Python) | about 400–600 | F2 Core ≥ 0.60 |
| D3 | **c-CRAB** `[AX-S8]`: review comments turned into executable tests, the closest match to arbiter's E4 rule | Executable tests | Python share to be checked | depends on subset; start with 30 items | Report pass-rate vs published tools |
| D4 | **SWR-Bench** `[AX-S7]`: 1,000 verified PRs with full repo context | LLM judge with about 90% human agreement | Python subset to be checked | 50 PRs ≈ 2,000–3,000 | Precision above the published best 16.65% by a wide margin |
| D5 | **CRBugBench** `[AX-S9]`: 1,800 tasks; tests misleading PR descriptions | Bug labels, top-k | Python subset to be checked | 50 tasks ≈ 2,000 | Recall vs the published 71.9% top-5 |
| D6 | **ContextCRBench, AACR-Bench** `[AI-§3]` | Hunk-level labels; expert comments (SEM-F1) | Multi-language | sample 50 | Comparison only |
| D7 | Python security set: a curated vulnerability-fix corpus such as CVEfixes `[from memory; verify]` | CVE fix commits | Python | 50 items | CWE-wise recall of A3 with zero clean-case blocks |

All published numbers above come from the papers' abstracts as quoted in `research/`. Before running each
benchmark, open its repository and confirm three things: the licence, the Python subset size, and the scoring
script. Some benchmarks may have leaked into model training (Martian notes this risk), so held-out seeded cases
stay the primary regression gate.

### P4. Hierarchical units: the §5 A/B (`--decompose`)

`research/research-decompose-hierarchical.md` §4 is built behind `--decompose hier|hier-split` (methodology §3.1);
`ocr` stays the default until this A/B passes.

| # | Change | Evidence | Acceptance | Cost |
|---|---|---|---|---|
| P4.1 | Run arms A (`ocr`), B (`hier`, B=150), B′ (`hier-split`) and optionally C (`hier`, `ARBITER_UNIT_BUDGET=75`) at `standard` effort with the same models and k, twice each, on the PRs whose unit sets differ between A and B: the seeded corpus (regression), 12 new seeded large/cross-unit Python cases, SWR-Bench Python PRs over 150 churn, Martian sentry, and a CRBugBench Python sample (≈195 issues in total for 80% power on +10 pp) `[DH-§5]` | Oversized units exist only on real PRs: 11 sentry units over 150 churn, none on seeded or the SWR sample `[DH-§4.0]` | Adopt `hier` as the default only if all hold: Δrecall ≥ +5 pp with the 95% CI excluding 0; precision non-inferior (Δ ≥ −2 pp at the lower CI); cross-unit recall non-inferior (Δ ≥ −5 pp); the seeded regression is exact; finder calls rise ≤ +30% on the changed PRs. One interim look at 50%: stop for futility if the upper CI of Δrecall < +3 pp, for harm if Δcross-unit recall < −10 pp with its upper CI < 0. If B passes but B′ fails on cross-unit recall, keep the manifest and widened acceptance even if the split is dropped | sentry alone: ≥ +22% finder calls at standard `[DH-§4.5]`; plus 1 contract call per PR with interface changes |

## Phase L: the other languages

1. Port the P1 core fixes; they are language-neutral.
2. Build seeded v2 dev/held-out sets for Go, TypeScript and Rust. Rust needs its own: no public review benchmark covers Rust `[AI-§3]`.
3. Run Martian grafana (Go) and cal.com (TS) in full; their samples scored F2 0.20 and 0.29.
   - Fix dependency fetch for real JS monorepos first: yarn and pnpm are missing, and grafana's frontend packages failed.
4. Language-specific proof recipes:
   - Go: `-race` with a driven test.
   - Rust: Miri in the sandbox with a pre-built sysroot.
   - TS: `node --test` with transform types.

## Phase I: an independent agent

Today arbiter is a CLI that drives other harnesses (`omp -p`, `claude -p`). The steps to make it an independent
agent, each building on the one before:

| # | Step | Why |
|---|---|---|
| I1 | **Own model client.** Direct calls to the Anthropic, OpenAI-compatible and DeepSeek APIs, with structured JSON output, retries with back-off on 429 using `retry-after`, and per-call token and cost accounting | Removes the harness dependency and gives exact cost. Rate-limit handling becomes precise instead of a 30 s retry |
| I2 | **Own tool loop for agents.** Read, grep and glob served by arbiter itself, so finders need no harness tools; the proof agent's commands go through a tool that *only* calls `sandbox.exec_` | Closes the main safety gap: the proof agent can no longer run anything on the host |
| I3 | **Per-role model routing and cross-model review** | Cross-model review raised high-severity recall in Greptile's data `[AI-§4 #9]`; cheap finders with a strong verifier and prover match the cost goal |
| I4 | **Convergence controls.** Diff-only re-review of a new push, no repeated findings, and a round cap | Anthropic: one-round pass rate 65% → 78% `[AI-§4 #8]` |
| I5 | **Feedback-learned suppression.** Store accepted and dismissed findings per repo, and suppress near-duplicates of dismissed ones | The strongest production precision gain after context `[AI-§4 #3]`; needs real traffic |
| I6 | **Integrations.** SARIF output; a GitHub Action / CI gate using the exit-code contract; devrem `reviewer` integration; PR inline comments via `gh` | The plan deferred devrem integration |
| I7 | **Sandbox hardening.** cgroup CPU and memory limits; an egress proxy for the dependency-fetch step; run the whole agent process in a sandbox whose only network access is the model API | `[DV-§4]` rules 4 and 9 are only partly met today |
| I8 | **Continuous evaluation.** The seeded dev set runs on every brief or core change in CI; held-out and Martian run on release; results append to `benchmarks.md` automatically | Prevents silent regressions as briefs evolve |

## Open questions to settle with measurements, not opinion

- Is SPEC worth its cost on real PRs, given that PR text is often thin? Use the P0.2 per-agent numbers.
- Should evolvability count in headline precision, or be scored separately, as SWR-Bench does by type?
- Does k=3 at deep effort pay for its 3× finder cost on real PRs? Use Martian with deep vs standard on D2.
