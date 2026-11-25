# arbiter

Autonomous, evidence-gated code review for Python, Go, Rust and TypeScript. A deterministic Python pipeline
(`arbiter run`) splits `base...HEAD` into small units and runs one-job LLM agents on each: correctness, edge cases,
errors, security, concurrency, contracts, supply chain, performance, ops, a11y, idiom, design and docs. A disprove
panel votes on every candidate. Functional findings must be proven in a bubblewrap sandbox (repro test, snippet,
race detector, ...) before they can block. It never asks questions and ends with a verdict and an exit code.

**Current scores:** see [Accuracy](#accuracy) below. Full results are in [docs/benchmarks.md](docs/benchmarks.md), and the score files in [eval/scores/](eval/scores/).

## Material

Documentation:
- [docs/decisions.md](docs/decisions.md): every idea and concern raised, adopted, behind a switch, proposed, deferred or dropped, with the evidence
- [docs/methodology.md](docs/methodology.md): design, the evidence behind each decision, decision log, deviations from the plan, limitations
- [docs/sources.md](docs/sources.md): papers, benchmarks and documents used, and what each changed
- [docs/benchmarks.md](docs/benchmarks.md): datasets, ground truth, scoring, full results, threats to validity
- [docs/roadmap.md](docs/roadmap.md): Python-first improvement plan, next datasets, path to an independent agent
- [CHANGELOG.md](CHANGELOG.md): every release, with the approach tried and the evidence behind it

Research (byte-identical copies from the 2026-11-21 research session; each file has its own source table with URLs):
- [research/research-axes.md](research/research-axes.md): review-axis taxonomy, agent grouping, priority
- [research/research-decompose-verify.md](research/research-decompose-verify.md): unit sizing, per-language command cookbook, evidence ladder, sandbox rules
- [research/research-security.md](research/research-security.md): security review method, per-language checklists, supply chain, LLM vulnerability-detection accuracy
- [research/research-ai-review-systems.md](research/research-ai-review-systems.md): how current AI review systems work, published benchmarks, precision techniques
- [research/prior-mint-review-research.md](research/prior-mint-review-research.md): OCR, mattpocock, Google eng-practices, pstack code judo
- [research/review-python.md](research/review-python.md), [research/review-go.md](research/review-go.md), [research/review-rust.md](research/review-rust.md), [research/review-typescript.md](research/review-typescript.md): per-language canon, tool layer, idioms, patterns, smells, severity

Later research:
- [research/research-decompose-hierarchical.md](research/research-decompose-hierarchical.md) (2026-11-23): hierarchical, syntax-aware review units, shared context, cross-unit merge, and the A/B plan behind `--decompose`
- [research/research-accuracy-techniques.md](research/research-accuracy-techniques.md) (2026-11-23): other accuracy techniques (voting, cascades, SAST triage, co-change context…), ranked for cheap models
- [research/research-learned-rules.md](research/research-learned-rules.md) (2026-11-23): learning review rules from past PRs/MRs, suppression, rule mining, risks, phased plan
- [research/research-code-quality-platforms.md](research/research-code-quality-platforms.md) (2026-11-23): Codacy, SonarQube, Qlty, DeepSource, Semgrep Pro, Snyk, CodeQL: what to leverage

Skills and agent prompts:
- [skills/arbiter-review/SKILL.md](skills/arbiter-review/SKILL.md): the core launcher
- [skills/arbiter-review/references/](skills/arbiter-review/references/): the shared material, listed in the table below
- Language skills, each with `references/` (canon, tools, idioms, design, severity, security, cookbook): [python-review](skills/python-review/), [go-review](skills/go-review/), [rust-review](skills/rust-review/), [ts-review](skills/ts-review/)

| File | Contents |
|---|---|
| [agent-preamble.md](skills/arbiter-review/references/agent-preamble.md) | rules shared by every agent |
| [schema.md](skills/arbiter-review/references/schema.md) | the JSON output schemas |
| [axes.md](skills/arbiter-review/references/axes.md) | the review axes |
| [evidence.md](skills/arbiter-review/references/evidence.md) | the evidence ladder |
| [security-method.md](skills/arbiter-review/references/security-method.md) | the security review method |
| [exclusions.md](skills/arbiter-review/references/exclusions.md) | known false-positive patterns to exclude |
| [threat-model-template.md](skills/arbiter-review/references/threat-model-template.md) | the threat-model template |
| [agents/](skills/arbiter-review/references/agents/) | the 18 agent briefs |

Evaluation data:
- [eval/seeded/](eval/seeded/): 28 seeded cases. Each has `base/`, `change.patch` and the ground truth in `expected.json`.
- [eval/martian/golden/](eval/martian/golden/): the Martian golden comments for sentry, grafana and cal.com. [SOURCE.json](eval/martian/golden/SOURCE.json) pins the upstream commit and records the MIT licence.
- [eval/scores/](eval/scores/): the score file of every reported run.

## Install

```bash
make install          # `arbiter` on PATH (uv tool, editable) + skills linked into ~/.omp/agent/skills
make install-claude   # optional: also link the skills into ~/.claude/skills (Claude Code)
make check            # ruff, mypy and the unit tests (no network, no LLM)
make uninstall        # removes the tool and only the symlinks that point into this checkout
```

Skills: `arbiter-review` (core launcher), `python-review`, `go-review`, `rust-review`, `ts-review`.

## Run

```bash
arbiter run [--repo .] [--base REF] [--effort quick|standard|deep] \
  [--lang python,go,rust,typescript] [--harness omp|claude] [--model M] [--verify-model M] [--out RUN] [--jobs N] [--max-agents N] \
  [--decompose ocr|hier|hier-split] [--decide] [--finder-passes 1|2]
```

The report is `RUN/report.md` (human) and `RUN/report.json` (machine). `report.md` opens with the verdict, the
tier counts and the next action, then lists the requirements (claims from commits, issues and specs, `R1…`, plus
`[block]` repo rules, `B1…`) with the findings that put each at risk. Findings follow by action tier: must fix
(proven blockers), should fix (fix or reply `decision: <why>`), verify (unproven; a human decides), then one line
of optional items and the pre-existing ones. Each finding folds its evidence and fix: the proof run, the minimal
fix the proof agent applied in the sandbox, and up to two GitHub suggestion patches. Two folds close the report:
every review axis with its counts per tier and whether an agent checked it, and the coverage. `report.json` adds
`tier` and `sarif_level` to each finding, plus `requirements` and `decision`.

`--decide` (or `ARBITER_DECIDE=1`) adds one Opus call at the end of the run that links findings to requirements,
dismisses noise among non-blocking findings, flags must-fix findings it doubts and names up to three missed concerns
(unverified, never blocking). It is strict: once per run (a claim file in `RUN`), no retry, no tools, and omp's
`--max-cost` cap `ARBITER_DECIDE_MAX_USD` (default `1.00`, at most 5). Only an Opus model is accepted
(`ARBITER_DECIDE_MODEL`, default `anthropic/claude-opus-5-5`), and only through omp. Every omp call arbiter makes
loads `arbiter/omp-overlay.yml`, which turns omp's advisor off. The decide call may not dismiss a maintainability,
idiom, design or docs finding that cites a measured fact (`measure`) or a repo precedent (`precedent`): arbiter keeps
such a finding in place and counts the dismissal as `refused` in the coverage.

Every per-unit finder runs twice by default (in deep mode, every finder not already run three times), each pass
with its own file order, and the candidates are merged by location before the verifier ([benchmarks
§3.11](docs/benchmarks.md)). `--finder-passes 1` (or `ARBITER_FINDER_PASSES=1`) runs one pass. Over the agent
budget, the second pass is the last thing dropped, after deep mode's k.

Three recall techniques measured in wave 2a are off by default ([benchmarks §3.9](docs/benchmarks.md)):
`ARBITER_BASE_READS=1` gives finders and the verifier the base checkout path, `ARBITER_COCHANGE=1` lists files
that often changed together with each unit's files, and `ARBITER_SAST_CANDIDATES=1` turns analyzer hits on added
lines that no agent reported into verifier candidates.

`--decompose` (or `ARBITER_DECOMPOSE`) picks how the diff is split into review units; `arbiter plan` and
`arbiter eval seeded|martian|swr|aacr run` take it too:
- `ocr` (default): hunk chunking with OCR's sizes.
- `hier`: Python split by package, module, definition, method and statement (budget 150 churn, `ARBITER_UNIT_BUDGET`), plus a change manifest and context map per unit, cross-unit acceptance and root-cause dedup, and one contract pass for signature changes, removals and renames.
- `hier-split`: the split alone (the ablation arm).

These two are experimental until the A/B in [roadmap.md](docs/roadmap.md) P4 passes ([methodology §3.1](docs/methodology.md#31-decomposition-arbiterdiffpy-arbiterunitspy-arbiterdecomposepy)).

Evaluation commands (results in `eval/results/`, reported runs copied to `eval/scores/`):

```bash
arbiter eval seeded build|run [--lang L] [--case TEXT]
arbiter eval martian fetch|run --repo sentry|grafana|cal_dot_com [--limit N] [--offset N] [--pr TEXT]...
arbiter eval swr fetch|sample|run [--limit N] [--skip-scored FILE]
arbiter eval aacr fetch|run [--lang python,ts,go,rust] [--pr TEXT]... [--limit N]
arbiter eval aacr rescore --runs TS TS... --label NAME --label NAME...
```

Every `run` takes `--effort`, `--harness`, `--model`, `--verify-model`, `--decompose`, `--review-from DIR` and `--decide`:
- `--pr TEXT` (repeatable, `martian` and `aacr`) keeps only PRs whose URL ends with the text, such as `sentry-greptile/pull/3`.
- `--review-from DIR` reviews with the arbiter checkout at `DIR` (its `.venv`), so an old and a new version run the same items on the same day.
- `aacr` reviews AACR-Bench v2 PRs from the dataset's pinned repository snapshots and scores them with its file-level semantic coverage.
- `aacr rescore` judges the main findings of several finished runs (folders under `eval/results/aacr/`) in one pass with one judge, and adds the union of the first two runs, raw and merged by location.
- `--judge auto` (the default for `martian` and `aacr`) asks Cloudflare's Clef decision model first whether a finding and a reference describe the same concern, and uses its answer only when its confidence is at least `ARBITER_CLEF_MIN_CONF` (default 0.8, [benchmarks §3.10](docs/benchmarks.md)). Clef runs only inside the account's free Workers AI allowance: arbiter keeps a per-UTC-day neuron ledger in `~/.cache/arbiter/clef-usage.json`, stops at 9,000 of the 10,000 free neurons, and stops for the day on Workers AI's daily-allocation error. Every other case (no credentials, allowance spent, API error or rate limit, low confidence) falls back to the LLM judge. Credentials come from `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_AUTH_TOKEN`, or `~/.config/arbiter/cloudflare.env` (mode 600). `--judge sonnet` skips Clef.

The decision ledger is `docs/decisions.jsonl`; `docs/decisions.md` is rendered from it. `arbiter ledger list
[--status S] [--area A] [--since DATE]`, `show ID`, `render` and `check` (rows valid and render current).

| Exit | Meaning |
|---|---|
| 0 | no Block findings |
| 1 | Block findings present |
| 2 | usage/config error |
| 3 | empty diff |
| 4 | diff too large (cap 500 files / 8000 lines) |
| 5 | internal failure |

| | quick | standard (default) | deep |
|---|---|---|---|
| Finders per unit | A1a A1b A2 A3 A6a | A1a A1b A1c A2 A3 A6a A6b A6c A6d | same as standard |
| Once per run | A0 | A0 SPEC | A0 SPEC |
| Conditional | none | triggered A4 A5 A5b A7 A8 A9 | same as standard |
| k passes | 2 | 2 | 3 for A1a A1b A2 A3 A4, 2 for the rest |
| Verifier | 1 vote | 3 lenses | 3 lenses |
| Proof rungs | E1 E3 | E1–E6 E8 | E1–E9 |
| Code judo | off | should-fix only | blockers with an E1 measured fact |

## Review techniques

Every technique the review applies today, on by default or behind a switch. The table is rendered from the decision
ledger by `arbiter ledger render`, and `arbiter ledger check` (part of `make check`) fails when it is stale. Proposed,
deferred and dropped ideas are in [docs/decisions.md](docs/decisions.md).

<!-- techniques:begin (arbiter ledger render) -->
| ID | Technique | Status |
|---|---|---|
| A-02 | Stdlib-only package | adopted |
| A-04 | Proof agent restricted to `arbiter sandbox exec` | adopted: open concern |
| A-05 | Hard proof gate: a functional finding blocks only with a confirmed proof at an accepted rung | adopted |
| A-07 | 3-lens disprove panel with a never-auto-dismiss CWE list | adopted |
| A-09 | Merge findings at one location under the highest-priority axis | adopted: open concern |
| A-10 | Fail closed when more than 25% of agent calls fail | adopted |
| A-11 | Proofs run one at a time | adopted |
| A-12 | bubblewrap sandbox: network off, `$HOME` hidden, env cleared | adopted: open concern |
| A-16 | omp advisor forced off on every arbiter call; one strictly capped Opus decision call per review (`--decide`) | adopted: opt-in, wave 2a |
| M-02 | Haiku finders, Sonnet verifier, proof agent and judge | adopted: confirmed 2026-11-24 |
| M-03 | Resolve models from omp roles (`arbiter-finder` or `smol`; `arbiter-verify`) | adopted |
| M-04 | Cost ceiling `ARBITER_BLOCKED_MODELS` (default `opus,fable`) applied to the resolved model | adopted |
| M-05 | Preflight each model: read a file, answer JSON | adopted |
| U-01 | OCR-style units: at most 150 changed lines, hunk chunks, merge up to 10 files | adopted: default |
| U-02 | Hierarchical split: package → module → definition → method → statement (Python, `ast`) | switch: `--decompose hier` |
| U-05 | Changed-symbol manifest and signature map per unit, built with zero model calls | switch |
| U-06 | Accept findings in any changed hunk of the PR; cluster by changed symbol | switch |
| U-07 | One contract pass per PR for signature changes | switch |
| T-01 | SAST hits as verifier candidates, with a CWE-specific lens | switch: `ARBITER_SAST_CANDIDATES=1`, wave 2a |
| T-03 | Repeated cheap finder passes merged by location (k=2 per unit at quick and standard effort) | adopted: default, wave 2b; `ARBITER_FINDER_PASSES=1` for one pass |
| T-04 | Co-change neighbour map from `git log` | switch: `ARBITER_COCHANGE=1`, wave 2a |
| T-12 | Place a verified (panel TRUE_POSITIVE) but unproven finding in the main section as should-fix when the proof could not run for environment reasons (dependency fetch failed), instead of in Suspected; blocking still needs a proof | adopted: wave 1, 2026-11-24 |
| T-13 | Repair a finding with empty `evidence_lines` from its `file:line` instead of rejecting it | adopted: wave 1, 2026-11-24 |
| T-18 | Anchor a finding by its quoted code snippet (OCR `existing_code`: match the diff hunks, then the whole file, then one LLM relocation) instead of rejecting findings with a bad line or empty evidence | adopted: wave 1, 2026-11-24, merged with T-13; hunk match only |
| T-19 | Let finders read the base side (OCR #1915: `side: old` on read and search tools); today they see the base only as `-` lines in the diff | switch: `ARBITER_BASE_READS=1`, wave 2a |
| T-27 | Reasoning before verdict: finders write `trigger` and `evidence_lines` before `claim` and `severity` | adopted: wave 2a |
| T-31 | Check linked tickets and specs for requirement gaps | adopted: existing |
| T-32 | Treat PR title, description, commits and tickets as untrusted | adopted: existing |
| T-34 | Runtime verifier that also lists what it could not observe | adopted: existing |
| T-35 | "Only post what could change a merge decision" | adopted: in part |
| MA-01 | Maintainability is a first-class axis: it reduces future pain (user decision, 2026-11-24) | adopted |
| MA-03 | Deterministic maintainability facts (Python `ast`, base vs head): complexity, nesting, length, params, file crossing 1,000 lines | adopted: wave 1 |
| MA-04 | A6d readability agent: names, dead code, complexity, nesting, magic numbers, flag arguments | adopted: wave 1, open concern |
| MA-05 | Blocking policy: a maintainability finding may block only with a block-eligible measured fact or a repo rule heading marked `[block]`; otherwise should-fix (user decision, 2026-11-24) | adopted: wave 1 |
<!-- techniques:end -->

## Models

arbiter works with any model its harness can call: Haiku, Sonnet, DeepSeek, GPT and other cheap models. Pick the
harness with `--harness` or `ARBITER_HARNESS` (`omp`, the default, or `claude`). Each role resolves in this order:

| Role | 1. flag or environment | 2. omp role | 3. fallback (`omp` / `claude`) |
|---|---|---|---|
| Finders, A0, SPEC | `--model`, `ARBITER_MODEL` | `arbiter-finder`, then `smol` | `anthropic/claude-haiku-5-5` / `haiku` |
| Verifier, proof agent, eval judge | `--verify-model`, `ARBITER_VERIFY_MODEL` | `arbiter-verify` | `anthropic/claude-sonnet-5-5` / `sonnet` |

- A flag value may name an omp role (`--model @smol`). Role values are resolved the way omp does: first candidate, `@alias` followed, `:thinking` suffix dropped.
- omp's `default` and `slow` roles are never used: they are usually the premium model.
- To route arbiter without flags, add the roles to `~/.omp/agent/config.yml`. For example, to use DeepSeek for finders and Sonnet to verify:
  ```yaml
  modelRoles:
    arbiter-finder: deepseek/deepseek-v4.1
    arbiter-verify: anthropic/claude-sonnet-5-5
  ```
- **Cost ceiling.** A resolved model whose name contains an entry of `ARBITER_BLOCKED_MODELS` (default `opus,fable`) is refused with exit 2. The one exception is the `--decide` call above, capped per call.
- **Preflight.** Before any review work, each model must read a file with its tool and answer in JSON. A model the harness cannot call, or one without tool use, exits 2 with the reason instead of failing every agent call.

## Accuracy

Seeded corpus: 20 bug cases and 8 clean cases, 5 bug and 2 clean per language, at `standard` effort with the `omp` harness.
A main-section finding counts as a match when it is in the same file, within 3 lines of the expected line, and on one of
the expected axes. The targets were precision ≥ 0.80, recall ≥ 0.70 and no findings on clean cases.
Precision missed its target after the 2 allowed brief revisions.

| Run | Models (finder / verify) | Precision | Recall | Clean-case findings |
|---|---|---|---|---|
| round 0 (as built) | omp default `anthropic/claude-opus-5-5` (before the cost ceiling) / same | 0.40 | 0.83 | 1 |
| round 1 (A1c A6a A6b A6c tightened) | same | 0.585 | 0.83 | 0 |
| round 2 (final briefs) | same | 0.606 | 0.76 | 0 |
| cheap model, final briefs | `anthropic/claude-haiku-5-5` / same | 0.69 | 0.62 | 1 |

In round 2, 13 of the 33 main findings did not match the corpus:
- 5 are deterministic gate hits. staticcheck reports SA4006 and SA4017 on the shadowed `err`, and rustfmt diffs 3 files.
- 4 are real defects on an axis the corpus does not list. Examples: the missing `Cancelled` case as logic rather than idiom, and `Box<dyn Error>` as errors rather than idiom.
- 4 are judgment findings: 2 on tests, 1 on observability and 1 on docs.

Real PRs, current defaults (2026-11-23 matrix, Python and TypeScript; Go and Rust postponed). Each setup ran once at `standard` effort.
- **H+S:** Haiku finders with Sonnet verifier, proof agent and judge (the default).
- **S+S:** Sonnet in every role.

| Dataset | H+S precision / recall / F1 | S+S precision / recall / F1 |
|---|---|---|
| Seeded Python+TS, 14 cases | 0.56 / 0.69 / 0.61 | 0.48 / 0.81 / 0.60 |
| Martian sentry (Python), 10 PRs | 0.31 / 0.36 / 0.34 | 0.29 / 0.42 / 0.34 |
| Martian cal.com (TS), 10 PRs | 0.42 / 0.43 / 0.43 | 0.36 / 0.51 / 0.42 |
| SWR-Bench, 40 PRs (28 issue, 12 clean) | 0.67 / 0.26 / 0.38 | 0.38 / 0.24 / 0.29 |

- Sonnet finders trade precision for recall on seeded and Martian, and lose on every metric on SWR-Bench. Haiku finders stay the default.
- Neither setup blocked a clean SWR PR or reported anything on a clean seeded case.
- Martian scoring: `withmartian/code-review-benchmark`, Core categories, one LLM judge. Martian publishes 47.7 F2 Core for Claude Code CLI over the full set; arbiter's F2 here is 0.35–0.47.
- The earlier Opus runs (grafana included) were partial because of rate limits; [docs/benchmarks.md](docs/benchmarks.md) §3.4–§3.6 keeps them.

**Maintainability is scored separately in every benchmark.** Each eval summary reports maintainability recall next to functional recall: SWR-Bench `E.*` changes, Martian `style` comments, AACR "Maintainability and Readability" comments, and the seeded evolvability axes. Maintainability findings need a rule plus a repo precedent, a linter id or a fact arbiter measured (complexity, nesting, length, parameters, file size; Python only for now). Their severity is capped at `should-fix`. Three exceptions may block: a finding whose `measure` names a block-eligible fact arbiter measured, a finding whose `rule` names a repo rule heading marked `[block]`, and a deep-mode code-judo finding with a confirmed E1 measured fact.

Per-case and per-PR tables, the ground truth for each case, and threats to validity are in
[docs/benchmarks.md](docs/benchmarks.md). The score files are in [eval/scores/](eval/scores/).
