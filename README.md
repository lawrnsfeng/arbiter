# arbiter

Autonomous, evidence-gated code review for Python, Go, Rust and TypeScript. A deterministic Python pipeline
(`arbiter run`) splits `base...HEAD` into small units and runs one-job LLM agents on each: correctness, edge cases,
errors, security, concurrency, contracts, supply chain, performance, ops, a11y, idiom, design and docs. A disprove
panel votes on every candidate. Functional findings must be proven in a bubblewrap sandbox (repro test, snippet,
race detector, ...) before they can block. It never asks questions and ends with a verdict and an exit code.

**Current scores:** see [Accuracy](#accuracy) below. Full results are in [docs/benchmarks.md](docs/benchmarks.md), and the score files in [eval/scores/](eval/scores/).

## Material

Documentation:
- [docs/methodology.md](docs/methodology.md): design, the evidence behind each decision, decision log, deviations from the plan, limitations
- [docs/sources.md](docs/sources.md): papers, benchmarks and documents used, and what each changed
- [docs/benchmarks.md](docs/benchmarks.md): datasets, ground truth, scoring, full results, threats to validity
- [docs/roadmap.md](docs/roadmap.md): Python-first improvement plan, next datasets, path to an independent agent

Research (byte-identical copies from the 2026-11-21 research session; each file has its own source table with URLs):
- [research/research-axes.md](research/research-axes.md): review-axis taxonomy, agent grouping, priority
- [research/research-decompose-verify.md](research/research-decompose-verify.md): unit sizing, per-language command cookbook, evidence ladder, sandbox rules
- [research/research-security.md](research/research-security.md): security review method, per-language checklists, supply chain, LLM vulnerability-detection accuracy
- [research/research-ai-review-systems.md](research/research-ai-review-systems.md): how current AI review systems work, published benchmarks, precision techniques
- [research/prior-mint-review-research.md](research/prior-mint-review-research.md): OCR, mattpocock, Google eng-practices, pstack code judo
- [research/review-python.md](research/review-python.md), [research/review-go.md](research/review-go.md), [research/review-rust.md](research/review-rust.md), [research/review-typescript.md](research/review-typescript.md): per-language canon, tool layer, idioms, patterns, smells, severity

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
  [--lang python,go,rust,typescript] [--harness omp|claude] [--model M] [--verify-model M] [--out RUN] [--jobs N] [--max-agents N]
```

The report is `RUN/report.md` (human) and `RUN/report.json` (machine).

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
| Finders per unit | A1a A1b A2 A3 A6a | A1a A1b A1c A2 A3 A6a A6b A6c | same as standard |
| Once per run | A0 | A0 SPEC | A0 SPEC |
| Conditional | none | triggered A4 A5 A5b A7 A8 A9 | same as standard |
| k passes | 1 | 1 | 3 for A1a A1b A2 A3 A4 |
| Verifier | 1 vote | 3 lenses | 3 lenses |
| Proof rungs | E1 E3 | E1–E6 E8 | E1–E9 |
| Code judo | off | should-fix only | blockers with an E1 measured fact |

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
- **Cost ceiling.** A resolved model whose name contains an entry of `ARBITER_BLOCKED_MODELS` (default `opus,fable`) is refused with exit 2.
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

Martian golden set: `withmartian/code-review-benchmark` at the commit recorded in `eval/martian/golden/SOURCE.json`.
An LLM judge (`ARBITER_VERIFY_MODEL`) pairs findings with golden comments, and scoring uses the Core categories.
These runs used the omp default model (Opus) at `standard` effort.

| Repo | PRs scored | Precision | Recall | F1 | F2 |
|---|---|---|---|---|---|
| sentry (Python) | 7 of 10 (3 lost to the rate limit) | 0.43 | 0.44 | 0.44 | 0.44 |
| grafana (Go) | 3 | 0.40 | 0.18 | 0.25 | 0.20 |
| cal.com (TS) | 3 | 0.25 | 0.30 | 0.27 | 0.29 |

For reference, Martian publishes 47.7 F2 Core for Claude Code CLI over the full set. These samples are too small to compare against it.

SWR-Bench (`ZZR0/SWRench`, MIT; 1,000 real Python PRs): the 40-PR sample was cut short by the rate limit. Only 12 PRs
were scored, all with issues, so false alarms on clean PRs are still unmeasured. On those 12: precision 0.58,
recall 0.37, F1 0.45. Benchmarks are paused until they can be rerun on the Haiku/Sonnet defaults.

Per-case and per-PR tables, the ground truth for each case, and threats to validity are in
[docs/benchmarks.md](docs/benchmarks.md). The score files are in [eval/scores/](eval/scores/).
