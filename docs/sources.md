# Sources

This file lists the papers, benchmarks, standards and engineering write-ups that shaped arbiter, and what
each one changed in the design.

The full research files are in `research/`. They are byte-identical copies of the 2026-11-21 research
session, and each has its own complete source table with URLs.

Keys used in [methodology.md](methodology.md) and [benchmarks.md](benchmarks.md) take the form `[PREFIX-ID]`:

| Prefix | Research file | Its source table |
|---|---|---|
| `AX-` | `research/research-axes.md` | §1 (S1–S33 papers and standards, V1–V5 vendors) |
| `DV-` | `research/research-decompose-verify.md` | "Sources" (S1–S43) |
| `DH-` | `research/research-decompose-hierarchical.md` (2026-11-23) | §2 (D1–D37); `[DH-§n]` cites a section |
| `AT-` | `research/research-accuracy-techniques.md` (2026-11-23) | its source table; the top-8 ranking is the last section |
| `LR-` | `research/research-learned-rules.md` (2026-11-23) | its source table (L1–L38); the phased plan is the last section |
| `CQ-` | `research/research-code-quality-platforms.md` (2026-11-23) | its source table; the ranked platform table is the last section |
| `LD-` | `research/research-leader-approaches.md` (2026-11-24) | §2 table (LD1–LD24) |
| `SEC-` | `research/research-security.md` | §1 (S1–S50) |
| `AI-` | `research/research-ai-review-systems.md` | sections §1–§4 (pipelines, systems, benchmarks, techniques) |
| `PM-` | `research/prior-mint-review-research.md` | OCR, mattpocock, Google eng-practices, pstack code judo |
| canon keys (`P8`, `EP3`, `C-GOOD-ERR`, `GSD`…) | `research/review-<lang>.md` §1 | per-language canon tables |
| `RC` | `research/research-report-cognition.md` (2026-11-26) | §1 (RC1–RC56); findings F1–F59; ranked rules §3 |
| `RP` | `research/research-report-prior-art.md` (2026-11-26) | §1 (RP01–RP55); patterns P1–P23 §3 |
| `RS` | `research/research-report-render-stack.md` (2026-11-26) | §1 (RS1–RS39) |
| `RM` | `research/research-report-components.md` (2026-11-26) | its source table; synthesis in `research/research-report-ux.md`, session log in `research/research-report-log.md` |
| `RA` | `research/research-report-situations.md` (2026-11-26) | its source table (RA1–RA57); how an agent reports per situation S1–S8 |
| own keys per file | `research/research-e2e-{design,adequacy,unhappy,current,prior-art}.md` (2026-11-25), synthesised in `research/research-e2e-best-practices.md` | each file's source table; cited from `skills/e2e-design/references/` and `skills/e2e-judge/references/` |

Claims tagged `[from memory]` or `[secondary]` in the research files were not checked against a primary
page. They are marked the same way here.

## 1. Peer-reviewed papers and preprints

| Key | Work | Claim used | Where it shaped arbiter |
|---|---|---|---|
| AX-S1 | Mäntylä & Lassenius, TSE 2009 | 75% of review defects affect evolvability, not visible function | Evolvability is reviewed, but kept apart from functional findings |
| AX-S2 | Beller et al., MSR 2014 | 75:25 evolvability:functional; Documentation / Structure / Resource / Check / Interface / Logic taxonomy | Axis taxonomy and the functional/evolvability `group` |
| AX-S3 | Bacchelli & Bird, ICSE 2013 | Only 14% of review comments are defects; 65 of 78 defects are logic | Logic gets its own agent (A1a) |
| AX-S4 | Sadowski et al., ICSE-SEIP 2018 | Review motivations at Google | Repo rules override canon |
| AX-S5, AX-S6 | McIntosh et al. MSR 2014; Thongtanunam et al. MSR 2015 | Lax review means more post-release defects; risky files get less scrutiny | `plan_required` risk notes for large units |
| AX-S7 / DV-S5 | SWR-Bench, Zeng et al., arXiv 2509.01494 | Best precision 16.65%, best F1 18.73%; multi-review aggregation up to +43.67% F1; 48% of false positives come from missing context | Precision-first design, verifier panel, deep k=3, finders get repo read access |
| AX-S8 | c-CRAB, arXiv 2603.23448 | Review comments turned into executable tests; design and docs lowest; maintainability 7.9–27% | Execution-based proof; evolvability capped; candidate next benchmark |
| AX-S9 | CRBugBench "Lights-off", arXiv 2610.13668 | Agents run code in only about 10% of turns; they trust misleading PR descriptions | Proof agent is mandatory for main-section functional findings; A0 treats PR text as claims, never as truth |
| AX-S10 | arXiv 2510.05450 | LLM comment resolution rates: readability 43.3%, bugs 41.9%, maintainability 36.2%, design 28.6% | Design findings need a measured fact (A6b) |
| AX-S11 | RevMate, arXiv 2411.07091 | 8.1% / 7.2% acceptance; about 35% rejected as "trivial" | Nit cap of 10; no generic-quality findings |
| AX-S12 | Spadini et al., ICSE 2018 | Test files carry defects too | A1c reviews added tests |
| AX-S21 | Yuan et al., OSDI 2014 | 92% of catastrophic failures come from mishandled non-fatal errors | A2 failure-path agent is always on |
| AX-S22, AX-S23 | Tu et al., ASPLOS 2019 (Go); Qin et al., PLDI 2020 (Rust) | Race detector catches about half of non-blocking Go bugs; Rust blocking bugs live in safe code | "Detector found nothing" is not clean (A4); E5 alone is not soundness |
| AX-S24 | Raemaekers et al. | About one third of library releases break the API | A5 contracts agent |
| AX-S27 | Sadowski et al., CACM 2018 | Review checks may have up to 10% effective false positives; noisy analyzers get disabled | The precision target and the fail-closed philosophy |
| AX-S28 | Spracklen et al., USENIX Sec 2025 | Hallucinated packages: 5.2% (commercial) to 21.7% (open models) | A5b checks that new dependencies exist on the registry |
| DV-S2 | Liu et al., *Lost in the Middle*, TACL 2024 | Information in the middle of the context is used worst | Task stated first and last in every prompt |
| DV-S3 / AX-S32 | Chroma, *Context Rot*, 2025 | Every one of 18 models degrades with input length | Small units; only the reference rows a brief names |
| DV-S4 | Kumar et al., *Bigger Isn't Always Better*, arXiv 2606.15689 | F1 0.657 under 10 changed lines vs 0.043 over 150; real PRs F1 0.066 vs 0.847 synthetic; near-zero performance-bug recall | 150-line unit cap; performance needs E8; synthetic-corpus caveat in the benchmark doc |
| DV-S14 | Project Naptime, Project Zero 2024 | Independent verification trajectories; sanitizer as perfect verifier | Up to 3 independent proof attempts |
| DV-S15 | RepoAudit, ICML 2025 | Path-condition validation reaches 78.43% precision | Security findings need every source→sink hop cited |
| DV-S16 | SWT-Bench, NeurIPS 2024 | Generated tests used as a filter doubled precision | E4 fail-before/pass-after |
| DV-S17 | Google BRT Agent, arXiv 2502.01821 | Plausible repro tests for only 28% of 80 real bugs | Unproven ≠ false: "Suspected" section |
| DV-S18 | Meta ACH, arXiv 2501.12862 | Mutation-guided tests; equivalent-mutant detection P 0.79 / R 0.47 | E7 accepted for the tests axis in deep mode only |
| DV-S19 | Huang et al., ICLR 2024 | LLMs cannot self-correct reasoning without external feedback | Separate writer and judge; exit codes are the oracle |
| DV-S20, DV-S21 | arXiv 2607.22883; Mathews & Nagappan, arXiv 2412.14137 | Buggy code steers generated tests into asserting the bug | Oracle must come from spec, docstring, type or caller (`oracle_source`) |
| DV-S22 | ImpossibleBench, arXiv 2510.20270 | Agents modify tests to pass | Proof agent may never edit existing tests |
| SEC-S40 | PrimeVul, ICSE 2025 | 68.26% F1 on BigVul falls to 3.09% on PrimeVul | Raw LLM vulnerability detection is not trusted without proof |
| SEC-S41 | SecLLMHolmes, S&P 2024 | Renaming variables flips answers in 17–26% of cases | Votes and execution, not single answers |
| SEC-S44 | IRIS, ICLR 2025 | LLM taint specs plus CodeQL: 55 vs 27 of 120 CVEs | SAST as oracle; E2 supporting evidence |
| SEC-S46 – SEC-S49 | Wagner et al.; ZeroFalse; Du et al. (Tencent); "Sifting the Noise" | FP filtering works but loses TPs; CWE-specific prompts beat generic ones | Never-auto-dismiss CWE list; the security brief is CWE-oriented |

## 2. Benchmarks consulted

| Benchmark | Used for | Status in arbiter |
|---|---|---|
| Martian Code Review Bench, offline (`withmartian/code-review-benchmark`, MIT) | Golden comments, Core category profile, F-beta scoring | **Used**: 9-PR sample, see [benchmarks.md](benchmarks.md) |
| SWR-Bench (AX-S7) | Precision/recall reference; multi-review evidence | Not run yet: roadmap |
| c-CRAB (AX-S8) | Executable ground truth from review comments | Not run yet: roadmap |
| CRBugBench (AX-S9) | Bug-finding top-k; misleading PR descriptions | Not run yet: roadmap |
| ContextCRBench, AACR-Bench, Greptile, Qodo, Bugbot resolution, AIDev (AI-§3) | Landscape and vendor numbers | Reference only; vendor benchmarks each rank their own tool first |

## 3. Industry systems and documents

| Key | Source | What arbiter took from it |
|---|---|---|
| AI-§1a | Anthropic `code-review` plugin command file | High-signal gate and false-positive list (`references/exclusions.md`) |
| AI-§1c | Anthropic `claude-security` plugin, `scan-verifier.md` | Verifier V: default FALSE_POSITIVE, refute only with a mitigation read, PREDATES_CHANGE, 3 lenses with 2 votes |
| SEC-S35 | Anthropic `/security-review` command | 17 hard exclusions, 12 precedents (env vars and CLI flags trusted, UUIDs unguessable, tests out of scope, React escapes, SSRF needs host or protocol control) |
| SEC-S36 | Anthropic, "Using LLMs to secure source code" (2026-05-27) | Threat model first; the six-question severity rubric; 90% vs 40% figure |
| SEC-S38 | GitHub Security Lab Taskflow agent | Small tasks with fresh context; `file:line` evidence; deterministic checks moved into tools |
| SEC-S39 | Trail of Bits `fp-check` skills | False-positive checklist and gates |
| AX-V1 | Cursor, "Building a better Bugbot" | Shuffled diff order per pass, majority vote, validator model |
| AI-§4 #10 | Greptile engineering posts | Self-rated confidence is "nearly random"; few-shot examples made the bot worse |
| DV-S6..S8 / PM | alibaba `open-code-review` (OCR) | Unit sizing, `plan_required`, per-language rule files |
| PM | mattpocock `code-review` skill | Standards and Spec as separate checks (A6* vs SPEC) |
| PM | Google eng-practices reviewer guide | Approve when code health improves; review order |
| PM | pstack "thermo-nuclear" code-quality review | Code-judo presumptive-blocker list (A6b, deep mode) |
| DV-S23 | Anthropic, Claude Code sandboxing | Filesystem and network isolation together; no credentials inside |

## 4. Language canons

Each language skill's `references/canon.md` is a verbatim copy of §1 of its `research/review-<lang>.md`, with
keys and URLs:

- **Python:** PEP 8, 20, 257, 572, 3134, 695, 698, 742, 765, 779; typing best practices; asyncio Tasks docs; Google Python Style Guide; Effective Python 3e; Hettinger idioms; python-patterns.guide; Ruff, mypy and pyright docs; the CPython devguide.
- **Go:** Effective Go, Go Code Review Comments, Google Go Style, Uber Go Style, `go vet` and staticcheck docs.
- **Rust:** Rust API Guidelines (C-*), the clippy lint index, rust-unofficial patterns, Effective Rust, the Nomicon and the SAFETY-comment policy, the compiler and std review policies.
- **TypeScript:** Handbook Do's and Don'ts, Google TypeScript Style Guide, typescript-eslint strict, Effective TypeScript, TS 5.x → 7 status.

Security checklists come from:
- research-security.md §3b–§3e (Python, Go, Rust, TypeScript), drawing on OWASP Top 10:2025, CWE Top 25 2025, ASVS 5.0 and the bandit, gosec and semgrep rule sets
- §4 for the supply-chain checks, drawing on pnpm, npm, uv, cargo-deny, OpenSSF Scorecard and SLSA

## 5. Tools that arbiter runs

| Tool | Role |
|---|---|
| bubblewrap 0.11.1 | Sandbox |
| ruff, mypy, pyright, pytest | Python gates (project's own, or ruff via cache) |
| bandit, semgrep (`p/python`, `p/rust`, `p/typescript`) | Analyzer oracles (E2) |
| go build, go vet, golangci-lint or staticcheck, go test, gosec, govulncheck | Go gates and analyzers |
| cargo clippy, rustfmt, cargo test, cargo-deny | Rust gates and analyzers |
| tsc, eslint, the package test script | TypeScript gates |
| codegraph `affected` | Test selection when the repo has a `.codegraph/` index |
