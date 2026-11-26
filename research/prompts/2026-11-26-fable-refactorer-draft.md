SUPERSEDED, never sent: the refactorer was built directly (`skills/python-refactor/`, `agents/refactorer.md`, ledger R-10) on the owner's `rulebook/`. Kept as the design brief it was.

You are the designer of arbiter's refactorer specialist. You get exactly one prompt: this one. Work autonomously to completion; never ask questions. Repo: /home/lawrence/relic/arbiter (cwd). Today: <DATE>.

# Goal
arbiter reviews code changes with evidence-gated finder agents. Design patterns and clean code are covered today by four finder agents (A6a idiom, A6b design, A6c docs, A6d readability) and Python-only measured facts, and maintainability recall is poor (SWR-Bench evolvability 1/13; AACR 2/9). The owner wants a refactorer specialist that checks code against a design/clean-code rulebook of the owner's own, and guarantees that every applicable rule is traversed and its outcome recorded.

# Read first (do not redo this context)
- research/refactorer-context.md: today's state, the rulebook seam, measurements, concerns C1-C10, resources, the owner's answers.
- research/research-learned-rules.md §5 (rule schema, retrieval, deterministic tier, import), §3.6 (risks).
- skills/arbiter-review/references/agents/A6a.md, A6b.md, A6d.md; skills/python-review/references/design.md; arbiter/maintain.py; arbiter/findings.py gate(); arbiter/plan.py _rules; docs/decisions.jsonl rows MA-01..MA-08, R-00..R-07.
- research/research-report-ux.md: the report design the specialist's output must fit (requirement matrix, needs-you list, "what was not checked").

# Owner's answers
1. Role (reviewer / reviewer + patch / performs refactor): <ANSWER>
2. Rulebook location and precedence: <ANSWER>; draft rulebook: <PATH or none>
3. Traversal: every rule on every change, or every applicable rule: <ANSWER>
4. Languages first: <ANSWER>
5. May rulebook violations block: <ANSWER>

# Task
1. Research (web_search + read primary sources; cite every claim with a URL; mark [unverified] / [INFERENCE]): how production tools and research check code against large rule sets exhaustively and prove coverage (SonarQube quality profiles, Semgrep rule packs, CodeQL query suites, PMD/Checkstyle, ArchUnit / import-linter / dependency-cruiser for architecture rules, Qodo Rule Miner, CodeRabbit path instructions, Cursor Bugbot rules, Copilot custom instructions); how LLMs follow many instructions (IFScale, instruction-density studies) and how to batch rules per call; refactoring detection and recommendation research (RefactoringMiner, JDeodorant, LLM refactoring studies, behaviour-preservation checks, characterization tests); clean-code and design-pattern canons usable as a default rulebook with their evidence.
2. Design: rule format (extend R-01 or replace), compile tiers (deterministic: semgrep / ast / architecture linters; model-checked: batched briefs), the traversal ledger (rule x unit -> applies / pass / violation / not applicable + reason), how findings flow through gate() and the report, cost per run, and the behaviour-preservation proof if the role includes patches.
3. Write research/research-refactorer.md (key prefix RF): sources table, findings, design, decisions, a phased plan with acceptance checks and a benchmark plan for maintainability recall. Tables over prose; terse.
4. Write a sample rulebook (research/mockups/rulebook-sample.jsonl, 10-15 rules spanning deterministic and model-checked) and a mock traversal ledger for the cal.com run (eval/results/martian/20261123233602/calcom-cal-com-pull-22532/), clearly labelled sample where invented.

# Rules
- Edit only under research/. Do not commit or push. Do not run arbiter's tests or evals.
- Save incrementally. Finish with a <= 20-line summary and what you could not verify.
