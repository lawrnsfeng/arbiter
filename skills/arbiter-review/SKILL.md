---
name: arbiter-review
description: Autonomous, evidence-gated code review of a git diff (base...HEAD) for Python, Go, Rust and TypeScript - correctness, edge cases, error handling, concurrency, security/privacy, API/data contracts, supply chain, performance, ops, a11y, plus idiom, design and clean code per each language's canon. Every blocking finding is proven by tool output, a test or a sandboxed run. Runs unattended with no questions; returns a verdict and exit code. Use for any code review request or as a CI/agent-workflow gate.
argument-hint: "[base-ref] [--effort quick|standard|deep] [--lang L]"
---

# arbiter-review

arbiter is a deterministic pipeline (`arbiter run`). It splits the diff into small units, runs one-job agents per unit,
votes each candidate through a disprove panel, proves functional findings in a bubblewrap sandbox, and gates every
blocking finding on ground truth. This skill only launches it and relays the report.

1. Never ask the user anything. Never edit the reviewed repo.
2. Run, from the repository root:
   ```bash
   arbiter run --repo . $ARGUMENTS </dev/null
   ```
   If the shell says `arbiter: command not found`, report "arbiter is not installed: run `make install` in the
   arbiter checkout" and stop.
   The first stdout line is the RUN directory; the last line is `verdict PASS|BLOCK · report <path>`.
3. Read `RUN/report.md`. Relay it verbatim, followed by one line with the verdict and the exit code.
4. Do not add, re-rank or soften findings. The report is the review.
5. If the exit code is 2–5, print the stderr line and stop.

Exit codes: `0` no Block findings · `1` Block findings present · `2` usage/config error · `3` empty diff ·
`4` diff too large · `5` internal failure.

Efforts: `quick` (5 finders, 1 vote, E1/E3 proofs) · `standard` (default: 8 finders + triggered specialists, 3-lens
panel, E1–E6/E8) · `deep` (k=3 passes on correctness/security/concurrency, E1–E9, code-judo blockers).

Models: any model the harness can call works (Haiku, Sonnet, DeepSeek, GPT and other cheap models). Finders use
`--model` / `ARBITER_MODEL`, else the omp role `arbiter-finder`, else `smol`, else Haiku. The verifier and proof agent
use `--verify-model` / `ARBITER_VERIFY_MODEL`, else the omp role `arbiter-verify`, else Sonnet. Models matching
`ARBITER_BLOCKED_MODELS` (default `opus,fable`) are refused with exit 2. A preflight checks each model can read a file
and answer in JSON before any review work; a model that cannot exits 2.
