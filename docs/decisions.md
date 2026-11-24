# Decision ledger

This ledger records every technical idea and concern raised for arbiter, whatever happened to it: adopted, adopted behind a switch, proposed, deferred or dropped. Each row names where the idea came from, the evidence, and where the result lives. The reasoning behind the adopted design is in [methodology.md](methodology.md) §2–§5. This ledger also holds what was **not** done, and why.

**Rule:** any new idea, concern, experiment or rejection gets a row here in the same change that raises it. When an idea's status changes, edit its row and add the date; do not delete rows. [CHANGELOG.md](../CHANGELOG.md) says what shipped, and this file says what was decided.

Status values:
- `adopted`: in the code.
- `switch`: in the code, off by default until a test decides.
- `proposed`: researched, not built.
- `deferred`: wanted, postponed on purpose.
- `dropped`: rejected, with the reason.
- `open`: a known concern with no fix yet.

Source keys (`[DV-S4]`, `[DH-D10]`, `[AT-…]`, `[LR-…]`, `[CQ-…]`) resolve through [sources.md](sources.md). The research file for each prefix:

| Prefix | File |
|---|---|
| AT | `research/research-accuracy-techniques.md` |
| LR | `research/research-learned-rules.md` |
| CQ | `research/research-code-quality-platforms.md` |
| DH | `research/research-decompose-hierarchical.md` |

## 1. Architecture and pipeline

| ID | Date | Idea or concern | Status | Decision and evidence | Where |
|---|---|---|---|---|---|
| A-01 | 2026-11-21 | Orchestrate with an LLM coordinator | dropped | Deterministic Python orchestrates; cheap models cannot be trusted to plan, and vote arithmetic must be exact | methodology §3, §4 |
| A-02 | 2026-11-21 | Stdlib-only package | adopted | No supply-chain surface in the reviewer; runs anywhere `uv` does | `pyproject.toml` |
| A-03 | 2026-11-21 | Finders and verifier get bash | dropped | Read, grep and glob only; a prompt-injected agent with bash outside the sandbox could run anything | `harness.py` `Tools` |
| A-04 | 2026-11-21 | Proof agent restricted to `arbiter sandbox exec` | adopted, **open concern** | Proof exit codes are re-read from `RUN/exec`, which sandboxed code cannot write. The proof agent's host bash is limited only by its prompt; the fix is I2 (own tool loop) | methodology §6, roadmap I2 |
| A-05 | 2026-11-21 | Hard proof gate: a functional finding blocks only with a confirmed proof at an accepted rung | adopted | `[DV-S16]` repro tests doubled precision; LLM self-confidence is close to random `[AI-§4 #10]` | `findings.gate` |
| A-06 | 2026-11-21 | Confidence scores as a filter | dropped | Greptile: self-rating "nearly random" `[AI-§4 #10]`; verbalized confidence is overconfident `[AT]` | — |
| A-07 | 2026-11-21 | 3-lens disprove panel with a never-auto-dismiss CWE list | adopted | The strongest measured precision gain `[AI-§4 #2]`; every FP filter loses some TPs `[SEC-S48..S50]` | `findings.tally` |
| A-08 | 2026-11-21 | SAST output pasted into finder prompts | dropped | Cut precision to 2.8% `[DV-S5]`; SAST is an E2 oracle attached afterwards | `gates.py` |
| A-09 | 2026-11-21 | Merge findings at one location under the highest-priority axis | adopted, **open concern** | One f-string query became 3 findings. It hid the proven go-02 bug behind a disputed security claim; the fix is roadmap P1.1 (pick the representative by support) | `findings.merge`, roadmap P1.1 |
| A-10 | 2026-11-21 | Fail closed when more than 25% of agent calls fail | adopted | A rate-limited run reported PASS with zero working agents | `pipeline._withhold` |
| A-11 | 2026-11-21 | Proofs run one at a time | adopted | Proof agents edit `RUN/wt`; parallel runs corrupt fail/pass pairs | `pipeline.proofs` |
| A-12 | 2026-11-21 | bubblewrap sandbox: network off, `$HOME` hidden, env cleared | adopted, **open concern** | No CPU or memory limit yet (`[DV-§4]` rule 9); the fix is I7 | `sandbox.py`, roadmap I7 |
| A-13 | 2026-11-22 | Gate HEAD-vs-base comparison when dependency fetch failed | dropped | The difference may come from the environment, so it is skipped and noted | `gates.py` |
| A-14 | 2026-11-22 | eslint runs on the host when the sandbox is down | dropped | `eslint.config.js` is repo code (found by arbiter's self-review) | `gates.STATIC_OK` |
| A-15 | 2026-11-23 | Repo rule files read from the PR's head | **open concern** | A PR can rewrite its own review policy; Anthropic reads REVIEW.md from the base branch only `[LR]`. The fix is LR phase R0 | `plan._rules`, §5 R0 |

## 2. Models and cost

| ID | Date | Idea or concern | Status | Decision and evidence | Where |
|---|---|---|---|---|---|
| M-01 | 2026-11-21 | Use the harness default model | dropped | It fell through to Opus and drained the token budget during the Martian and SWR runs | CHANGELOG 0.2.0 |
| M-02 | 2026-11-22, confirmed 2026-11-24 | Haiku finders, Sonnet verifier, proof agent and judge | adopted | User decision; cheap independent finders, with the strong model where precision is decided `[AI-§4 #9]`. Confirmed by the 2026-11-23 matrix (benchmarks §3.7): see M-11 | `harness.FALLBACK_MODELS` |
| M-11 | 2026-11-24 | Sonnet finders (Sonnet in every role) | dropped | Matrix, Python+TS, one run each. Seeded and Martian: recall +6 to +12 points, precision −2 to −8, F1 tied. SWR-Bench 40 PRs: P 0.38 vs 0.67, R 0.24 vs 0.26, FP 18 vs 6. Higher cost for no consistent gain | benchmarks §3.7 |
| M-03 | 2026-11-23 | Resolve models from omp roles (`arbiter-finder` or `smol`; `arbiter-verify`) | adopted | User asked for omp roles mapped to Haiku and Sonnet at most; `default` and `slow` are Opus here and never used | `harness.settings` |
| M-04 | 2026-11-23 | Cost ceiling `ARBITER_BLOCKED_MODELS` (default `opus,fable`) applied to the resolved model | adopted | User set Sonnet as the ceiling | `harness._resolve` |
| M-05 | 2026-11-23 | Preflight each model: read a file, answer JSON | adopted | An unconfigured model crashed every omp call after about 80 s | `harness.preflight` |
| M-06 | 2026-11-23 | DeepSeek and GPT models | **open concern** | Untested: only the Anthropic provider is configured. The preflight is the safety net | README Models |
| M-07 | 2026-11-23 | Packaging as a Claude/omp plugin with a marketplace manifest | dropped | User chose `make install` (an `arbiter` command on PATH plus the skills linked into `~/.omp/agent/skills`) | `Makefile` |
| M-08 | 2026-11-23 | Cheap verifier panel first, escalate only split votes to the strong model | proposed | FrugalGPT: up to 98% cheaper at equal accuracy; code cascades save 26% on average `[AT]`. Ranked #2 | AT §ranking |
| M-09 | 2026-11-23 | One verifier lens run by a different model family | proposed | 56.7% vs 42.7% caught; one pairing direction got worse `[AT]`. Ranked #7 | AT §ranking |
| M-10 | 2026-11-23 | Fine-tuning or distillation on review data | dropped | Conflicts with the model-agnostic, stdlib-only design `[AT]` | — |

## 3. Decomposition (review units)

| ID | Date | Idea or concern | Status | Decision and evidence | Where |
|---|---|---|---|---|---|
| U-01 | 2026-11-21 | OCR-style units: at most 150 changed lines, hunk chunks, merge up to 10 files | adopted (default) | F1 0.657 under 10 lines vs 0.043 over 150 `[DV-S4]`, later found confounded `[DH]` | `units.py` |
| U-02 | 2026-11-23 | Hierarchical split: package → module → definition → method → statement (Python, `ast`) | switch (`--decompose hier`) | Smaller inputs help (CRBugBench OR 0.59; *Lost in the End* +37% recall), but syntax splits have not beaten line splits, and per-function chunking was worst `[DH-D5, D18]`. Adopt only if the P4 A/B passes | `decompose.py`, roadmap P4 |
| U-03 | 2026-11-23 | Per-function units as the main split | dropped | Worst chunking strategy by 3.6–5.6 points `[DH]` | — |
| U-04 | 2026-11-23 | Paste caller and callee bodies into each unit | dropped | Pasted bodies hurt; fetching on demand scored 8–9 points higher (JitVul) `[DH-D10]` | `decompose.py` context map |
| U-05 | 2026-11-23 | Changed-symbol manifest and signature map per unit, built with zero model calls | switch | Cross-unit context loss caused 861 FPs in a project-scale study `[DH]` | `decompose.py` |
| U-06 | 2026-11-23 | Accept findings in any changed hunk of the PR; cluster by changed symbol | switch | The own-unit rule discards cross-unit findings `[DH-§4.0]` | `findings.merge` |
| U-07 | 2026-11-23 | One contract pass per PR for signature changes | switch | Covers callers outside the diff `[DH-§4.4]` | `pipeline` CONTRACT job |
| U-08 | 2026-11-23 | Size budget in tokens instead of lines | dropped | Every review-sizing number in the evidence is in changed lines `[DH-§4.1]`; a 24k-character guard trims the context map only | `decompose.py` |

## 4. Accuracy techniques (beyond decomposition)

Ranked in `research/research-accuracy-techniques.md`. Every gain is extrapolated from the literature, not measured on arbiter.

| ID | Idea | Status | Evidence | Next |
|---|---|---|---|---|
| T-01 | SAST hits as verifier candidates, with a CWE-specific lens | proposed (#1) | Tencent triage removed 94–98% of FPs; ZeroFalse F1 0.91–0.96 | targets python-03, which Haiku missed |
| T-02 | Cascade: cheap panel first, escalate split votes | proposed (#2) | see M-08 | |
| T-03 | k=3 cheap finders on risky units at standard effort | proposed (#3) | 5×Flash beat 1×Pro on SWR-Bench; more votes can hurt on hard items | |
| T-04 | Co-change neighbour map from `git log` | proposed (#4) | +10.85 pp in a Go review study; zero model calls | |
| T-05 | A0 claims and a riskiest-hunks spotlight passed to finders | proposed (#5), partly in `hier` | Meta ARCTIC intent F1 0.86; spotlight 2.4× better on 5× fewer tokens | `hier` passes claims |
| T-06 | Suppress findings similar to past dismissals | proposed (#6) | Greptile address rate 19% → 55%+ | see LR R4 |
| T-07 | Cross-model verifier lens | proposed (#7) | see M-09 | |
| T-08 | Property-based tests as finder and prover | proposed (#8) | 56% valid reports, 86% for top-ranked | |
| T-09 | Multi-agent debate | dropped | Majority voting explains most of its gains `[AT]` | — |
| T-10 | Intrinsic self-critique without external feedback | dropped | No successful case `[AT]`, `[DV-S19]` | — |
| T-11 | Few-shot bad-example prompts | dropped | Made Greptile's bot worse `[AI-§4 #11]` | — |
| T-12 | Place a verified (panel TRUE_POSITIVE) but unproven finding in the main section as should-fix when the proof could not run for environment reasons (dependency fetch failed), instead of in Suspected; blocking still needs a proof | proposed | Martian 20-PR loss trace (benchmarks §3.7): both such findings were High golden bugs that the top tools report; 2/2 true, so no precision cost | +2 of 70 Core |
| T-13 | Repair a finding with empty `evidence_lines` from its `file:line` instead of rejecting it | proposed | Same trace: 2 golden bugs (1 consensus) rejected for this formatting slip by Haiku | +≤2 of 70 |
| T-14 | Loosen the verifier panel to recover true bugs it drops | dropped | The panel dropped 62 findings on 20 PRs, 5 of them true (about 92% right). Wholesale loosening trades about 11 FPs per TP | — |
| T-15 | Semantic code retrieval ("context engine": Augment, Qodo) for finders | deferred | Leaders credit it for cross-system bugs. In the trace, 12 of 20 missed consensus bugs were never raised, several cross-file contract breaks. Try the `hier` contract pass and codegraph callers first (P4 A/B) | P4 |
| T-16 | Reasoning-heavy finder model that makes more tool calls (Augment chose GPT-5.2 over Sonnet for review). Candidate: `openai/gpt-6-luna` (Oct 2026, $0.10/$0.50 per M tokens; vendor-reported DeepSWE 66.6% at max effort, near Opus 5 at medium) | **open** | Cannot test: omp has no OpenAI provider (M-06). Test plan: Luna finders + Sonnet verifier on the same 20 Martian PRs and the 40 SWR PRs, against H+S. Briefs were tuned on Claude models; Augment reports prompts need per-model tuning. The S+S matrix (M-11) shows a stronger Anthropic finder alone does not close the gap | — |
| T-17 | Learn from PR history (Qodo recommendation agent) | proposed | Same as the learned-rules plan; see R-01..R-05 | §5 |
| T-18 | Anchor a finding by its quoted code snippet (OCR `existing_code`: match the diff hunks, then the whole file, then one LLM relocation) instead of rejecting findings with a bad line or empty evidence | proposed, merges with T-13 | OCR v1.14 `code_comment` line resolution `[OCR paper §3.3.3]`. The Martian trace lost 3 golden bugs to validation (2 empty evidence, 1 outside hunks ±3) | +≤3 of 70 |
| T-19 | Let finders read the base side (OCR #1915: `side: old` on read and search tools); today they see the base only as `-` lines in the diff | proposed | Removed or moved code and "what did callers expect before" questions need the old file; arbiter already keeps a base worktree for the sandbox | — |
| T-20 | OCR-style reflector: the same model sees only the diff and drops a finding only when the diff contradicts it; fails open | dropped as a replacement for the panel | OCR reports precision 25–38% on AACR-Bench with it (a different benchmark, not directly comparable). arbiter's repo-reading panel is about 92% right on its drops (T-14). The principle behind the reflector is already in V.md: filter only, never generate, and stay independent by seeing less | — |

## 5. Learned rules from past PRs and MRs

Design and evidence: `research/research-learned-rules.md`. Verdict: it works mostly through learned suppression and validated deterministic checks; rule text in prompts is the weakest part.

| ID | Phase | Idea | Status | Evidence |
|---|---|---|---|---|
| R-00 | R0 | Read repo rules from the base branch; strip invisible Unicode | proposed, priority | fixes A-15; rule files can hide instructions in invisible Unicode `[LR]` |
| R-01 | R1 | `.arbiter/rules.jsonl` schema; import the user's existing rule list | proposed | — |
| R-02 | R2 | `arbiter learn` from `gh`/`glab`: review comments followed by a fix commit, generalized by one cheap call; dedup; live only with 2 sources and a replay that fires on bad and not on good | proposed | Phoenix top-1 only 54% without validation `[LR]` |
| R-03 | R3 | Compile strong rules to semgrep; zero model calls | proposed | SpongeBugs 87% accepted; KNighter 92 bugs; QLCoder 53.4% vs 10% `[LR]` |
| R-04 | R4 | Dismissal-based suppression after 3 dismissals across at least 2 PRs; Wilson-bound retirement | proposed | Greptile, Bito thresholds `[LR]` |
| R-05 | R5 | Time-split eval: learn before a cutoff, test after | proposed | — |
| R-06 | — | Many rules as prompt text | dropped as the main mechanism; capped at 8 rules and 2k tokens per unit | 68% accuracy at 500 instructions; rules 49.0% vs raw examples 53.5% `[LR]` |
| R-07 | — | RL or preference tuning on accepted vs rejected comments | dropped | Conflicts with the model-agnostic design (see M-10) |

## 6. External tools and platforms

Evaluation: `research/research-code-quality-platforms.md`.

| ID | Idea | Status | Decision and evidence |
|---|---|---|---|
| X-01 | Codacy rule set or Critical tier | dropped | Wraps tools arbiter already runs; "Critical" is a relabel; the default Critical tier found 0 of 452 OWASP Python vulns; grade weights unpublished |
| X-02 | Code Climate / Qlty | dropped | BUSL licence excludes AI coding services |
| X-03 | DeepSource, Snyk Code | dropped | Cloud-only, closed, vendor-run precision claims |
| X-04 | SonarQube Cloud/Server taint analysis | dropped | Paid server or cloud only; analyzer licence bars competing products. Kept as a precision benchmark |
| X-05 | Semgrep Pro | deferred | Use only if a user already has it |
| X-06 | Secrets scanning (gitleaks or Trivy) | proposed (rank 1) | A real coverage gap; hits become verifier seeds plus E2 |
| X-07 | Lockfile vulnerability scanning (osv-scanner or Trivy) | proposed (rank 1) | A gap for Python, TS, and Rust without `deny.toml`; deterministic E1 on the deps axis |
| X-08 | Go semgrep pack; 3 rules gosec misses (jwt none alg, insecure gRPC client and server); TS MCP taint rules | proposed (rank 2) | Go has no semgrep pack in arbiter today |
| X-09 | Opengrep cross-file taint | deferred | After a precision A/B on arbiter's benchmark |
| X-10 | CodeQL default suite | proposed, opt-in | Only for repos under an OSI licence; its licence bars automated use on closed code |
| X-11 | Lint-tier hits treated as proof | dropped | Codacy/Sonar tiers fall short of Google's <10% effective-FP bar and Sonar's own >80% TP target |

## 7. Evaluation and process

| ID | Date | Idea or concern | Status | Decision and evidence |
|---|---|---|---|---|
| E-01 | 2026-11-21 | Seeded corpus, 28 cases | adopted, **open concern** | Prompts were tuned twice on the same cases; precision is optimistic. Fix: roadmap P0.3 held-out split |
| E-02 | 2026-11-21 | Martian golden set with one LLM judge | adopted, **open concern** | Martian uses 3 judges; samples are small |
| E-03 | 2026-11-22 | SWR-Bench, official judge prompts, 40-PR sample | adopted, **open concern** | SWE-bench repos are likely in training data; only 20 issue PRs exceed 150 lines, too few for P4 alone |
| E-04 | 2026-11-22 | A failed judge call scored as a false positive | dropped | Now reported as "unjudged" (found by self-review) |
| E-05 | 2026-11-23 | Go and Rust benchmark runs | deferred | User postponed them; the matrix runs Python and TS only |
| E-06 | 2026-11-23 | Two benchmark runners at once | dropped | A reboot followed by a restart left two runners sharing caches for about 75 min; their results were discarded. The matrix script now takes a `flock` |
| E-07 | 2026-11-23 | Benchmark runs survive a reboot | **open concern** | Logs persist in `eval/results/logs/`, but a reboot stops the run |
| E-08 | 2026-11-22 | Token accounting per call | proposed | Cost is reported as model calls only; roadmap P0.1 |
| E-09 | 2026-11-21 | Project renamed curve → arbiter in a new repository | adopted | User decision |
| E-10 | 2026-11-21 | devrem `reviewer` integration | deferred | Out of the original plan; roadmap I6 |
| E-11 | 2026-11-24 | Run-to-run variance of each setup | **open concern** | Every matrix cell ran once; differences of a few points may be noise. Fix: repeat runs (roadmap P0) |
| E-12 | 2026-11-24 | AACR-Bench (Alibaba, Apache-2.0): 200 PRs, 50 repos, 10 languages including Python, TS, Go and Rust; 1,505 expert-verified comments plus a 155-PR negative set; full repo snapshots; pluggable `--reviewer` pipeline | proposed | Larger than the Martian set, with a clean-PR negative set. Comments include maintainability, so score the Code Defect and Security subset to match arbiter's blocking scope. Published reference: OCR SEM-F1 17.9–25.1% across 6 models, Claude Code 10.9–14.1% |
