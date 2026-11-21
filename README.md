# arbiter

Autonomous, evidence-gated code review for Python, Go, Rust and TypeScript. A deterministic Python pipeline
(`arbiter run`) splits `base...HEAD` into small units and runs one-job LLM agents on each: correctness, edge cases,
errors, security, concurrency, contracts, supply chain, performance, ops, a11y, idiom, design and docs. A disprove
panel votes on every candidate. Functional findings must be proven in a bubblewrap sandbox (repro test, snippet,
race detector, ...) before they can block. It never asks questions and ends with a verdict and an exit code.
Research and citations: `research/`.

## Install

```bash
make install     # symlinks skills/* into ~/.claude/skills (omp loads them via skills.enableClaudeUser)
make test        # unit tests (no network, no LLM)
```

Skills: `arbiter-review` (core launcher), `python-review`, `go-review`, `rust-review`, `ts-review`.

## Run

```bash
uv run --project ~/relic/arbiter arbiter run [--repo .] [--base REF] [--effort quick|standard|deep] \
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

`ARBITER_HARNESS` = `omp` (default) or `claude`. `ARBITER_MODEL` sets finders, A0 and SPEC; `ARBITER_VERIFY_MODEL` sets
the verifier, proof agent and eval judge (defaults to `ARBITER_MODEL`). Both default to the harness's own default.
The flags `--harness`, `--model` and `--verify-model` override the environment.

## Accuracy

Seeded corpus: 20 bug cases and 8 clean cases, 5 bug and 2 clean per language, at `standard` effort with the `omp` harness.
A main-section finding counts as a match when it is in the same file, within 3 lines of the expected line, and on one of
the expected axes. The targets were precision ≥ 0.80, recall ≥ 0.70 and no findings on clean cases.
Precision missed its target after the 2 allowed brief revisions.

| Run | Models (finder / verify) | Precision | Recall | Clean-case findings |
|---|---|---|---|---|
| round 0 (as built) | omp default `anthropic/claude-opus-5-5` / same | 0.40 | 0.83 | 1 |
| round 1 (A1c A6a A6b A6c tightened) | same | 0.585 | 0.83 | 0 |
| round 2 (final briefs) | same | 0.606 | 0.76 | 0 |
| cheap model, final briefs | `anthropic/claude-haiku-5-5` / same | 0.69 | 0.62 | 1 |

In round 2, 13 of the 33 main findings did not match the corpus:
- 5 are deterministic gate hits. staticcheck reports SA4006 and SA4017 on the shadowed `err`, and rustfmt diffs 3 files.
- 4 are real defects on an axis the corpus does not list. Examples: the missing `Cancelled` case as logic rather than idiom, and `Box<dyn Error>` as errors rather than idiom.
- 4 are judgment findings: 2 on tests, 1 on observability and 1 on docs.

Martian golden set: `withmartian/code-review-benchmark` at the commit recorded in `eval/martian/golden/SOURCE.json`.
The sample is the first 3 PRs per repo. An LLM judge (`ARBITER_VERIFY_MODEL`) pairs findings with golden comments.
Scoring uses the Core categories. The model is the omp default, at `standard` effort.

| Repo | PRs | Precision | Recall | F1 | F2 |
|---|---|---|---|---|---|
| sentry (Python) | 3 | 0.50 | 0.73 | 0.59 | 0.67 |
| grafana (Go) | 3 | 0.40 | 0.18 | 0.25 | 0.20 |
| cal.com (TS) | 3 | 0.25 | 0.30 | 0.27 | 0.29 |

For reference, Martian publishes 47.7 F2 Core for Claude Code CLI over the full set. This 9-PR sample is too small to compare against it.
