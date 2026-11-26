Context pack for a refactorer specialist, 2026-11-26. Draft for the owner's review before it goes to Fable as one
prompt ([prompts/2026-11-26-fable-refactorer-draft.md](prompts/2026-11-26-fable-refactorer-draft.md)). Gathered
from the repo only; no new web research yet.

# Refactorer specialist: context

## 1. How design patterns and clean code are reflected today

Four finder agents own the evolvability group (`maintainability`, `design`, `idiom`, `docs`; `arbiter/model.py`
`EVOLVABILITY`). Each is a brief in `skills/arbiter-review/references/agents/` plus per-language references.

| Agent | Owns | Reads | Evidence it must cite |
|---|---|---|---|
| A6a idiom | added code that breaks the language canon or the repo's idiom | `idioms.md`, `tools.md` (tool-silent list), `canon.md` | canon rule + repo precedent, or a lint id |
| A6b design | wrong layer, needless abstraction, duplicated helper, smell with a named refactoring, pstack "code judo" | `design.md` (§4 GoF patterns → language-native replacement; §5 smell → refactoring), `canon.md` | `rule` + `precedent` (repo `path:line`); at most one design finding per unit |
| A6c docs | missing or wrong docs on public API | `canon.md` | rule + repo precedent |
| A6d readability | names, dead code, long functions, nesting, magic numbers, flag arguments | `design.md`, `canon.md`, `tools.md` + arbiter's measured facts | `measure` (fact id) or `precedent` |

Deterministic support: `arbiter/maintain.py` (ledger MA-03) measures base vs head on **Python only** with `ast`:
complexity, nesting, length, parameter count, a file crossing 1,000 lines. Thresholds from radon ranks C/D, pylint
defaults and pstack. TypeScript, Go, Rust facts are deferred (MA-08).

Gate (`arbiter/findings.py` `gate()`, lines 481–503): an evolvability finding with no rule, or with a rule but no
lint id, repo precedent or measured fact, is **dropped**. It may block only with a block-eligible measured fact, a
repo rule heading marked `[block]`, or confirmed code judo at deep effort (MA-05); otherwise should-fix or nit. Nits
cap at 10, evolvability nits overflow first (`pipeline.py` 594–599). `--decide` may not dismiss a backed one (MA-01).

Per-language design canon: `skills/{python,go,rust,ts}-review/references/design.md`, copied from
`research/review-<lang>.md`. Example (Python): Singleton → module global; Strategy/Command → pass functions;
`isinstance` switch → `singledispatch`/`match`; 4+ return values → dataclass.

## 2. Where a user rulebook plugs in today

| Mechanism | State | What it does | Limit |
|---|---|---|---|
| Repo rule files | built (`plan.py` `_rules`, lines 151–160) | reads `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.claude/rules/*.md` **from the reviewed repo**, concatenates them into `RUN/rules.md`, injects as "Repo rules" text into every finder, verifier and proof prompt | 20 KB cap, then truncated with a note; read from HEAD, not base (R-00 open); no per-rule tracking |
| `[block]` headings | built (MA-05) | a heading containing `[block]` becomes a `path#heading` key; a finding whose `rule` names it may block, and it becomes a `B…` requirement in the report | only headings, not bullets |
| Preamble rule 8 | built | "repo rules override canon" | |
| `.arbiter/rules.jsonl` | **proposed** (R-01) | structured rules: id, kind check/suppress, text, rationale, axis, severity ceiling, scope (langs, paths, tokens, semgrep), bad/good hunks, status | design in `research/research-learned-rules.md` §5.1 |
| `arbiter rules import FILE` | **proposed** (§5.7) | import the owner's existing rule list (e.g. `tasks/lessons.md`), one rule per heading or bullet | without a linked PR a rule can only be a prompt rule capped at nit |
| Compile rules to semgrep | **proposed** (R-03) | zero model calls per check | only for rules expressible as patterns |
| Retrieval cap | **proposed** (§5.3) | at most 8 rules and 2k tokens per unit | conflicts with "every rule must be traversed" (§4 C1) |
| Many rules as prompt text | **dropped** (R-06) | | 68% accuracy at 500 instructions; rules 49.0% vs raw examples 53.5% `[LR]` |

**Answer to "is there a placeholder":** no global or user-level rulebook exists. The only seam is a rule file in the
reviewed repo, injected as unstructured text, with no record of which rule was checked against which code. Nothing
today guarantees every rule is traversed.

## 3. Measured state of maintainability review

| Measure | Value | Source |
|---|---|---|
| SWR-Bench evolvability changes found | 1 of 13 | ledger MA-01 |
| AACR maintainability recall, wave 1 (8 items) | 2/9 both arms | benchmarks.md lines 407–412 |
| AACR ComfyUI 8446 | 0/4: A6d raised 4 real-looking items, none matched a reference | benchmarks.md line 395 |
| Past runs, all 374 `report.json` | 22 maintainability findings (20 nit, 2 should-fix), 0 blocking; evolvability group 192 main findings | counted 2026-11-26 |
| LLM design comments resolved | 28.6% | AX-S10 |

## 4. Concerns to settle before building

| # | Concern | Evidence | Options |
|---|---|---|---|
| C1 | **Exhaustive traversal vs. prompt capacity.** "Every rule must be checked" cannot be one prompt with the whole rulebook | R-06: 68% instruction-following at 500 rules; Lost in the Middle (DV-S2); the 20 KB truncation today | per-rule × per-unit check matrix; rule batches per call; compile what can be compiled (semgrep, `ast`); retrieval to pre-filter "not applicable" deterministically, then check the rest |
| C2 | **Proof of traversal.** A reviewer must show each rule's outcome, not just findings | report design A-17 already wants "what was not checked" | a coverage ledger `rule × unit → applies / pass / violation / not applicable (why)`; shown as a matrix in the report |
| C3 | **Reviewer or doer?** A specialist that *finds* refactorings vs. one that *performs* them | arbiter's proof agent already applies minimal fixes in a sandbox | finder only; finder + proposed patch; full refactor agent with behaviour-preservation proof (tests before/after, the owner's `safe-refactor` skill pattern) |
| C4 | **Behaviour preservation.** A refactor must not change behaviour | existing evidence ladder E1–E8; E4 fail-before/pass-after | for a refactor: tests pass before and after, plus characterization tests when none cover the code |
| C5 | **Noise.** Design comments have the lowest acceptance | AX-S10 28.6%; RevMate ~35% rejected as trivial; A6b "one finding per unit" | rulebook hits are rule-backed, so they may earn a higher cap; taste stays excluded |
| C6 | **Rule provenance and injection.** Rule files can hide instructions | R-00: read rules from base; strip invisible Unicode | load from base ref; sanitize; the rulebook diff is itself a review unit |
| C7 | **Rule format.** Free markdown vs. structured | R-01 schema; MA-05 only honours headings | each rule needs id, scope, check type (deterministic / model), severity ceiling, example bad/good |
| C8 | **Languages.** Measured facts are Python only | MA-08 deferred | which languages first |
| C9 | **Where the rulebook lives.** The reviewed repo, the owner's home (`~/.arbiter/rules`), or both with precedence | repo rules override canon today | layered: canon < user rulebook < repo rules, or user rulebook wins |
| C10 | **Cost.** Exhaustive checking multiplies calls | Martian PR: 20–106 calls today | deterministic tier first; batch rules by axis; only changed code |

## 5. Resources already in the repo

| File | Use for the refactorer |
|---|---|
| `research/research-learned-rules.md` | rule schema, ingestion, retrieval, deterministic tier, suppression, import of the owner's rules (§5), risks (§3.6) |
| `research/research-axes.md` §2b | maintainability and design axis definitions, review-comment taxonomies |
| `research/prior-mint-review-research.md` | pstack code judo presumptive blockers, mattpocock standards vs spec, Google eng-practices |
| `research/review-{python,go,rust,typescript}.md` | per-language patterns, smells → refactorings, version-gated modernization |
| `research/research-code-quality-platforms.md` | SonarQube, Codacy, Qlty, DeepSource, Semgrep: rule engines and quality gates to reuse |
| `research/research-leader-approaches.md` | Qodo Rule Miner, cubic learnings, maintainability as first-class |
| `skills/arbiter-review/references/agents/A6a.md`–`A6d.md`, `skills/*-review/references/design.md` | current briefs and canon |
| `arbiter/maintain.py`, `arbiter/findings.py` `gate()`, `arbiter/plan.py` `_rules` | code seams the specialist would extend |
| `docs/decisions.jsonl` MA-01..MA-08, R-00..R-07 | decisions already taken |
| owner's skills `safe-refactor`, `code-simplifier` agent, `ponytail` | existing behaviour-preserving refactor practice to align with |

## 6. Questions for the owner (answer before sending)

1. Reviewer only, reviewer + proposed patch, or an agent that performs the refactor (C3)?
2. Where does your rulebook live, and does it override or sit under repo rules (C9)? Do you have a draft rulebook to
   attach?
3. Must every rule be checked on every change, or every rule that applies (deterministically filtered) (C1)?
4. Which languages first (C8)?
5. Should rulebook violations be able to block, or stay should-fix unless marked `[block]`?

Answers so far (owner, 2026-11-26):
- Python only for now.
- The rulebook is the owner's (OOP-leaning, opinionated); each rule is a pattern with × incorrect and ✓ correct
  examples, captured from images. Lives in this repo: [rulebook/](../rulebook/).
- Detection must be by a scanner that finds every occurrence where a pattern can express the rule; a semantic model
  check with high thinking where it cannot. Every known rule is traversed; all findings go to the report and verdict.
- Feasibility checked before building: [rulebook-feasibility/README.md](rulebook-feasibility/README.md).
- Question 1 answered: the refactorer performs the refactor, as a separate skill/agent (`python-refactor`,
  `refactorer`). Review owns behaviour and feature quality; the refactorer owns clean code. It writes to the working
  tree uncommitted, tests green before and after; scope defaults to uncommitted changes, extends to the feature
  branch or the whole codebase. A review whose `report.json` has `refactor.needed` hands off to it.
- Still open: question 5 (blocking); every owner rule is `severity: should-fix` for now.
