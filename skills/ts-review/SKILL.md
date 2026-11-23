---
name: ts-review
description: TypeScript code review by arbiter against Handbook Do's and Don'ts, Google TS guide, typescript-eslint strict, Effective TypeScript. Autonomous, evidence-gated: correctness, security, idiom, design and clean code; every blocking finding is proven. Runs unattended; use when reviewing TypeScript changes.
argument-hint: "[base-ref] [--effort quick|standard|deep]"
---

1. Never ask the user anything. Never edit the reviewed repo.
2. Run:
   ```bash
   arbiter run --repo . --lang typescript $ARGUMENTS </dev/null
   ```
   If the shell says `arbiter: command not found`, report "arbiter is not installed: run `make install` in the
   arbiter checkout" and stop.
3. The first stdout line is the RUN path. Read `RUN/report.md` and relay it verbatim, followed by one line with the verdict and the exit code.
4. Do not add, re-rank or soften findings. The report is the review.
5. If the exit code is 2–5, print the stderr line and stop.

References for this language live in `references/` and are loaded by arbiter automatically.
