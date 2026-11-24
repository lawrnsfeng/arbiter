<!-- generated from decisions.jsonl by arbiter ledger render; edit the JSONL -->
# Decision ledger

This ledger records every technical idea and concern raised for arbiter, whatever happened to it: adopted, adopted behind a switch, proposed, deferred or dropped. Each row names where the idea came from, the evidence, and where the result lives. The reasoning behind the adopted design is in [methodology.md](methodology.md) §2–§5. Rejected approaches live in §8 with four fields: the tool or framework the idea came from, what it is, why that tool uses it, and why arbiter dropped it.

**Rule:** any new idea, concern, experiment or rejection gets a row in `decisions.jsonl` in the same change that raises it; `arbiter ledger render` regenerates this file and `arbiter ledger check` fails when it is stale. When an idea's status changes, edit its row and add the date; do not delete rows. [CHANGELOG.md](../CHANGELOG.md) says what shipped, and this file says what was decided.

Status values:
- `adopted`: in the code.
- `switch`: in the code, off by default until a test decides.
- `proposed`: researched, not built.
- `deferred`: wanted, postponed on purpose.
- `dropped`: rejected, with the reason.
- `open`: a known concern with no fix yet.

Source keys (`[DV-S4]`, `[DH-D10]`, `[AT-…]`, `[LR-…]`, `[CQ-…]`, `[LD1]`) resolve through [sources.md](sources.md). The research file for each prefix:

| Prefix | File |
|---|---|
| AT | `research/research-accuracy-techniques.md` |
| LR | `research/research-learned-rules.md` |
| CQ | `research/research-code-quality-platforms.md` |
| DH | `research/research-decompose-hierarchical.md` |
| LD | `research/research-leader-approaches.md` |

## 1. Architecture and pipeline

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| A-02 | 2026-11-21 | Stdlib-only package | adopted | No supply-chain surface in the reviewer; runs anywhere `uv` does | `pyproject.toml` |
| A-04 | 2026-11-21 | Proof agent restricted to `arbiter sandbox exec` | adopted, open concern | Proof exit codes are re-read from `RUN/exec`, which sandboxed code cannot write. The proof agent's host bash is limited only by its prompt; the fix is I2 (own tool loop) | methodology §6, roadmap I2 |
| A-05 | 2026-11-21 | Hard proof gate: a functional finding blocks only with a confirmed proof at an accepted rung | adopted | `[DV-S16]` repro tests doubled precision; LLM self-confidence is close to random `[AI-§4 #10]` | `findings.gate` |
| A-07 | 2026-11-21 | 3-lens disprove panel with a never-auto-dismiss CWE list | adopted | The strongest measured precision gain `[AI-§4 #2]`; every FP filter loses some TPs `[SEC-S48..S50]` | `findings.tally` |
| A-09 | 2026-11-21 | Merge findings at one location under the highest-priority axis | adopted, open concern | One f-string query became 3 findings. It hid the proven go-02 bug behind a disputed security claim; the fix is roadmap P1.1 (pick the representative by support) | `findings.merge`, roadmap P1.1 |
| A-10 | 2026-11-21 | Fail closed when more than 25% of agent calls fail | adopted | A rate-limited run reported PASS with zero working agents | `pipeline._withhold` |
| A-11 | 2026-11-21 | Proofs run one at a time | adopted | Proof agents edit `RUN/wt`; parallel runs corrupt fail/pass pairs | `pipeline.proofs` |
| A-12 | 2026-11-21 | bubblewrap sandbox: network off, `$HOME` hidden, env cleared | adopted, open concern | No CPU or memory limit yet (`[DV-§4]` rule 9); the fix is I7 | `sandbox.py`, roadmap I7 |
| A-15 | 2026-11-23 | Repo rule files read from the PR's head | open | A PR can rewrite its own review policy; Anthropic reads REVIEW.md from the base branch only `[LR]`. The fix is LR phase R0 | `plan._rules`, §5 R0 |
| A-16 | 2026-11-24 | omp advisor forced off on every arbiter call; one strictly capped Opus decision call per review (`--decide`) | adopted, opt-in, wave 2a | omp's advisor retries up to 3 times and falls back across models, so it cannot keep a one-Opus-call budget; arbiter loads `omp-overlay.yml` (advisor.enabled false) and makes the call itself: claim file per RUN, harness.call with no retry, no tools, omp --max-cost $1.00, Opus only, omp only. Wave 2a (benchmarks §3.9): 5 reviews, 5 calls, none retried; F2 0.200 vs 0.198 old, precision 0.200 vs 0.190; 7 dismissals, 2 of them matched a reference (one the only maintainability reference of ComfyUI 7952); 0 challenges, 0 missed concerns | `harness.argv`, `pipeline.decide`, `agents/DECIDE.md` · next: stop dismissals of maintainability findings (MA-01) before considering a default |

## 2. Models and cost

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| M-02 | 2026-11-22 | Haiku finders, Sonnet verifier, proof agent and judge | adopted, confirmed 2026-11-24 | User decision; cheap independent finders, with the strong model where precision is decided `[AI-§4 #9]`. Confirmed by the 2026-11-23 matrix (benchmarks §3.7): see M-11 (§8) | `harness.FALLBACK_MODELS` |
| M-03 | 2026-11-23 | Resolve models from omp roles (`arbiter-finder` or `smol`; `arbiter-verify`) | adopted | User asked for omp roles mapped to Haiku and Sonnet at most; `default` and `slow` are Opus here and never used | `harness.settings` |
| M-04 | 2026-11-23 | Cost ceiling `ARBITER_BLOCKED_MODELS` (default `opus,fable`) applied to the resolved model | adopted | User set Sonnet as the ceiling | `harness._resolve` |
| M-05 | 2026-11-23 | Preflight each model: read a file, answer JSON | adopted | An unconfigured model crashed every omp call after about 80 s | `harness.preflight` |
| M-06 | 2026-11-23 | DeepSeek and GPT models | open | Untested: only the Anthropic provider is configured. The preflight is the safety net. GPT-6 Luna: the user will try it in their organization's harness (no OpenAI key here). Run `arbiter eval martian run --repo sentry --model openai/gpt-6-luna` in an omp with an OpenAI provider, or `--harness claude` behind a GPT gateway; any other harness needs I1. | README Models |
| M-08 | 2026-11-23 | Cheap verifier panel first, escalate only split votes to the strong model | proposed | FrugalGPT: up to 98% cheaper at equal accuracy; code cascades save 26% on average `[AT]`. Ranked #2 | AT §ranking |
| M-09 | 2026-11-23 | One verifier lens run by a different model family | proposed | 56.7% vs 42.7% caught; one pairing direction got worse `[AT]`. Ranked #7 | AT §ranking |
| M-12 | 2026-11-25 | Jev (TypeSafe System One) as the eval matching judge with a confidence cascade to Sonnet | deferred, no TYPESAFE_API_KEY on this machine | reading-type judgments within 2-3 pts of GPT-6 at 0.36% of its fee; 13-28 pts behind on code/math/logic (arXiv 2609.26550; Scale Labs To Jev or Not to Jev); unfit as code verifier |  · next: set TYPESAFE_API_KEY, then build eval/judge.py jev cascade |

## 3. Decomposition (review units)

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| U-01 | 2026-11-21 | OCR-style units: at most 150 changed lines, hunk chunks, merge up to 10 files | adopted, default | F1 0.657 under 10 lines vs 0.043 over 150 `[DV-S4]`, later found confounded `[DH]` | `units.py` |
| U-02 | 2026-11-23 | Hierarchical split: package → module → definition → method → statement (Python, `ast`) | switch, `--decompose hier` | Smaller inputs help (CRBugBench OR 0.59; *Lost in the End* +37% recall), but syntax splits have not beaten line splits, and per-function chunking was worst `[DH-D5, D18]`. Adopt only if the P4 A/B passes | `decompose.py`, roadmap P4 |
| U-05 | 2026-11-23 | Changed-symbol manifest and signature map per unit, built with zero model calls | switch | Cross-unit context loss caused 861 FPs in a project-scale study `[DH]` | `decompose.py` |
| U-06 | 2026-11-23 | Accept findings in any changed hunk of the PR; cluster by changed symbol | switch | The own-unit rule discards cross-unit findings `[DH-§4.0]` | `findings.merge` |
| U-07 | 2026-11-23 | One contract pass per PR for signature changes | switch | Covers callers outside the diff `[DH-§4.4]` | `pipeline` CONTRACT job |

## 4. Accuracy techniques (beyond decomposition)

Ranked in `research/research-accuracy-techniques.md`. Every gain is extrapolated from the literature, not measured on arbiter.

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| T-01 | 2026-11-24 | SAST hits as verifier candidates, with a CWE-specific lens | switch, `ARBITER_SAST_CANDIDATES=1`, wave 2a | Tencent triage removed 94–98% of FPs; ZeroFalse F1 0.91–0.96. Wave 2a (benchmarks §3.9): no analyzer hit fell on an added line in 5 AACR Python PRs, so it never fired; the bundled new arm lost 0.002 rescored F2, so off by default per the adoption rule | `pipeline._sast_candidates` · next: measure on items with analyzer hits in the diff (python-03, Martian security PRs) |
| T-02 | — | Cascade: cheap panel first, escalate split votes | proposed, #2 | see M-08 |  |
| T-03 | — | k=3 cheap finders on risky units at standard effort | proposed, deprioritized 2026-11-25 | 5×Flash beat 1×Pro on SWR-Bench; more votes can hurt on hard items; 2026-11-25 union re-judge on 6 AACR PRs: two passes merged by location P 0.275 R 0.269 F1 0.272 F2 0.270 vs one pass P 0.289 R 0.250 F1 0.268 F2 0.257 (+1 of 52 refs, inside judge noise) |  |
| T-04 | 2026-11-24 | Co-change neighbour map from `git log` | switch, `ARBITER_COCHANGE=1`, wave 2a | +10.85 pp in a Go review study; zero model calls. Wave 2a (benchmarks §3.9): only langflow 6044 got a neighbour (1 file; AACR snapshots have short histories) and no main finding was in a co-change file; the bundled new arm lost 0.002 rescored F2, so off by default per the adoption rule | `arbiter/cochange.py`, `plan.plan` · next: measure on repos with full history (Martian, own repos) |
| T-05 | — | A0 claims and a riskiest-hunks spotlight passed to finders | proposed, #5, partly in `hier` | Meta ARCTIC intent F1 0.86; spotlight 2.4× better on 5× fewer tokens |  · next: `hier` passes claims |
| T-06 | — | Suppress findings similar to past dismissals | proposed, #6 | Greptile address rate 19% → 55%+ |  · next: see LR R4 |
| T-07 | — | Cross-model verifier lens | proposed, #7 | see M-09 |  |
| T-08 | — | Property-based tests as finder and prover | proposed, #8 | 56% valid reports, 86% for top-ranked |  |
| T-12 | — | Place a verified (panel TRUE_POSITIVE) but unproven finding in the main section as should-fix when the proof could not run for environment reasons (dependency fetch failed), instead of in Suspected; blocking still needs a proof | adopted, wave 1, 2026-11-24 | Martian 20-PR loss trace (benchmarks §3.7): both such findings were High golden bugs that the top tools report; 2/2 true, so no precision cost. Spot check (benchmarks §3.8): not exercised; fetch failed on sentry and cal.com, but no verified finding there was left unproven |  · next: `findings.gate`, `pipeline._env_gap` |
| T-13 | — | Repair a finding with empty `evidence_lines` from its `file:line` instead of rejecting it | adopted, wave 1, 2026-11-24 | Same trace: 2 golden bugs (1 consensus) rejected for this formatting slip by Haiku. Spot check: 1 finding repaired in each new AACR run; neither matched a reference |  · next: `findings.merge`, `findings._repair` |
| T-15 | — | Semantic code retrieval ("context engine": Augment, Qodo) for finders | deferred | Leaders credit it for cross-system bugs. In the trace, 12 of 20 missed consensus bugs were never raised, several cross-file contract breaks. Try the `hier` contract pass and codegraph callers first (P4 A/B) |  · next: P4 |
| T-16 | — | Reasoning-heavy finder model that makes more tool calls (Augment chose GPT-5.2 over Sonnet for review). Candidate: `openai/gpt-6-luna` (Oct 2026, $0.10/$0.50 per M tokens; vendor-reported DeepSWE 66.6% at max effort, near Opus 5 at medium) | open | Cannot test: omp has no OpenAI provider (M-06). Test plan: Luna finders + Sonnet verifier on the same 20 Martian PRs and the 40 SWR PRs, against H+S. Briefs were tuned on Claude models; Augment reports prompts need per-model tuning. The S+S matrix (M-11) shows a stronger Anthropic finder alone does not close the gap. GPT-6 Luna: the user will try it in their organization's harness (no OpenAI key here). Run `arbiter eval martian run --repo sentry --model openai/gpt-6-luna` in an omp with an OpenAI provider, or `--harness claude` behind a GPT gateway; any other harness needs I1. |  |
| T-17 | — | Learn from PR history (Qodo recommendation agent) | proposed | Same as the learned-rules plan; see R-01..R-05 |  · next: §5 |
| T-18 | — | Anchor a finding by its quoted code snippet (OCR `existing_code`: match the diff hunks, then the whole file, then one LLM relocation) instead of rejecting findings with a bad line or empty evidence | adopted, wave 1, 2026-11-24, merged with T-13; hunk match only | OCR v1.14 `code_comment` line resolution `[OCR paper §3.3.3]`. The Martian trace lost 3 golden bugs to validation (2 empty evidence, 1 outside hunks ±3). Spot check: no relocation fired on the 3 items |  · next: `findings.merge`, `findings._relocate` |
| T-19 | 2026-11-24 | Let finders read the base side (OCR #1915: `side: old` on read and search tools); today they see the base only as `-` lines in the diff | switch, `ARBITER_BASE_READS=1`, wave 2a | Removed or moved code and "what did callers expect before" questions need the old file. Wave 2a (benchmarks §3.9): the base checkout path reached every finder and verifier prompt and omp reads absolute paths outside the cwd, but no new reference was covered; the bundled new arm lost 0.002 rescored F2, so off by default per the adoption rule | `pipeline._base_input` · next: measure alone on removal and rename PRs |

## 4b. From the leader study

Source: `research/research-leader-approaches.md` (Augment, Qodo 2.0, cubic, alibaba OpenCodeReview and AACR-Bench).

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| T-21 | — | Path-scoped rule areas: each rule carries `globs`, `severity` and `id` | proposed | Augment `areas:` YAML and directory-scoped guidelines [LD1][LD3]; Qodo pattern clustering by path [LD11] |  · next: Fold into R-01 schema (wave 3) |
| T-22 | — | A "Do not apply when" exception on every learned rule | proposed | cubic learnings [LD16] |  · next: R-01 schema (wave 3) |
| T-23 | — | Learning curation: create, improve, remove, keep; a raw evidence log plus a curated file; explicit feedback outweighs reactions; weekly merge and archive of rules that stopped helping | proposed | cubic [LD16]; Augment capture → curate → load [LD6] |  · next: R-02/R-04 (wave 3) |
| T-24 | — | Mine only comments that led to code changes, weighted by the reviewer's ownership (git blame) of the code | proposed | Qodo Rule Miner [LD11] |  · next: R-02 (wave 3) |
| T-25 | — | Relevance from history: tag each finding High, Medium or Low by how similar past findings were handled, with links | proposed | Qodo Relevance [LD11] |  · next: R-04 (wave 3) |
| T-26 | — | Deterministic risk-based effort routing (`--effort auto`): blast radius (callers, shared paths), behavioral complexity (MA-03 facts), potential damage (security, data, billing paths); when unsure go deeper | proposed | Qodo Review effort Auto and Merge Risk [LD12]; Augment Risk Analyzer [LD7] |  · next: Wave 2 |
| T-27 | 2026-11-24 | Reasoning before verdict: finders write `trigger` and `evidence_lines` before `claim` and `severity` | adopted, wave 2a | cubic explicit reasoning logs, part of a 51% FP cut [LD14]. Wave 2a (benchmarks §3.9): bundled with T-19, T-04, T-01, the new arm scored F2 0.196 vs 0.198 old on 5 AACR PRs (inside noise); brief text only, no code path to switch | `schema.md` Candidate order, preamble rule 5 |
| T-28 | — | Per-agent tool-call observability | proposed | Augment [LD1] |  · next: With P0.1 token accounting |
| T-29 | — | Comment-category distribution as an eval metric | adopted, wave 1 | Augment online metrics [LD1] |  · next: Eval summaries report evolvability findings and maintainability recall |
| T-30 | — | Agent-ready remediation prompt per finding | proposed | Qodo finding anatomy [LD8] |  · next: Wave 3 |
| T-31 | — | Check linked tickets and specs for requirement gaps | adopted, existing | Qodo requirement gaps [LD10]; PR-Agent TicketCompliance [LD13] |  · next: SPEC agent |
| T-32 | — | Treat PR title, description, commits and tickets as untrusted | adopted, existing | PR-Agent prompt [LD13] |  · next: A0, SPEC and hier inputs carry "untrusted" labels |
| T-33 | — | Seeded v2 built by injecting bugs *and* best-practice violations into real merged PRs, with repo rules written to AGENTS.md | proposed | Qodo benchmark method [LD9] |  · next: Roadmap D1; maintainability cases first |
| T-34 | — | Runtime verifier that also lists what it could not observe | adopted, existing | Augment Verifier [LD7] |  · next: Proof agent; Suspected and T-12 placement reasons |
| T-35 | — | "Only post what could change a merge decision" | adopted, in part | Augment [LD3] |  · next: Nit cap 10 per run; maintainability findings still post as should-fix (MA-01) |
| T-36 | — | Bounded tool outputs (read 500 lines, search 100 matches) | proposed | OCR [LD17] |  · next: With I2 (own tool loop) |

## 4c. Maintainability

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| MA-01 | — | Maintainability is a first-class axis: it reduces future pain (user decision, 2026-11-24) | adopted | Evolvability is about 75% of human review fixes `[AX-S1] [AX-S2]`; arbiter found 1/13 SWR evolvability changes [LD23]; Martian "style" goldens were not scored |  |
| MA-02 | — | Score maintainability recall separately in every benchmark: SWR `E.*`, Martian `style`, AACR "Maintainability and Readability", seeded evolvability axes | adopted, wave 1 | Same. Spot check: AACR maintainability recall 2/9 old and 2/9 new over 6 Python samples (ComfyUI 9560, 7952, 8446, ragflow 7151, langflow 6044, 6652); 1/3 with `hier` on 9560 alone; the two Martian PRs have no `style` goldens (benchmarks §3.8) |  · next: Eval summaries |
| MA-03 | — | Deterministic maintainability facts (Python `ast`, base vs head): complexity, nesting, length, params, file crossing 1,000 lines | adopted, wave 1 | radon ranks; pylint defaults; pstack "1k-line file" blocker. Spot check: ComfyUI 9560 got 2 facts, `server.py` crossing 1,000 lines (985 → 1005, block-eligible) and `cache_control` complexity 4 → 11; sentry-greptile 3 got 2 length facts on functions already over 120 lines (not block-eligible); cal.com is TypeScript (no facts, MA-08). No finding cited the block-eligible file fact |  · next: `arbiter/maintain.py` |
| MA-04 | — | A6d readability agent: names, dead code, complexity, nesting, magic numbers, flag arguments | adopted, wave 1, open concern | No agent owned these axis-13 items (A6a walks the idiom table only). Spot check: over 6 AACR samples A6d reported 9 findings, most on measured facts, none matching any of the 9 maintainability references. The references ask for consistency, dead code, merged branches and clearer conditions; the two that were covered were found by A6b and ruff. Adds 1–6 agent calls per run. Wave 2 decides whether A6d pays for itself or its facts should go to A6a/A6b |  · next: `agents/A6d.md` |
| MA-05 | — | Blocking policy: a maintainability finding may block only with a block-eligible measured fact or a repo rule heading marked `[block]`; otherwise should-fix (user decision, 2026-11-24) | adopted, wave 1 | Same proof-gated spirit as functional findings. Spot check: it blocked ragflow 7151, where `InfinityConnection.update` complexity rose from 11 to 22 (block line 20); no AACR reference names it, and the old arm passed. On ComfyUI 8446 and langflow 6044, A6d reported new functions with complexity 26 and 33 but rated them should-fix, so the rule allowed a block and the agent did not claim one |  · next: `findings.gate` |
| MA-07 | — | Learned repo conventions are mostly maintainability: prioritize them in the learned-rules track | proposed | Rule Miner and cubic learnings are convention-heavy [LD11][LD16] |  · next: R-01..R-05 |
| MA-08 | — | Maintainability facts for TypeScript, Go and Rust | deferred | No stdlib parser; use the eslint `complexity`, gocyclo and clippy `cognitive_complexity` gates when installed |  · next: Wave 2 |

## 5. Learned rules from past PRs and MRs

Design and evidence: `research/research-learned-rules.md`. Verdict: it works mostly through learned suppression and validated deterministic checks; rule text in prompts is the weakest part.

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| R-00 | — | R0: Read repo rules from the base branch; strip invisible Unicode | proposed, priority | fixes A-15; rule files can hide instructions in invisible Unicode `[LR]` |  |
| R-01 | — | R1: `.arbiter/rules.jsonl` schema; import the user's existing rule list | proposed |  |  |
| R-02 | — | R2: `arbiter learn` from `gh`/`glab`: review comments followed by a fix commit, generalized by one cheap call; dedup; live only with 2 sources and a replay that fires on bad and not on good | proposed | Phoenix top-1 only 54% without validation `[LR]` |  |
| R-03 | — | R3: Compile strong rules to semgrep; zero model calls | proposed | SpongeBugs 87% accepted; KNighter 92 bugs; QLCoder 53.4% vs 10% `[LR]` |  |
| R-04 | — | R4: Dismissal-based suppression after 3 dismissals across at least 2 PRs; Wilson-bound retirement | proposed | Greptile, Bito thresholds `[LR]` |  |
| R-05 | — | R5: Time-split eval: learn before a cutoff, test after | proposed |  |  |

## 6. External tools and platforms

Evaluation: `research/research-code-quality-platforms.md`.

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| X-05 | — | Semgrep Pro | deferred | Use only if a user already has it |  |
| X-06 | — | Secrets scanning (gitleaks or Trivy) | proposed, rank 1 | A real coverage gap; hits become verifier seeds plus E2 |  |
| X-07 | — | Lockfile vulnerability scanning (osv-scanner or Trivy) | proposed, rank 1 | A gap for Python, TS, and Rust without `deny.toml`; deterministic E1 on the deps axis |  |
| X-08 | — | Go semgrep pack; 3 rules gosec misses (jwt none alg, insecure gRPC client and server); TS MCP taint rules | proposed, rank 2 | Go has no semgrep pack in arbiter today |  |
| X-09 | — | Opengrep cross-file taint | deferred | After a precision A/B on arbiter's benchmark |  |
| X-10 | — | CodeQL default suite | proposed, opt-in | Only for repos under an OSI licence; its licence bars automated use on closed code |  |

## 7. Evaluation and process

| ID | Date | Idea or concern | Status | Evidence | Where / next |
|---|---|---|---|---|---|
| E-01 | 2026-11-21 | Seeded corpus, 28 cases | adopted, open concern | Prompts were tuned twice on the same cases; precision is optimistic. Fix: roadmap P0.3 held-out split |  |
| E-02 | 2026-11-21 | Martian golden set with one LLM judge | adopted, open concern | Martian uses 3 judges; samples are small |  |
| E-03 | 2026-11-22 | SWR-Bench, official judge prompts, 40-PR sample | adopted, open concern | SWE-bench repos are likely in training data; only 20 issue PRs exceed 150 lines, too few for P4 alone |  |
| E-05 | 2026-11-23 | Go and Rust benchmark runs | deferred | User postponed them; the matrix runs Python and TS only |  |
| E-07 | 2026-11-23 | Benchmark runs survive a reboot | open | Logs persist in `eval/results/logs/`, but a reboot stops the run |  |
| E-08 | 2026-11-22 | Token accounting per call | proposed | Cost is reported as model calls only; roadmap P0.1 |  |
| E-09 | 2026-11-21 | Project renamed curve → arbiter in a new repository | adopted | User decision |  |
| E-10 | 2026-11-21 | devrem `reviewer` integration | deferred | Out of the original plan; roadmap I6 |  |
| E-11 | 2026-11-24 | Run-to-run variance of each setup | open | Every matrix cell ran once; differences of a few points may be noise. Fix: repeat runs (roadmap P0) |  |
| E-12 | 2026-11-24 | AACR-Bench (Alibaba, Apache-2.0): 200 PRs, 50 repos, 10 languages including Python, TS, Go and Rust; 1,505 expert-verified comments plus a 155-PR negative set; full repo snapshots; pluggable `--reviewer` pipeline | adopted, wave 1 | Larger than the Martian set, with a clean-PR negative set. Score every category and report maintainability recall separately (MA-02). The adapter is `arbiter eval aacr` (wave 1). Its PR target commits are not on GitHub, so repos come from AACR's pinned Hugging Face snapshots (`Alibaba-Aone/aacr-bench-repos`), as AACR's own `repo_utils.py` does. Published reference: OCR SEM-F1 17.9–25.1% across 6 models, Claude Code 10.9–14.1% |  |
| E-13 | 2026-11-24 | A/B against another checkout (`--review-from`) and per-PR filters (`--pr`) | adopted, wave 1 | Same-day old-vs-new runs avoid regression to the mean when items are picked as best or worst |  |
| E-14 | 2026-11-24 | `arbiter eval aacr rescore`: judge several finished runs in one pass with one judge, plus the union of the first two | adopted, wave 2a | Runs judged on different days drifted; wave 2a scored old, new and new+decide in one pass (benchmarks §3.9) and also judges decide dismissals | `eval/aacr.rescore` |
| E-15 | 2026-11-24 | Requirement-first report with action tiers (must fix, should fix, verify, optional, pre-existing), an axes table, folded evidence, sandbox fix diffs and suggestion patches; `report.json` tier and sarif_level | adopted, wave 2a | User request: condensed, starts from the requirements, every axis shown, a next action. Requirements are A0 claims (R1…) and [block] repo rules (B1…); finders set `addresses` and `patches` | `report.py`, `pipeline.intent` |

## 8. Rejected approaches

Every dropped idea, with where it came from and why that source uses it. Rows keep their original IDs.

| ID | Date | Source (tool, framework or paper) | What it is | Why the source uses it | Why arbiter dropped it |
|---|---|---|---|---|---|
| A-01 | 2026-11-21 | cubic planner agent [LD14]; Claude Code `/code-review` orchestrator | An LLM decides which checks and agents run on a PR | Flexible triage per PR without hand-written rules | Cheap models cannot be trusted to plan, and vote arithmetic must be exact. Deterministic triggers choose the agents (methodology §3, §4) |
| A-03 | 2026-11-21 | Claude Code and Codex review; cubic "basic terminal" [LD14] | Finders and verifier get a shell | Free exploration: grep, git log, running tests | A prompt-injected agent with a host shell could run anything; unbounded tools also add non-determinism and token snowball [LD17]. Finders get read, grep and glob only |
| A-06 | 2026-11-21 | PR-Agent `min_finding_confidence` 0–10 [LD13]; cubic `confidence` field [LD14]; early Greptile | Model self-rated confidence used as a filter | A cheap threshold to cut noise | Self-rating is "nearly random" `[AI-§4 #10]`, and verbalized confidence is overconfident `[AT]`. The verifier panel and proof gate filter instead |
| A-08 | 2026-11-21 | Linter-augmented prompting `[DV-S5]` | Paste SAST/lint output into finder prompts | Give the model hints about suspicious lines | Cut precision to 2.8% `[DV-S5]`. SAST is attached afterwards as E2 support |
| A-13 | 2026-11-22 | arbiter (own candidate) | Compare HEAD and base gate results even when the dependency fetch failed | More gate signal on real repos | The difference may come from the environment, not the change, so it is skipped and noted |
| A-14 | 2026-11-22 | arbiter (own fallback) | Run eslint on the host when the sandbox is down | Keep TS lint coverage without bubblewrap | `eslint.config.js` is repo code; running it on the host executes untrusted code (found by self-review) |
| M-01 | 2026-11-21 | omp / Claude Code default model | Use whatever model the harness defaults to | Zero configuration | It fell through to Opus and drained the token budget (CHANGELOG 0.2.0) |
| M-07 | 2026-11-23 | Claude Code / omp plugin marketplaces | Ship arbiter as a plugin with a marketplace manifest | One-click install and updates | User chose `make install`: an `arbiter` command on PATH plus skills linked into `~/.omp/agent/skills` |
| M-10 | 2026-11-23 | LLaMA-Reviewer, MelcotCR (in [LD17] related work) | Fine-tune or distill a model on review data | Encode review knowledge in weights; a small model can match a large one | Conflicts with the model-agnostic, stdlib-only design; weights cannot read the target repo [LD17] |
| M-11 | 2026-11-24 | Augment: use the strongest reasoning model as reviewer [LD2] | Sonnet in every role, including finders | Deeper reasoning and more tool calls find more bugs | Matrix: +6–12 points of recall on seeded and Martian but lower precision everywhere; SWR-Bench P 0.38 vs 0.67 with FP 18 vs 6 [LD24]. Higher cost for no consistent gain |
| U-03 | 2026-11-23 | Function-level chunkers (cAST baselines) `[DH]` | Review one function per unit | A function is a natural semantic unit | Worst chunking strategy, by 3.6–5.6 points `[DH]`. OCR also warns that per-function review "fragments a coherent change" [LD17] |
| U-04 | 2026-11-23 | RAG reviewers: LAURA, RAG-Reviewer, AUGER [LD17 §2.1] | Paste caller and callee bodies into each unit | Give the model context up front | Pasted bodies hurt; on-demand fetching scored 8–9 points higher (JitVul) `[DH-D10]` |
| U-08 | 2026-11-23 | Context-window packers; OCR's 80%-of-window file filter [LD17] | Size review units in tokens | Fit the model's window exactly | Every review-sizing result in the evidence is in changed lines `[DH-§4.1]`; a 24k-character guard trims only the context map |
| T-09 | 2026-11-23 | spencermarx/open-code-review personas plus a tech lead `[PM]` | Multi-agent debate before a verdict | Diverse viewpoints argue out weak claims | Majority voting explains most of debate's gains `[AT]`; it is more calls for the same effect |
| T-10 | 2026-11-23 | Reflexion, Self-Refine | The same model critiques its own findings with the same context | A cheap quality pass | No successful case without external feedback `[AT]`, `[DV-S19]`; it inherits the same bias [LD17] |
| T-11 | 2026-11-23 | Greptile experiment `[AI-§4 #11]` | Few-shot examples of bad comments in the prompt | Teach the model what not to flag | Made Greptile's bot worse `[AI-§4 #11]` |
| T-14 | 2026-11-24 | arbiter (own candidate from the recall trace) | Loosen the verifier panel to recover dropped true bugs | 5 of 62 dropped findings were true golden bugs | The panel is about 92% right on drops; loosening trades about 11 FPs per TP [LD22] |
| T-20 | 2026-11-24 | alibaba OpenCodeReview reflector [LD17] | The same model sees only the diff and drops a finding only when the diff contradicts it; fails open | Removes hallucinations cheaply while keeping recall; independence through a smaller information boundary | OCR's precision with it is 25–38%; arbiter's repo-reading panel is about 92% right on drops. Its principle is already in V.md |
| R-06 | 2026-11-23 | CodeRabbit and Copilot custom instructions; Augment guidelines [LD1] | Many repo rules as prompt text | Encode tribal knowledge directly | 68% accuracy at 500 instructions; rules 49.0% vs raw examples 53.5% `[LR]`. Kept only as a cap: 8 rules and 2k tokens per unit |
| R-07 | 2026-11-23 | Learning-from-feedback systems `[LR]` | RL or preference tuning on accepted vs rejected comments | The model itself learns team taste | Conflicts with the model-agnostic design (M-10); suppression and validated rules get the effect without weights |
| X-01 | 2026-11-23 | Codacy `[CQ]` | Codacy rule set or its "Critical" tier | One dashboard over many linters with grades | Wraps tools arbiter already runs; "Critical" is a relabel; the default Critical tier found 0 of 452 OWASP Python vulns; grade weights are unpublished |
| X-02 | 2026-11-23 | Code Climate / Qlty `[CQ]` | Qlty CLI and maintainability grades | Maintainability scoring across languages | BUSL licence excludes AI coding services |
| X-03 | 2026-11-23 | DeepSource, Snyk Code `[CQ]` | Proprietary analyzers with AI autofix | Hosted analysis with fixes | Cloud-only, closed, and vendor-run precision claims |
| X-04 | 2026-11-23 | SonarQube Cloud/Server `[CQ]` | Sonar taint analysis | Cross-file injection detection | Paid server or cloud only; the analyzer licence bars competing products. Kept as a precision benchmark |
| X-11 | 2026-11-23 | Codacy and Sonar severity tiers `[CQ]` | Treat lint-tier hits as proof | Reuse existing tool severities | The tiers miss Google's <10% effective-FP bar and Sonar's own >80% TP target |
| E-04 | 2026-11-22 | arbiter eval (own bug) | Count a failed judge call as a false positive | Simple scoring | A judge outage is not a reviewer error; it is now "unjudged" (found by self-review) |
| E-06 | 2026-11-23 | arbiter eval operations (incident) | Two benchmark runners at once | Restart after a reboot without checking | They corrupted shared cache checkouts for about 75 min and the results were discarded; the matrix script now takes a `flock` |
| X-12 | 2026-11-24 | Augment Risk Analyzer [LD5][LD7]; Qodo auto-approval workflows | Auto-approve low-risk PRs (docs, config, trivial) | Removes low-value queue work; about 10% of PRs auto-approved at first | arbiter gives an evidence-gated verdict and never approves or merges. The routing idea is kept as effort routing (T-26) |
| X-13 | 2026-11-24 | Augment Pair Reviewer [LD5][LD7] | An interactive reviewer that walks a human through design decisions | Humans keep judgment and knowledge transfer | arbiter must run with no human in the loop (user requirement) |
| X-14 | 2026-11-24 | Augment PR Author / PR Fixer [LD5][LD6] | Agents that write the PR and fix review findings | Close the author-side loop | Out of scope: arbiter reviews; its `fix` text and proof-agent minimal fixes stay advisory |
| X-15 | 2026-11-24 | Qodo UX-deviation (Figma) and cross-repository conflict checks [LD10] | Compare the PR with linked designs and with dependent repos | Organization-level product and service context | arbiter reviews one repo checkout offline with no design or org-graph inputs. Revisit if a user supplies those inputs |
| X-16 | 2026-11-24 | Qodo PR-Agent `require_estimate_contribution_time_cost`, `require_can_be_split_review` [LD13] | Effort estimates and split suggestions in the review | Help reviewers plan | Not a defect or maintainability finding; no evidence it changes merge decisions |
| X-17 | 2026-11-24 | Augment "Precise" style [LD4]; Qodo "Precise" config [LD9] | Ship a second, lower-recall style | Teams wanting fewer comments | arbiter's precision comes from the panel and proof gate, not from suppressing recall; effort levels already trade cost for depth |
| MA-06 | 2026-11-24 | Qodo PR-Agent reviewer prompt [LD13] | "Do not report missing docstrings, type hints, comments, unused imports" | Cut noise to raise acceptance | Conflicts with the maintainability priority (MA-01): A6c reports missing docs on public API with repo precedent, and A6d reports dead code. Linter-owned items stay excluded through `tools.md` |
