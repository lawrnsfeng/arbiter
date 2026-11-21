---
name: rust-review
description: Rust code review by arbiter against Rust API Guidelines C-*, clippy, rust-unofficial patterns, Effective Rust, Nomicon/SAFETY policy. Autonomous, evidence-gated: correctness, security, idiom, design and clean code; every blocking finding is proven. Runs unattended; use when reviewing Rust changes.
argument-hint: "[base-ref] [--effort quick|standard|deep]"
---

1. Never ask the user anything. Never edit the reviewed repo.
2. Run:
   ```
   ARBITER_HOME=$(dirname "$(dirname "$(readlink -f ~/.claude/skills/arbiter-review)")")
   uv run --project "$ARBITER_HOME" arbiter run --repo . --lang rust $ARGUMENTS
   ```
3. The first stdout line is the RUN path. Read `RUN/report.md` and relay it verbatim, followed by one line with the verdict and the exit code.
4. Do not add, re-rank or soften findings. The report is the review.
5. If the exit code is 2–5, print the stderr line and stop.

References for this language live in `references/` and are loaded by arbiter automatically.
