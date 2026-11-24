Leader study, 2026-11-24: Augment Code Review, Qodo 2.0 (and open-source PR-Agent), cubic, alibaba OpenCodeReview and AACR-Bench. Every claim is the vendor's own unless marked measured.

# Leader approaches

## 1. Why

The top tools on the same 20 Martian PRs scored F2 0.58–0.65 against arbiter's 0.40 (benchmarks §3.7). The recall trace showed the gap:
- 12 of 20 bugs that the leaders agree on and arbiter missed were never raised by a finder;
- 8 were raised and then lost: 2 to validation, 4 to the verifier and 2 to Suspected placement.

On SWR-Bench, arbiter found 1 of 13 evolvability changes.

## 2. Sources

|Key|Source|URL|
|---|---|---|
|LD1|Augment, "How we built a high-quality AI code review agent" (2026-03-10)|https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent|
|LD2|Augment, "Why GPT-5.2 is our model of choice for Augment Code Review"|https://www.augmentcode.com/blog/why-gpt-5-2-is-our-model-of-choice-for-augment-code-review|
|LD3|Augment, "Code review at scale is broken" (launch, 2025-12-11)|https://www.augmentcode.com/blog/introducing-augment-code-review|
|LD4|Augment docs, Code Review overview and Review Styles|https://docs.augmentcode.com/codereview/overview.md , https://docs.augmentcode.com/codereview/review-style.md|
|LD5|Augment, "How Cosmos accelerated … code review" (2026-05-06)|https://www.augmentcode.com/blog/solving-code-review-with-cosmos|
|LD6|Augment docs, Code Review Memory and the review pipeline|https://docs.augmentcode.com/cosmos/experts-code-review-memory.md , https://docs.augmentcode.com/cosmos/experts-code-review.md|
|LD7|Augment docs, Risk Analyzer, Deep Reviewer, Verifier|https://docs.augmentcode.com/cosmos/experts-risk-analyzer.md , …/experts-deep-reviewer.md , …/experts-verifier.md|
|LD8|Qodo, "Introducing Qodo 2.0" (2026-02-04)|https://www.qodo.ai/blog/introducing-qodo-2-0-agentic-code-review|
|LD9|Qodo, "How we built a real-world benchmark for AI code review"|https://www.qodo.ai/blog/how-we-built-a-real-world-benchmark-for-ai-code-review|
|LD10|Qodo docs, How code review works, Context Engine|https://docs.qodo.ai/code-review/overview , https://docs.qodo.ai/core-concepts/context-engine.md|
|LD11|Qodo docs, Relevance and Rule Miner|https://docs.qodo.ai/code-review/relevance.md , https://docs.qodo.ai/governance/rule-enforcement/rule-miner.md|
|LD12|Qodo docs, Merge Risk, Review effort mode, fix-loop optimization|https://docs.qodo.ai/code-review/assess-pull-request-merge-risk.md , https://docs.qodo.ai/code-review/use-qodo-in-prs/control-review-effort.md , https://docs.qodo.ai/code-review/optimize-review-focus-in-fix-loops.md|
|LD13|Qodo PR-Agent (open source) reviewer prompt|https://github.com/qodo-ai/pr-agent/blob/main/pr_agent/settings/pr_reviewer_prompts.toml|
|LD14|cubic, "Learnings from building AI agents"|https://www.cubic.dev/blog/learnings-from-building-ai-agents|
|LD15|cubic, "AI code review false positives"|https://www.cubic.dev/blog/the-false-positive-problem-why-most-ai-code-reviewers-fail-and-how-cubic-solved-it|
|LD16|cubic docs, Memory and learning|https://docs.cubic.dev/ai-review/memory-and-learning.md|
|LD17|Li et al., OpenCodeReview (arXiv 2608.09290v2)|https://arxiv.org/html/2608.09290v2|
|LD18|OCR releases v1.13.10–v1.14.2 (#1915 old-side tools, #1937 behavior/impact analysis)|https://github.com/alibaba/open-code-review/releases|
|LD19|AACR-Bench repo and metrics|https://github.com/alibaba/aacr-bench , https://github.com/alibaba/aacr-bench/blob/main/docs/metrics.md|
|LD20|Martian offline results, Sonnet 4.5 judge (pinned 23a35d0)|https://github.com/withmartian/code-review-benchmark/tree/23a35d0d64f7de5a68e5679da08414e0edacea9b/offline/results|
|LD21|OpenAI, GPT-6 Sol and Luna|https://openai.com/index/introducing-gpt-6-sol-and-luna|
|LD22|arbiter Martian recall trace (measured)|docs/benchmarks.md §3.7|
|LD23|arbiter SWR evolvability recall (measured): E.* 1/13 H+S, 2/13 S+S; F.* 11/33 both|eval/scores/swr-20261123031300.json, swr-20261123144505.json, swr-20261123195901.json|
|LD24|arbiter matrix (measured)|docs/benchmarks.md §3.7|

## 3. What each leader does, and why

**Augment** ([LD1]–[LD7]). F2 Core 0.65 on arbiter's 20 PRs (rank 1).
- **Context and inputs.**
  - Context beyond the diff through a semantic "Context Engine": token validation in other services, auth middleware, historical permission-check patterns, related APIs. Why: diff-only and grep-only review miss cross-system issues.
  - Repo-level and directory-scoped guidelines, plus `areas:` rules with `globs`, `id`, `description` and `severity`. Why: tribal knowledge is not in the code.
  - Deterministic injection of the diff and existing comments, rather than fetching them through tools. Why: stability.
  - The PR title and description are used as context. Why: better intent leads to more targeted reviews.
- **Prompts, tools and models.**
  - A system prompt that chooses either high signal or thoroughness, names the categories to avoid, recommends tool-use patterns and gives workflow steps. Why: the prompt is the precision/recall knob.
  - Tools with minimal overlap, plus observability of tool use. Why: overlapping tools confuse models, and tool logs explain behaviour.
  - Prompts and tools are tuned per model. GPT-5.2 was chosen over Sonnet and Opus because it "makes more tool calls" and reasons longer for asynchronous review.
  - Guardrails: narrow tool operations, restricted shell, deterministic components.
  - Two review styles, Thorough (default, "50% more bugs") and Precise, "with the same low false positive rate". Philosophy: "If a comment won't likely change a merge decision, we don't post it."
  - Focus areas: bugs, security, correctness, cross-system breaks, invariants, change-impact risks and missing tests; not style nits.
- **Evals and learning.**
  - Offline evals hill-climb on F-score. Online metrics: bugs fixed per PR, % of comments addressed, and the distribution of comment categories.
  - Memory: capture, then curate, then load. A raw breadcrumb log of human comments, reactions and addressed requests is kept, alongside a curated per-repo knowledge file. Explicit human feedback outweighs reactions, so weak signals must recur. The memory is used to avoid known false positives.
  - It adapts to which comments developers address or ignore.
- **Cosmos pipeline.**
  - A Risk Analyzer routes each PR: low risk is auto-approved (about 10% at first), higher risk gets tagged review dimensions.
  - Deep Reviewer does line-by-line correctness.
  - Pair Reviewer is interactive with a human.
  - Verifier exercises the change at runtime and reports what could not be observed.
  - PR Author and Fixer close the loop.

**Qodo 2.0** ([LD8]–[LD13]). Qodo v2 is rank 2 at F2 0.61; Qodo extended v2 is rank 4.
- **Multi-agent architecture.**
  - Specialized agents, each with its own context, plus a judge agent that resolves conflicts, dedups and filters low-signal findings. Why: one agent doing everything trades depth for coverage.
  - Principle: "Precision can be tuned through filtering … Recall cannot."
  - Two configurations: Precise and Exhaustive.
- **Context from history and standards.**
  - Context Engine: codebase, PR history, tickets and standards.
  - A recommendation agent reads past PRs and review feedback. Why: avoid flagging deliberately accepted patterns, and catch divergence from established ones.
  - Relevance: each finding is tagged High, Medium or Low according to how similar findings were handled before, with links to those PRs.
  - Rule Miner:
    - only comments that were accepted and led to code changes count;
    - comments are weighted by the reviewer's code ownership;
    - a pattern must recur, though one strong-ownership comment can qualify;
    - rules are clustered by path;
    - dismissals fade a rule.
- **Risk and effort routing.**
  - Merge Risk: blast radius, behavioral complexity and potential damage, each with evidence.
  - Review effort Auto: a fast pre-analysis picks a Fast, Balanced or Deep review. When unsure it goes deeper. Example: a one-line billing change goes to Deep.
  - Fix-loop optimization: follow-up reviews narrow to the new fix commits.
- **Findings.** Each finding states what is wrong, why it matters and how to fix it, with evidence, a quality-dimension label, a snippet and an agent-ready remediation prompt. Qodo also checks requirement gaps against linked tickets.
- **Benchmark.** It injects 1–3 functional bugs *and* best-practice violations into real merged PRs (3+ files, 50–15,000 lines, no revert). The repo rules are extracted into AGENTS.md. A hit needs both the right text and the right location.
- **PR-Agent prompt (LD13).**
  - The PR title, description, commits and tickets are untrusted.
  - "For clear bugs and security issues, be thorough … do not skip a genuine problem just because the trigger scenario is narrow."
  - "Do not speculate that a change might break other code unless you can identify the specific affected code path."
  - Optional confidence 0–10; `existing_code`/`improved_code` of at most 10 lines; failure modes (what, where, trigger).

**cubic** ([LD14]–[LD16]). cubic v2 is rank 3 at F2 0.58.
- **Reasoning and tools.**
  - Explicit reasoning logs: the reasoning comes before the finding in the output. Why: it structures thinking and makes FPs debuggable.
  - A smaller toolset (a simplified LSP and a basic terminal). Why: extra tools caused confusion.
  - Type-aware analysis: static types are used to verify whether a flagged issue can happen.
  - Specialized micro-agents with a planner: security, duplication, editorial and so on. Why: rules piled into one big prompt were ignored.
  - Combined result: 51% fewer FPs at equal recall, and median comments per PR halved.
- **Learnings.**
  - Sources: replies, threads, reactions, and the historical comments of chosen senior reviewers.
  - Operations on each learning: create, improve, remove or keep.
  - Each learning has a "Do not apply when" exception.
  - A weekly cleanup merges duplicates and archives rules that no longer improve reviews.
  - Learnings can be imported as CSV from CodeRabbit.

**alibaba OpenCodeReview** ([LD17]–[LD19]).
- **Deterministic engineering at three points.**
  - Rule-guided dispatch.
  - Grounded review with 6 bounded tools: `file_read` 500 lines, search 100 matches, plus `file_read_diff`, run by one file-level subagent per file with up to 30 rounds.
  - A falsification-only reflector that sees only the diff and fails open.
- **Line resolution.** Each comment carries an `existing_code` snippet, which is matched against the diff hunks, then the whole file, then one LLM relocation.
- **Results.** SEM-F1 25.1% against Claude Code's 11.6% on AACR-Bench, using 5–15× fewer tokens.
- **v1.14.** `side: old` reads and an optional behavior/impact analysis.
- **AACR-Bench v2.** 151 PRs across 10 languages (20 Python, 19 TS, 17 Go, 7 Rust). Comment categories: Code Defect, Security Vulnerability, Performance, Maintainability and Readability. Scored by file-level semantic coverage: one judge call per generated comment, with greedy dedup for precision.

## 4. Measured on arbiter

|Measurement|Result|Source|
|---|---|---|
|Matrix|Haiku finders + Sonnet verifier stay the default; Sonnet finders lose on SWR-Bench (FP 18 vs 6)|LD24|
|Martian 20 PRs|H+S F2 0.40 (rank 18 of 51), S+S F2 0.43 (rank 15); tool mean 0.34; leaders 0.58–0.65|LD20, LD22|
|Recall trace, 70 Core goldens|28 hit, 32 never raised, 3 validation, 5 verifier, 2 Suspected|LD22|
|Evolvability recall|1/13 (H+S), 2/13 (S+S) on SWR-Bench|LD23|
