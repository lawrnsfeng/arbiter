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

Filled in from `eval/results/` (`arbiter eval seeded run`, `arbiter eval martian run`).
