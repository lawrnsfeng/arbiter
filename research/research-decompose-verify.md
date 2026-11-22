# Decomposition and ground-truth verification for an agentic code-review skill set

Access date for every vendor or doc fact below: 2026-11-21.

Tag legend:
- `†` = `[from memory]`. I did not open a source for that command or flag.
- `[INFERENCE]` = my own synthesis. No source states it directly.

## Sources (IDs used below)

| ID | Source | URL |
|---|---|---|
| S1 | SmartBear/Cisco review best practices (vendor page) | https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/ |
| S2 | Liu et al., *Lost in the Middle* (TACL 2024) | https://arxiv.org/abs/2307.03172 |
| S3 | Chroma, *Context Rot* (Jul 2025, 18 models) | https://www.trychroma.com/research/context-rot |
| S4 | Kumar et al., *Bigger Isn't Always Better* (arXiv 2606.15689, Apr 2026) | https://arxiv.org/abs/2606.15689 |
| S5 | Zeng et al., SWR-Bench (arXiv 2509.01494, Sep 2025) | https://arxiv.org/html/2509.01494v1 |
| S6 | OCR `task_template.json` | https://raw.githubusercontent.com/alibaba/open-code-review/main/internal/config/template/task_template.json |
| S7 | OCR `template.go` (PlanRequired / GroupingPlan) | https://raw.githubusercontent.com/alibaba/open-code-review/main/internal/config/template/template.go |
| S8 | OCR `grouping.go` | https://raw.githubusercontent.com/alibaba/open-code-review/main/internal/agent/grouping.go |
| S9 | aider repo map docs and blog; `repomap.py` (`nx.pagerank`) | https://aider.chat/docs/repomap.html · https://aider.chat/2023/10/22/repomap.html · https://raw.githubusercontent.com/Aider-AI/aider/main/aider/repomap.py |
| S10 | CodeGraph CLI reference | https://colbymchenry.github.io/codegraph/reference/cli |
| S11 | SCIP README | https://github.com/scip-code/scip |
| S12 | Greptile graph context docs | https://www.greptile.com/docs/how-greptile-works/graph-based-codebase-context |
| S13 | GitHub CODEOWNERS docs | https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners |
| S14 | Project Zero, *Project Naptime* (Jun 2024) | https://projectzero.google/2024/06/project-naptime.html |
| S15 | RepoAudit (ICML 2025) | https://arxiv.org/abs/2501.18160 |
| S16 | SWT-Bench (NeurIPS 2024) | https://arxiv.org/abs/2406.12952 |
| S17 | Google BRT Agent (Feb 2025) | https://arxiv.org/abs/2502.01821 |
| S18 | Meta ACH, mutation-guided test generation (Jan 2025) | https://arxiv.org/abs/2501.12862 |
| S19 | Huang et al., *LLMs Cannot Self-Correct Reasoning Yet* (ICLR 2024) | https://proceedings.iclr.cc/paper_files/paper/2024/file/8b4add8b0aa8749d80a34ca5d941c355-Paper-Conference.pdf |
| S20 | Zhao et al., misguidance of buggy code in LLM tests (Jul 2026) | https://arxiv.org/abs/2607.22883 |
| S21 | Mathews & Nagappan, LLM test generators validate bugs (Dec 2024) | https://arxiv.org/abs/2412.14137 |
| S22 | ImpossibleBench (Oct 2025) | https://arxiv.org/abs/2510.20270 |
| S23 | Anthropic, Claude Code sandboxing (Oct 2025) | https://www.anthropic.com/engineering/claude-code-sandboxing |
| S24 | Go race detector | https://go.dev/doc/articles/race_detector |
| S25 | Go fuzzing | https://go.dev/doc/security/fuzz/ |
| S26 | `go` alldocs (`list -deps -test`, TestImports) | https://raw.githubusercontent.com/golang/go/master/src/cmd/go/alldocs.go |
| S27 | Miri README | https://github.com/rust-lang/miri |
| S28 | Rust sanitizer (Unstable Book) | https://doc.rust-lang.org/stable/unstable-book/compiler-flags/sanitizer.html |
| S29 | cargo-mutants `--in-diff` | https://mutants.rs/in-diff.html |
| S30 | Stryker incremental | https://stryker-mutator.io/docs/stryker-js/incremental/ |
| S31 | benchstat `main.go` | https://raw.githubusercontent.com/golang/perf/master/cmd/benchstat/main.go |
| S32 | Semgrep CLI reference | https://semgrep.dev/docs/cli-reference |
| S33 | Python Development Mode | https://docs.python.org/3/library/devmode.html |
| S34 | `cargo metadata` | https://doc.rust-lang.org/cargo/commands/cargo-metadata.html |
| S35 | grimp usage | https://grimp.readthedocs.io/en/stable/usage.html |
| S36 | dependency-cruiser README | https://github.com/sverweij/dependency-cruiser |
| S37 | madge README | https://raw.githubusercontent.com/pahen/madge/master/README.md |
| S38 | cargo-modules README | https://raw.githubusercontent.com/regexident/cargo-modules/main/README.md |
| S39 | cargo-semver-checks README | https://raw.githubusercontent.com/obi1kenobi/cargo-semver-checks/main/README.md |
| S40 | griffe API-break checking | https://mkdocstrings.github.io/griffe/guide/users/checking/ |
| S41 | Go `apidiff` package docs (from a synthesized search answer; page not opened directly) | https://pkg.go.dev/golang.org/x/exp/apidiff |
| S42 | mutmut, gremlins, atheris, jazzer.js, cargo-fuzz, rapid, fast-check READMEs | github.com/boxed/mutmut · go-gremlins/gremlins · google/atheris · CodeIntelligenceTesting/jazzer.js · rust-fuzz/cargo-fuzz · flyingmutant/rapid · dubzzz/fast-check |
| S43 | criterion CLI · pytest-benchmark usage · vitest features | https://bheisler.github.io/criterion.rs/book/user_guide/command_line_options.html · https://pytest-benchmark.readthedocs.io/en/latest/usage.html · https://vitest.dev/guide/features.html |

---

## 1. Decomposition

### 1a. Techniques

| Technique | What it does (verified) | Strength for review | Weakness / caveat | Src |
|---|---|---|---|---|
| **Repo map, aider style** | Tree-sitter pulls definitions and references. It builds a file graph with an edge per dependency and ranks it with `nx.pagerank` (personalised by chat files). It keeps the top identifiers that fit `--map-tokens` (default 1k). | Cheap global "skeleton" (signatures only) for each subagent. It points the model to files to open. | Ranks by reference count, not by change impact. It is syntactic, so dynamic dispatch is approximate. | S9 |
| **CodeGraph CLI** (`codegraph`) | Commands: `impact <sym> --depth N`, `callers`, `callees`, `implementations --depth`, `affected [files...]`, `files --format package`, `cycles`, `explore`, `node`, `status --strict`. | `affected` finds test files hit by changed files through transitive imports, so it doubles as a test-selection oracle. `files --format package` splits a monorepo by nearest `package.json`. `cycles` exits 1 when cycles exist. | `impact` truncates on hot symbols (`"truncated": true`). `affected` stops at process boundaries (HTTP/queue) unless you pass `--cross-tier`. It warns when a file is `changedOnDisk`, so run `codegraph sync` first. | S10 |
| **SCIP index** (Sourcegraph) | Protobuf index for go-to-definition, find-references and find-implementations. Indexers: scip-python (a pyright fork), scip-typescript, rust-analyzer, scip-go (repo exists). | Compiler-precise references, better than tree-sitter guesses. | Needs a build or index step per language. **Conflict:** your rules forbid rust-analyzer, so use CodeGraph plus cargo-modules for Rust. | S11 |
| **Greptile graph** (vendor) | Indexes directories, files, functions, calls, imports and variables. Per changed function it queries dependencies, callers, and "similar patterns" for consistency checks. | Same idea as CodeGraph `impact` plus a pattern-consistency query. | Closed source. The docs are marketing-level with no precision numbers. | S12 |
| **OCR semantic grouping** | One `GROUPING_TASK` LLM call sees **metadata only** (path, status, churn) and returns groups as integer indices. Any error falls back to per-file groups. `enforceGroupTokenBudget` splits over-budget groups. `maxFilesPerGroup = 10`. | Cheap, because it sends no diff content. The index-based output avoids truncation. | The grouping is semantic, not dependency-proven. | S8 |
| **OCR thresholds** | `GROUPING_MIN_FILES=4`: below 4 files, no LLM grouping. `GROUPING_BUNDLE_LINE_THRESHOLD=200`: under 4 files and under 200 changed lines, bundle into one group, else one group per file. `PLAN_MODE_LINE_THRESHOLD=50`: plan phase when any single file has ≥50 changed lines. `PLAN_MODE_GROUP_LINE_THRESHOLD=100`: plan phase when ≥2 files total ≥100 lines. `MAX_REVIEW_ROUNDS=2`, `MAX_TOKENS=200000`. A file whose diff exceeds 80% of `MAX_TOKENS` is dropped. | Concrete, tested defaults to start from. | The bundle threshold is a heuristic. The code comment says one round's attention "is spread too thin" past the ceiling. | S6, S7, S8 |
| **Language-native module graph** | `go list -deps -test -json`, `cargo metadata`, `cargo modules dependencies`, grimp, dependency-cruiser and madge (§2). | Ground-truth package boundaries and import edges. Use them to cluster hunks and to order the review: leaves first. | Import graphs miss runtime wiring (DI, reflection, plugin registries). | S26, S34–S38 |
| **CODEOWNERS** | Gitignore-like patterns, and the last match wins. Read from `.github/`, then root, then `docs/`. The base-branch copy applies. `!` negation does not work. | Free human-curated module boundaries, and owner = reviewer context. | Ownership is not coupling. Treat it as a tiebreaker only. | S13 |
| **Change-impact / blast radius** | Changed symbols → `codegraph impact`/`callers` → callers outside the diff become **read-only context** for the unit, not review targets. | Catches broken callers that the diff never touches. | Depth above 2 explodes. Cap the depth and report truncation. | S10 |

### 1b. Sizing evidence

| Evidence | Finding | Strength | Src |
|---|---|---|---|
| Cisco/SmartBear (2006, human reviewers) | Review ≤200–400 LOC at a time. Defect finding falls beyond 400 LOC, at rates above 500 LOC/h, and after 60 minutes. The page claims "70–90% defect discovery" for 200–400 LOC over 60–90 minutes. | Vendor-run study on humans. Directional only. | S1 |
| *Bigger Isn't Always Better* (2026) | **Diff size is the dominant predictor of LLM review quality.** F1 is 0.657 on diffs under 10 lines and 0.043 on diffs over 150 lines. Real PRs score F1 0.066 against 0.847 on synthetic bugs. Recall on performance bugs is near zero. | Preprint, n=150, 5 models. The size effect is very large. | S4 |
| Lost in the Middle (2023/24) | Accuracy is highest when the relevant information sits at the start or end of the context, and drops in the middle. | Peer-reviewed. Older models. | S2 |
| Context Rot (Chroma 2025) | Performance falls with input length in all 18 models, even on simple tasks. Focused prompts (~300 tokens) beat full prompts (~113k) in every model family, thinking modes included. Distractors hurt more at long lengths. In Chroma's NIAH variant, needle position made no notable difference. | Vendor tech report with a replication kit. | S3 |
| SWR-Bench (2025) | Benchmark PRs average 6.57 files and about 118 added / 64 deleted lines. The best tool reached only 16.65% precision. Precision is the binding constraint. Aggregating multiple reviews raised F1 by up to 43.67%. | 1000 manually verified PRs. | S5 |

### 1c. Recommended unit sizing

| Parameter | Value | Basis |
|---|---|---|
| Changed lines per review unit | **Target ≤150, hard cap 200.** Split by symbol above that. | S4 cliff at >150 lines; OCR bundle at 200 (S6); Cisco 200–400 (S1) |
| Files per unit | ≤10 | OCR `maxFilesPerGroup` (S8) |
| Plan phase | Any file ≥50 changed lines, or ≥2 files totalling ≥100 | OCR (S7) |
| No grouping step | Under 4 files: bundle if total under 200 lines, else one unit per file | OCR (S7) |
| Context per unit | Diff, then a signatures-only map, then the callers/callees slice. Never whole unrelated files. Put instructions and the diff at the **start and end**. | S2, S3, S9 |
| Concern split | One finding class per subagent pass (correctness / concurrency / security / idiom-design) on the same unit. Per S5, aggregate several reviews, then filter. | S5 |
| Clustering key | Package/crate/module from §2 graphs, then CODEOWNERS as tiebreak, then an LLM grouping fallback | S8, S13, S26–S38 |

Size thresholds measure **churn, not file length** (OCR `diffsChurn`).

[INFERENCE] Keep each unit's assembled context well below the window, so most of it is relevant. Chroma shows irrelevant tokens alone degrade results. I have no source giving a token number.

---

## 2. Per-language command cookbook

`V` = verified in the source column. `†` = from memory. Every command runs in the sandbox from §4.

| Task | Python | Go | Rust | TypeScript |
|---|---|---|---|---|
| **Enumerate modules** | `grimp.build_graph('pkg')`, then `.modules` and `.find_children()` V (S35) | `go list -json ./...` V (S26) | `cargo metadata --format-version 1 --no-deps` (`packages`, `targets`, `workspace_members`) V (S34). `cargo modules structure` V (S38) | `codegraph files --format package` V (S10). `tsc -b` with project references † |
| **Dependency graph** | grimp `find_upstream_modules` / `find_downstream_modules` / `find_matching_direct_imports("a.* -> b.*")` V (S35). `pydeps` †. `import-linter` (`lint-imports`) † | `go list -deps -test -json ./...` with `Imports`, `Deps`, `TestImports`, `XTestImports` V (S26) | `cargo metadata` `resolve` graph V. `cargo modules dependencies --lib --acyclic` (cycle error) V (S38) | `npx depcruise src --include-only "^src" --output-type json` V (S36). `madge --circular --ts-config tsconfig.json src` (`--circular`, `--json`, `--depends`) V (S37) |
| **Graph-agnostic** | `codegraph impact <sym> --depth 2 --json`; `codegraph affected <files>`; `codegraph cycles` V (S10) | same | same (avoid rust-analyzer per your rules) | same |
| **Single test** | `pytest path/test_x.py::test_name -x` † | `go test -run '^TestX$' -count=1 ./pkg` † (`-count` V S26) | `cargo test test_name -- --exact` † | `npx vitest run file.test.ts -t "name"` † |
| **Property testing** | Hypothesis `@given(st.integers())` † | `rapid.Check(t, func(t *rapid.T){...})` V (S42). `testing/quick` (frozen) † | `proptest! { ... }` †. quickcheck † | `fc.assert(fc.property(fc.string(), ...))` V (S42) |
| **Fuzzing** | atheris: `with atheris.instrument_imports(): ...`, `atheris.Setup(sys.argv, f)`, `atheris.Fuzz()` V (S42) | `go test -fuzz=FuzzX -fuzztime=60s ./pkg`. Failing input goes to `testdata/fuzz/FuzzX/<hash>` and becomes a regression test. Coverage only on amd64/arm64. Per-input timeout is 1 s. V (S25) | `cargo fuzz init` / `add <t>` / `run <t> -- -max_total_time=60` (init/add/run V S42; the time flag †) | `npx jazzer FuzzTarget`; Jest `it.fuzz(...)` via `@jazzer.js/jest-runner` V (S42) |
| **Mutation (test strength)** | `mutmut run "pkg.mod.func*"`, then `mutmut browse` V (S42). cosmic-ray † | `gremlins unleash` V (S42). go-mutesting † | `cargo mutants --in-diff <(git diff base)` V (S29). Edits to test code alone yield no mutants. | `npx stryker run --incremental --force --mutate src/a.ts:5-7` V (S30) |
| **Sanitizer / race** | `python -X dev` (faulthandler, ResourceWarning, asyncio debug, malloc debug hooks) plus `-X tracemalloc=5` for allocation sites V (S33) | `go test -race ./pkg`. It finds races **only on executed paths**. Exit code 66. V (S24) | `cargo +nightly miri test` catches UB, data races and leaks on executed paths. "No UB found" does not mean sound. No networking or most FFI. V (S27). `RUSTFLAGS=-Zsanitizer=thread cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu` V (S28) | `node --trace-warnings` †. `--unhandled-rejections=strict` † |
| **Type checker as oracle** | `pyright --strict` † / `mypy --strict` † | `go vet` †, `staticcheck ./...` † | `cargo clippy --all-targets -- -D warnings` † | `tsc --noEmit -p tsconfig.json` † |
| **SAST** | `semgrep scan --config p/python --baseline-commit $BASE --dataflow-traces --json` V (S32). `bandit -r` † | semgrep (same flags) V. `gosec ./...` †. `govulncheck ./...` † | semgrep V. `cargo geiger` † (unsafe census). `cargo audit` † | semgrep V. `eslint-plugin-security` †. CodeQL † |
| **API break** | `griffe check -s src pkg -a <base-ref>` V (S40) | `apidiff` (sorts changes into incompatible and compatible) V (S41). `gorelease` (S41 secondary) | `cargo semver-checks --baseline-rev <base>` V (S39) | `api-extractor` † |
| **Benchmark** | `pytest --benchmark-autosave`, then `--benchmark-compare --benchmark-compare-fail=mean:5%` V (S43) | `go test -run='^$' -bench=. -count=10 > old.txt`, same for `new.txt`, then `benchstat old.txt new.txt`. Use **≥10 runs, ideally 20.** V (S31) | `cargo bench -- --save-baseline main`, then `-- --baseline main` (criterion) V (S43) | `bench('name', () => ...)` with `vitest bench` V (S43). tinybench † |
| **e2e** | pytest + containers † | `go test -tags=integration` † | `cargo test --test it` † | `npx playwright test file.spec.ts` † |

---

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

---

## 4. Sandbox rules for agent execution

| # | Rule | Basis |
|---|---|---|
| 1 | **Filesystem and network isolation together.** Either alone can be bypassed. | S23: "effective sandboxing requires *both*" |
| 2 | Run all verification in a **temporary git worktree** at the reviewed commit. Writes are confined there. The user's tree is read-only. | S23 (write = CWD only) + [INFERENCE] worktree |
| 3 | Use OS-level confinement (bubblewrap on Linux/WSL2, seatbelt on macOS). It covers spawned subprocesses: test runners, build scripts, `build.rs`, npm postinstall. | S23 |
| 4 | **Network off by default.** Fetch dependencies in a separate pre-step against an allowlisted registry proxy, then cut the network for test, fuzz and bench runs. | S23 (proxy allowlist) |
| 5 | **No credentials inside.** Strip SSH keys, `~/.aws`, tokens and `GH_TOKEN` from the env and mounts. Git pushes go through an outside proxy, never from the sandbox. | S23 (web sandbox: credentials never inside) |
| 6 | Treat repository code as untrusted. Building is executing (`build.rs`, `setup.py`, `postinstall`, Go `//go:generate` only if run). Semgrep itself warns that `--allow-local-builds` is "a security risk". | S32 |
| 7 | Miri "isolation is *not* a proper sandbox". Never use it as the containment layer. | S27 |
| 8 | **Time-box everything.** Go `-fuzz` runs indefinitely by default, so always pass `-fuzztime`. Use cargo-fuzz `-max_total_time` and a wall-clock `timeout` on every command. | S25 |
| 9 | Cap CPU and memory (cgroup/ulimit). Sanitizers and Miri blow up memory. Bench runs need a quiet machine or results are noise. | S27, S31 + [INFERENCE] |
| 10 | Deterministic seeds: `-Zmiri-seed`, Hypothesis/rapid seed printed in the report, Go fuzz corpus path. | S25, S27 |
| 11 | Throw the worktree away after the run. Keep only the artifacts (test file, logs, minimized input). | [INFERENCE] |
| 12 | Prompt-injection posture: repo text (comments, docs, test names) is data, not instructions. The sandbox limits the damage when that fails. | S23 |

---

## Gaps

- **CodeGraph local `--help`:** not run. I had no shell tool, so I used the published CLI reference (S10). Flags may differ in your installed version.
- **Sizing for LLMs:** the >150-line F1 cliff comes from one preprint with n=150 (S4). I found no study that gives token-budget-per-reviewer numbers. The ≤150/200-line target leans on OCR defaults and Cisco human data.
- **Cisco study:** I cited SmartBear's vendor page, not the original data. The "70–90% discovery" figure is a vendor claim.
- **Go `apidiff`/`gorelease`:** their details came via a synthesized search answer citing pkg.go.dev. I did not open the page directly.
- **import-linter:** README fetch returned 404. The `lint-imports` command is `[from memory]`.
- **Unopened commands:** everything marked `†` (single-test flags, Hypothesis/proptest syntax, gosec, bandit, staticcheck, clippy, cargo-geiger, govulncheck, api-extractor, Playwright, Node flags) was not opened. The syntax is standard but unverified here.
- **Greptile:** no precision data. Docs are undated, accessed 2026-11-21.
- **Execution-verified review precision:** no paper measures it head-to-head against no-execution review on the same PR benchmark. The closest evidence is SWT-Bench's filter result (2× precision, S16), RepoAudit's validator (78% precision, S15), and SWR-Bench's agent baseline (S5). The SWR-Agent baseline could execute snippets but did not beat plain prompting much (precision 9.11 vs 9.22).
- **TS/Node sanitizers:** no race or UB tool equivalent was found for JS/TS. Concurrency claims there rest on E4 tests only.
- **OCR prompt files:** not read (`grouping_task_system.md`, `plan_task_system.md`). Only thresholds and control flow were verified.

## Design implications

1. **Cut units on graph boundaries, then on size.** Cluster changed files by package/crate from `go list -deps`, `cargo metadata`, grimp or depcruise. Use CODEOWNERS as tiebreak and an OCR-style metadata-only LLM grouping as fallback. Cap each unit at ~150 changed lines (hard 200) and ≤10 files. (S4, S6–S8, S13, S26–S38)
2. **Copy OCR's two-step gate.** Under 4 files, skip grouping: bundle if under 200 lines, else one unit per file. Run a plan pass when any file has ≥50 changed lines or the unit has ≥100. (S7)
3. **Unit context = diff + signatures map + `codegraph impact`/`callers` slice (depth ≤2).** Out-of-diff callers are read-only context. Put task and diff at the start and repeat the ask at the end. No whole unrelated files. (S2, S3, S9, S10)
4. **One concern per pass:** correctness, concurrency/UB, security, idiom-design. Then aggregate and dedupe in a separate merge step. This gave up to +43.67% F1 in SWR-Bench. (S5)
5. **Make the ladder a hard gate.** A finding is "confirmed" only with its class's minimum evidence from §3b. Otherwise it is "suspected" (shown separately, never blocking). Perf findings without E8 are dropped. (S4, S16, S19)
6. **Run a separate verifier subagent with spec-only inputs.** It writes a fail-before/pass-after test from signature, docs and caller contract, never from the suspect body. It may add tests but never edit them. (S16, S20–S22)
7. **Treat "couldn't reproduce" as a downgrade, not a deletion.** About 28% repro rate on real bugs means many true bugs won't reproduce cheaply. (S17)
8. **Use SAST and type checkers as oracles, never as prompt stuffing.** Run them diff-aware (`--baseline-commit`) and attach the rule ID and trace to an LLM finding. Do not feed raw reports to the reviewer. Doing so cut precision to 2.8%. (S5, S32)
9. **Route each claim class to its dynamic checker automatically:** Go goroutine/shared state → `go test -race`; Rust `unsafe`/FFI → Miri, then TSan; Python I/O/async → `-X dev`; parsers/decoders → fuzz with a time box. (S24, S25, S27, S28, S33)
10. **Put a deterministic API-break check in the first pass** (`cargo semver-checks`, `apidiff`, `griffe check`). It is cheap, precise and catches cross-module breaks that unit-scoped agents miss. (S39–S41)
11. **Back test-quality findings with diff-scoped mutation only** (`cargo mutants --in-diff`, `stryker --incremental --mutate file:lines`, `mutmut run "mod*"`). Report surviving mutants, not coverage. (S29, S30, S42)
12. **Wrap every execution in the §4 sandbox:** throwaway worktree, bubblewrap with FS and network isolation, deps fetched before cutting the network, no credentials, wall-clock timeouts. (S23, S25, S27, S32)
13. **Check CodeGraph health first:** run `codegraph sync` and `codegraph status --strict` before decomposing. A stale index gives wrong line numbers and wrong blast radius. (S10)

I skipped running any tool locally and skipped the OCR prompt bodies. The main risk is the sizing cliff: it comes from one small preprint, so measure it on your own PRs before you hard-code 150 lines.

### Critical Files for Implementation
- `internal/config/template/task_template.json` (alibaba/open-code-review): threshold defaults to copy.
- `internal/config/template/template.go` (OCR): `PlanRequired` / `GroupingPlan` logic to port.
- `internal/agent/grouping.go` (OCR): metadata-only grouping, fallback and token-budget splitting.
- `aider/repomap.py` (Aider-AI/aider): tree-sitter + PageRank signature map pattern.
- CodeGraph CLI reference (`impact`, `affected`, `files --format package`, `cycles`): decomposition and test-selection primitives.