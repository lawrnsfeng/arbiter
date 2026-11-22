Findings below cover four sources: two projects named open-code-review (alibaba and spencermarx), mattpocock/skills `code-review`, and Google eng-practices. They are combined with mint's own rules in `.claude/rules/*.md` and `pyproject.toml`. I wrote nothing to disk. A ready `SKILL.md` draft is at the end.

## 1. What each project contributes

| Source | Main idea | What to take |
|---|---|---|
| **alibaba/open-code-review** (`ocr` v1.13.3 is installed here) | Fixed pipeline plus an LLM agent. Comments point to exact lines. Each language has its own rule file, e.g. `rule_docs/python.md`. | **Precision over recall.** Every finding gets a severity and a category. Review only added lines. Before flagging, read the surrounding context with a tool. A second pass removes only findings the diff proves wrong. Rules are layered: `--rule`, then repo, then home, then built-in. |
| **spencermarx/open-code-review** | Several reviewer personas (Fowler, Beck, Metz…) argue, then a "tech lead" merges the result. | Review against the requirements. Read project standards from `CLAUDE.md`. Turn findings into a human-voice review that follows Google's guidelines. |
| **mattpocock/skills `code-review`** | Two separate checks: **Standards** and **Spec**. Each runs in its own subagent, and the reports are never merged or reranked. | A baseline of 12 Fowler smells that always applies. **The repo's rules override it.** Smells are always "possible X", a judgement call. Skip anything a tool already enforces. Resolve the base ref and confirm the diff is non-empty before spawning agents. |
| **Google eng-practices** ([reviewer guide](https://google.github.io/eng-practices/review/reviewer/)) | Approve once the change clearly improves overall code health, even if it isn't perfect. | Review order: design, functionality, complexity, tests, naming, comments, style, docs. Prefix minor points with `Nit:` / `Optional:` / `FYI:`. |
| **Fowler, *Refactoring* 2e** ch.3 and the [catalog](https://refactoring.com/catalog/) | Smell → named refactoring. | The refactoring section below. |

## 2. The review standard

**Scope**
- Review the diff `git diff <base>...HEAD` (three dots, so it compares from the merge-base). Comment on `+` lines only. Deleted and unchanged lines are context.
- Before calling something a bug, read the callers or callee with a tool. Never assume what you didn't read (OCR: "confirm the data source with `file_read` before flagging").
- Cross-file checks are in scope: a contract changed in one file but not in its caller, test or fixture.

**Precision**
- A false alarm costs more trust than a missed minor issue. If the context is unclear, stay silent.
- Security and correctness findings block the merge. Style and idiom findings never do.
- Skip anything ruff, mypy or ty enforce. CI catches those.

**Taxonomy** (OCR's, adopted as is)
- Severity: `critical | high | medium | low`. Drop `low` from the report unless the user asks for everything.
- Category: `bug | security | performance | maintainability | test | style | documentation`.

**Evidence per finding:** `path:line`, category, severity, one sentence on the problem, one on the fix, and the quoted code. Hard rule violations cite the rule's file and heading. Smells are worded "possible Feature Envy".

**Self-filter pass:** re-check each finding against the code. Drop it only if it is **proven** wrong. "Low value" or "I can't verify" are not reasons to drop it.

**Two separate verdicts:** Standards (code quality plus repo rules) and Spec (`specs/NNN-*/` acceptance criteria). Report them separately.

## 3. Python correctness checklist (blocking categories)

Condensed from OCR `python.md`. Each item has a "don't report" exception, which matters as much as the item.

| Area | Flag | Don't flag |
|---|---|---|
| Mutable state | `def f(x=[])`; class-level mutable attributes; module-global caches mutated per request; closures capturing a loop variable late | The argument is never mutated; a documented cache or sentinel |
| Edge cases | `xs[0]`, `max()` on possibly-empty input; off-by-one; `None` from an upstream call that can return it; float `==`; `//` truncation, divide by zero; `d[k]` with a missing key | The type contract or upstream validation already rules it out |
| Exceptions | Bare `except:`; `except Exception` broader than what the call raises; swallowed exceptions; re-raise without `from err`; a `try` wrapping far more than the failing line; `assert` used to validate input (stripped by `-O`) | — |
| Identity | `is` against literals; `== True` | `== None` is a minor style issue, not blocking |
| Resources | `open`, socket, lock or connection without `with`; missing `finally`; generators holding resources open | Already inside a `with` or framework lifecycle |
| Async / concurrency | Blocking I/O, `time.sleep` or CPU work inside `async def`; `create_task` not awaited or not referenced (it may be garbage-collected); check-then-act races; CPU work in threads | No evidence the code runs concurrently |
| Performance (hot path only) | `+=` string building in loops; `in list` lookups in loops; regex compiled inside a loop; `log.info(f"...")` | Cold paths, small inputs |
| Security (attacker-controlled input only) | `eval`/`exec`; `shell=True` with interpolated input; `pickle`/`yaml.load` on untrusted data; SQL built with f-strings; secrets or PII in logs; `random` used for tokens; md5/sha1 for passwords; path traversal | Trusted constants |
| Dead code | Unreachable branches; unused parameters, variables or imports; commented-out blocks | `.pyi` stubs |

Additions for mint, which uses async SQLAlchemy, aiohttp and storage clients:
- `AsyncSession` shared across tasks.
- Session or UnitOfWork used outside its scope.
- `asyncio.gather` without `return_exceptions` handling where one failure leaks the others.
- Transaction commit and rollback on error paths.

## 4. Coding style: three layers, highest priority first

**Layer 1: tools enforce it, so the reviewer stays silent.** `ruff` with `select = ["ALL"]` at line-length 99, `ruff format`, mypy strict settings plus the pydantic plugin, and ty. That covers PEP 8, import order, docstring presence (D rules), annotations (ANN), naming (N), bandit rules (S), complexity (C901, PLR0912…), `datetime` timezone (DTZ), boolean positional arguments (FBT), exception messages (EM, TRY). The reviewer only flags **new suppressions**: `# noqa`, or `# type: ignore` without a code or not caused by a third-party gap (coding-style.md, "No suppression comments").

**Layer 2: repo rules that tools miss.** These are the point of the skill. Cite file and heading:

| Rule | Source | What to check in the diff |
|---|---|---|
| PEP 695 generics; type parameters named `T` or `KeyT`/`ValueT`, never `Item` | coding-style.md | `TypeVar` used without a third-party reason; `class X[Item]` |
| No `from __future__ import annotations` | coding-style.md | — |
| Guard clauses, fail fast | coding-style.md | Nested happy path |
| RORO: several parameters → one object; several return values → object, not tuple | coding-style.md | `return a, b, c` |
| Data-class tiers: BaseModel / pydantic dataclass / dataclass | coding-style.md | Wrong tier, e.g. BaseModel for a plain value holder |
| `isinstance`/`issubclass` instead of `hasattr`/`getattr(..., default)` | coding-style.md | Includes the Protocol caveat: `issubclass` fails on a Protocol that has data members |
| Never name a module after the stdlib | coding-style.md | `types.py`, `io.py` |
| `mp_<k>_<v>` for intermediate dicts | coding-style.md | — |
| Return new objects; no globals; explicit dependencies | coding-style.md | — |
| **OOP placement Case A/B** | oop.md | Free function whose first owned-class parameter makes it a method; zero-arg pure method that should be `@property`; a "dangling module" of `x_foo(foo)` functions; services own I/O through constructor injection |
| Exceptions: hierarchy per module; `TemplatedError` subclass with `TEMPLATE` and typed fields; never a pre-built `msg` variable; never bare `Exception`/`RuntimeError` | modular-design.md, `mint/exc.py` | — |
| models are pure; services do I/O; files 200–400 lines, hard cap 800 | modular-design.md | — |
| pytest only; `autospec=True`; parametrize with tuples; annotated fixtures with docstrings; mirrored test layout; 100% branch coverage | testing.md | — |
| Public API has a docstring with Args/Returns/Raises; README updated for new features | documentation.md | — |

**Layer 3: general Python idiom.** Non-blocking, `Nit:` only. Sources: [PEP 8](https://peps.python.org/pep-0008/), [PEP 20](https://peps.python.org/pep-0020/), [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html).
- Comprehension instead of map/filter+lambda, as long as it stays one readable line.
- `pathlib` over `os.path`.
- `enumerate`/`zip(strict=True)` instead of index loops.
- `match` for structural dispatch.
- `functools.cache` instead of a hand-rolled memo.
- `contextlib` instead of try/finally boilerplate.
- `Final`/`Literal`/`enum.StrEnum` instead of magic strings.
- `Protocol` instead of an ABC when only the shape matters.
- `@dataclass(slots=True, frozen=True)` for value objects.

## 5. Refactoring

**Rules for the reviewer:**
- Each smell is a labelled guess ("possible X"), never a hard violation.
- Repo rules override smells. Example: oop.md *requires* service classes, so a "Middle Man" smell on a thin service is suppressed.
- Suggest a refactoring only for code **in the diff**. Never "while you're here, refactor module Y".
- A refactor PR must not change behavior. Check that the tests still pass and were not edited to match the new code. Mixed refactor-plus-feature diffs: ask for them to be split.

**Smell → Python form → refactoring:**

| Smell | Python symptom | Move |
|---|---|---|
| Mysterious Name | `data`, `res`, `tmp`, `handle()`, `Manager` | Rename. If no honest name exists, the design is unclear. |
| Duplicated Code | Same shape in two hunks or files | Extract Function or Method; Pull Up Method |
| Long Function | More than ~1 screen; comment-headed "sections" | Extract Function; Replace Temp with Query (`@property`) |
| Long Parameter List | More than 3–4 parameters; boolean flags | Introduce Parameter Object (RORO, dataclass); Remove Flag Argument (split the function) |
| Data Clumps | `(bucket, key, region)` passed around together | Bundle into a frozen dataclass |
| Primitive Obsession | `str` for IDs, URLs, money; `dict[str, Any]` as a record | `NewType`, `StrEnum`, small dataclass or BaseModel |
| Feature Envy | Function reading `other.x`, `other.y`, `other.z` | Move Function onto `other` (this is oop.md Case A) |
| Repeated Switches | `if kind == "s3" … elif "azure"` in several places | Polymorphism through a Protocol, or one shared dispatch `dict` |
| Shotgun Surgery | One concept edited across many files | Move Function or Field so the things that change together sit together |
| Divergent Change | One module edited for unrelated reasons | Split Module |
| Speculative Generality | Unused parameter or hook, an ABC with one implementation, `**kwargs` passthrough "for later" | Inline Class or Function; Remove Parameter; delete it |
| Message Chains | `a.b.c.d()` | Hide Delegate |
| Middle Man | Class that only forwards | Remove Middle Man (unless oop.md requires it) |
| Refused Bequest | Subclass overriding or raising `NotImplementedError` on most inherited methods | Replace Inheritance with Delegation |
| Global Data / Mutable Data | Module-level mutable state | Encapsulate in a class, inject it; return new objects |
| Loops vs Pipeline | Accumulator loop | Replace Loop with Pipeline (comprehension or generator) |
| Dangling module (mint) | `serialize.py` full of `x_order(order)` | Fold into the class; **delete the module, no shim** |

## 6. Problems in mint's rules a skill must resolve

| Conflict | Evidence |
|---|---|
| Line length 100 vs 99 | coding-style.md "Max 100" vs `pyproject.toml:88` `line-length = 99`. Ruff wins in practice. |
| Coverage gate missing | testing.md says `--cov-fail-under=100` is in pyproject; it isn't. `[tool.pytest.ini_options]` has no addopts. |
| Python version mismatch | `requires-python = ">=3.13"` but `[tool.mypy] python_version = "3.12"`. |
| Type checker unclear | Rules say ty; pdm `tc` script runs mypy. Both are installed. |
| Rules copied from another project | modular-design.md shows a `stevard/` layout with typer `commands.py`; mint has no typer. |

The skill should report against what ruff and mypy actually enforce, and mention these mismatches once rather than per finding.

## 7. Draft `SKILL.md`

Suggested path: `.claude/skills/python-review/SKILL.md`

```markdown
---
name: python-review
description: Review Python changes in this repo (diff vs a base ref) for correctness, security, repo standards and refactoring smells. Use when asked to review a branch, PR, commit or working-tree changes in Python code.
---

# Python Review

## 1. Pin scope
- Base = user-given ref, else merge-base with `master`. Run `git rev-parse <base>`; stop on bad ref.
- Diff: `git diff <base>...HEAD -- '*.py' 'pyproject.toml'`; commits: `git log <base>..HEAD --oneline`. Stop if empty.
- Spec: issue refs in commits → `specs/NNN-*/` matching branch → ask. None → Spec axis "no spec".

## 2. Gates first (tool-enforced = never comment on it)
Run `uv run ruff check`, `uv run ruff format --check`, `uv run mypy .`, `uv run pytest --cov=mint --cov-branch`.
Report failures verbatim as one `high` finding each. Do not restate individual lint rules.

## 3. Optional machine pass
`ocr review --audience agent -b "<spec summary>" --from <base> --to HEAD --output /tmp/ocr.txt`; read file in full.
Treat each OCR finding as a lead: verify against code before keeping.

## 4. Standards axis (subagent A)
Review only `+` lines. Read callers/callees before calling anything a bug. Checklists, in order:
1. Correctness & security: references/python-correctness.md (mutable defaults, edge cases, exceptions,
   identity, resources, async, security, dead code — each with its don't-report clause).
2. Repo rules: .claude/rules/{coding-style,oop,modular-design,testing,documentation}.md.
   Cite `file#heading` for every violation. Flag new `# noqa` / bare `# type: ignore`.
3. Smells: references/smells.md. Always "possible <Smell>" + suggested refactoring.
   Repo rule overrides smell (oop.md service classes are not Middle Man).
4. Tests: each changed behavior has a test that fails without the change; parametrized boundaries;
   autospec mocks; no test edited only to match new output.

## 5. Spec axis (subagent B)
Missing/partial requirements; unrequested behavior (scope creep); implemented-but-wrong. Quote spec line.

## 6. Filter
Drop a finding only if the code proves it wrong. Drop `low` unless asked. Never drop for "low value".

## 7. Report
## Standards
**Files**: N · **Findings**: X critical, Y high, Z medium
### Critical / High / Medium
- **`path:line`** [category] — problem.
  > Fix: concrete change. (Rule: `.claude/rules/x.md#heading` | Smell: possible X)
## Spec
...
One line: count per axis + worst item per axis. Never rerank across axes.
Security/correctness = blocking; style/smell = `Nit:` non-blocking.

## 8. Fix (only if asked)
Fix critical/high/medium; rerun gates; never edit tests to make them pass.
```

Move sections 3 and 5 of this answer into `references/python-correctness.md` and `references/smells.md` next to the skill. That keeps `SKILL.md` short and loads the checklists only when a review runs.

I only read the source of alibaba OCR and mattpocock. Spencermarx's project I took from its README; Google's guide I took from memory and its link. I didn't check the Qodo PR-Agent or CodeRabbit prompts, and I didn't create the skill files. Fix the conflicts in section 6 before relying on the skill, or it will cite rules that disagree with the tools.

---

Every platform follows the same four steps: **pin the scope → gather context → review → filter and report**. They differ in how many reviewers run and how findings get checked.

## alibaba/open-code-review (`ocr`)
A fixed pipeline plus an LLM agent, run per group of files. Sources: their prompts in `internal/config/template/prompts/`.
1. **Pick the target.** Workspace (staged, unstaged and untracked changes), `--commit`, or `--from/--to`. The skill first gathers business context and passes it with `--background`.
2. **Group the files** (`grouping_task`). Related files are reviewed together, so a contract broken across files is caught.
3. **Plan.** This runs only when a file has ≥50 changed lines or a group has ≥100 (`plan_task`). It does a risk analysis before the main review.
4. **Main review** (`main_task`). The agent sees the unified diff and can call tools (`file_read`, search) for context. It reports with `code_comment` and must give each file its own pass, then calls `task_done`. Effort low/medium/high sets 1, 2 or 3 rounds.
5. **Rules per language.** `rule_docs/python.md` is injected based on file path. Rule priority: `--rule` > repo `.opencodereview/rule.json` > `~/.opencodereview` > built-in.
6. **Fix line positions** (`re_location_task`). Comments that drifted get remapped. A finding at line `0,0` means remapping failed.
7. **Filter** (`review_filter_task`). A fact-checker sees only the diff and removes a finding only if the diff **proves** it wrong.
8. **Output.** Text, JSON or SARIF. Each finding has severity and category, and may include `suggestion_code`. Large contexts are compressed (`memory_compression_task`) and runs have token budgets.

Techniques:
- Precision over recall.
- Only added lines are reviewed.
- Every "flag X" rule has a matching "don't flag when Y".
- Confirmation is required through tools.

## spencermarx/open-code-review
A multi-agent team that discusses findings. Source: README only.
1. **Discover context.** It reads `CLAUDE.md`, `.cursorrules`, OpenSpec files, and the requirements or spec you pass in.
2. **Review map** (optional for large changes). The change is split into sections, with a Mermaid dependency graph to set the reading order.
3. **Parallel reviewers.** Several personas (generalists, specialists, "Fowler/Beck/Metz") review the same code independently. Running more than one instance is intentional: each one notices different things.
4. **Discourse.** Reviewers challenge and confirm each other's findings.
5. **Synthesis.** A "tech lead" agent dedupes, ranks and gives a verdict.
6. **Triage and post.** Findings can be marked addressed or dismissed in a dashboard. They post to GitHub as-is, or rewritten into one human voice following Google's guidelines. Later review rounds can address earlier feedback.

Techniques:
- Several reviewers for coverage.
- Debate to remove false positives.
- Personas focus each reviewer's attention.

## mattpocock/skills `code-review`
Two separate checks, run as subagents. I read the full SKILL.md.
1. **Fix the base ref.** Confirm it with `git rev-parse` and fail early if the diff is empty. Use `git diff base...HEAD`.
2. **Find the spec.** Order: issue refs in commits, then an argument, then `docs/`, `specs/` or `.scratch/`, then ask the user.
3. **Find the standards.** `CODING_STANDARDS.md` and `CONTRIBUTING.md`, plus a baseline of 12 Fowler smells.
4. **Run two subagents in parallel, each with a fresh context:**
   - Standards: rule violations (citing the rule) plus possible smells.
   - Spec: missing requirements, scope creep, and requirements implemented wrongly.
   - Each report is capped at 400 words.
5. **Combine.** Report the two side by side, without merging or reranking. Name the worst issue per check.

Techniques:
- Separate contexts so one check can't hide the other.
- Repo rules override smells.
- Smells are judgement calls.
- Skip anything tooling already enforces.

## Google eng-practices
The human method that the AI tools borrow.
1. **Look at the whole change.** Does it make sense at all? Is the description adequate?
2. **Read the main part first.** Find the file or files carrying the logical core and review the design there before details.
3. **Read the rest in a sensible order.**
4. **Check these areas in order:** design, functionality (edge cases, concurrency), complexity (over-engineering), tests, naming, comments (why, not what), style, docs.
5. **Write comments.** Be courteous and explain why. Label severity with `Nit:`, `Optional:`, `FYI:`.

Standard: approve once the change clearly improves overall code health, not when it's perfect.

## Summary across platforms

| Technique | OCR-alibaba | OCR-spencermarx | mattpocock | Google |
|---|---|---|---|---|
| Diff-only scope | ✔ | ✔ | ✔ (merge-base) | ✔ |
| Read context with tools before flagging | ✔ | ✔ | — | human |
| Language and repo rules | ✔ rule.json | ✔ CLAUDE.md | ✔ standards files | style guide |
| Check against spec or requirements | via background | ✔ | ✔ separate check | CL description |
| Multiple reviewers | — | ✔ personas | ✔ 2 checks | — |
| False-positive check | filter pass | discourse | — | — |
| Severity taxonomy | 4 levels × 8 categories | ranked synthesis | hard vs judgement | Nit/Optional/FYI |
| Fix line positions | ✔ | — | — | — |

The draft skill from my last reply already uses: OCR's rules, filter and taxonomy; mattpocock's two-check split; and Google's review order. I left out spencermarx's personas and debate step. That step costs about 3–5× the tokens; add it only if false positives are still a problem after the filter pass.

I read the source of alibaba OCR and mattpocock. Spencermarx's workflow comes from its README only, and Google's from memory of the guide.

---

Lauren Tan (poteto, Cursor) publishes her review skills in **pstack**. I read three of them in the port `michael-denyer/pstack-claude`, under `plugins/pstack/skills/`. I couldn't find an upstream `poteto/pstack` repo through `gh`.

Her approach splits the work into two separate reviews: one for correctness and security, one for structure. The structural review is the more aggressive one. It treats "works but messy" as grounds to block.

## 1. `thermo-nuclear-review`: correctness and security audit
This is a single prompt with no fixed pipeline. Steps:
1. **Scope.** Only code added or modified in the branch. Never existing code that wasn't touched.
2. **Trace side effects across modules.** Small changes often break things elsewhere through cross-package dependencies.
3. **Check four risk classes:**
   - bugs
   - broken existing features
   - security problems
   - **devex breaks**: renamed env vars, how secrets are read, port remapping, new required scripts. A new dependency doesn't count.
   - **feature-gate leaks**: code meant to sit behind a flag or internal check that escapes it.
4. **Skip intended breakage.** If the PR deliberately removes a safeguard and the scope is narrow, don't report it. Still report it if the author seems to underestimate the impact, or the change looks malicious ("Delete the database").
5. **Finish the research before reporting.** Never write "X is a problem unless the backend handles it" when you can read the backend yourself.
6. **Read the PR discussion afterwards** (`gh`). Only after the audit, so the first read is unbiased. Merge in valid findings from review bots and credit them.

Calibration: overstating priority costs trust, so trace each issue end to end before calling it High.

## 2. `thermo-nuclear-code-quality-review`: structural review
Steps:
1. Audit the branch diff. Base prompt: "rethink how to structure the change… without impacting behavior."
2. **Look for a "code judo" move.** That means a restructuring that makes whole branches, modes, helpers or layers *disappear*, not one that just rearranges them.
3. Ask the 13 primary questions for every meaningful change, for example:
   - Is the logic in the right layer?
   - Do repeated conditionals point to a missing model?
   - Does this abstraction earn its place?
   - Does a cast or optional value hide the real invariant?
   - Is the flow more sequential or less atomic than it needs to be?
4. **Treat these as presumptive blockers:**
   - a file pushed from under 1k lines to over 1k
   - ad-hoc `if`s scattered into unrelated flows ("spaghetti growth")
   - feature checks spread across shared code
   - thin or identity wrappers
   - cast-heavy or optional-heavy contracts
   - duplicating an existing helper
   - logic in the wrong layer
   - keeping incidental complexity when a code-judo simplification is visible
5. **Rank output by importance:** structural regressions → missed simplifications → added branching complexity → boundary and type problems → file size → modularity → legibility. Prefer a few high-conviction findings over many nits. No "rename this" when the real problem is structural.
6. **Report in layers.** Write to `/tmp/<project>-thermo/`:
   - a summary of about 200 lines: verdict, each finding as a prose paragraph, a fix sequence
   - detail files `01_<subsystem>.md` and so on, with measurements, the commands run, and worked code-judo proposals
   - with parallel reviewers (via her **swarm** skill), each reviewer's report becomes a detail file

Approval bar: "do not approve merely because behavior seems correct." Tone is direct and not softened. Example: `this adds another special-case branch into an already busy flow. can we move this behind its own abstraction?`

## 3. `make-pr-easy-to-review`: author side, before review
1. Resolve the PR and inspect commits, diff size, generated files and description.
2. Find what makes the PR hard to review: noisy commits, mechanical and logic changes mixed together, a stale description, unclear entry point.
3. **Propose a plan before rewriting history.**
4. Regroup commits in dependency order: schema → core logic → wiring → UI → tests.
5. **Check the content is unchanged:** `git rev-parse HEAD^{tree}` must equal the original tree. Never push if it differs.
6. Write a TL;DR plus notes on which files are core vs mechanical, risky changes, migration order and test coverage. If the PR is too big, recommend splitting it rather than polishing around it.

## Compared with the other platforms

| | alibaba OCR | mattpocock | **poteto pstack** |
|---|---|---|---|
| How findings are filtered | Precision filter pass | Repo rules override smells | Trace end to end; calibrate priority |
| Structure / refactoring | Maintainability category | 12 Fowler smells, as judgement calls | **Code judo, presumptive blockers**: most aggressive |
| Unique checks | Fixes drifted line positions | Separate Spec check | Devex breaks, feature-gate leaks, intended breakage, PR discussion read afterwards |
| Size rule | — | — | File crossing 1k lines (mint's own rule caps files at 800) |
| Output | Severity list | Two reports side by side | Prose summary plus detail files on disk |

## What to add to the mint Python skill
- **Gate-leak and devex checks.** Mint has optional extras (`db`, `orm`) and dependency groups (`s3`, `azure`). A core import that reaches an optional extra is the Python version of a feature leak.
- **Spaghetti growth and file crossing 800 lines** as presumptive blockers in the structural check, using mint's 800-line cap.
- **Rule: research finished before reporting.**
- **Read the PR discussion after the audit,** then merge in bot findings with credit.
- Skip her pushy "be ambitious, restructure the codebase" stance in the default mode. It conflicts with diff-only scope; make it an opt-in "deep" mode instead.

I didn't read pstack's `reflect` reviewers (divergent, judgment, tooling). They review the agent's own work, not code changes.