---
name: python-refactor
description: Clean-code refactorer for Python that applies the owner's rulebook (rulebook/python, R1-R89 - OOP, design patterns, maintainability) to code and performs the refactors itself, behaviour-preserving, tests green before and after, uncommitted in the working tree. Scope defaults to the current uncommitted changes; extends to a feature branch or the whole codebase. Use on demand ("refactor", "clean up this code", "apply the rulebook") or when an arbiter review report says "Refactor needed". Not for functional review or bug fixes.
argument-hint: "[--scope changes|branch|all] [--base REF] [--only R1,R46,...] [PATH...]"
---

# python-refactor

Review (arbiter-review / python-review) owns behaviour and feature quality; this skill owns clean code. It finds every
rulebook violation in scope with the deterministic detectors plus a model pass for what they cannot decide, then fixes
each one without changing behaviour.

## 0. Locate the rulebook

`RB` = the `rulebook/` directory of the arbiter checkout, the first that exists of: the path the task names; two
levels above this skill's real path (`dirname "$(dirname "$(readlink -f <this skill's directory>)")"`/rulebook);
`${CLAUDE_PLUGIN_ROOT}/rulebook` under Claude Code. It holds `scan.py`, `README.md` and `python/R*/rule.md` with
`bad.py` / `good.py` examples. Run its scripts with `python3` (stdlib only, Python ≥ 3.12). Never edit `RB`.
`RUN=$(mktemp -d)` holds the scan JSON, snapshots and any equivalence harness, outside the repo.

## 1. Scope

| `--scope` | Code in scope | `scan.py` arguments |
|---|---|---|
| `changes` (default) | uncommitted changes: working tree vs `HEAD`, untracked files included | `--diff HEAD <repo root>` |
| `branch` | the whole feature branch: working tree vs `git merge-base <base> HEAD` (`--base`, default the remote default branch) | `--diff <merge-base sha> <repo root>` |
| `all` | every `*.py` under the PATHs (default: repo root) | `<PATH...>` |

A review handoff passes `--scope branch --base <sha>`. Test files in scope are refactor targets like any other code
(see §4.2 for what may change in them). Exclude vendored, generated and migration code from fixes (report it, do not
edit it). `--only` limits the ledger to the listed rule ids; it is never passed to `scan.py`, whose own `--rules` is
the rules directory.

## 2. Baseline (stop if it fails)

1. `git status --porcelain`: record every file already modified; the owner's uncommitted work is never reverted,
   reformatted or staged by you.
2. Test command: the one the task gives, else the project's (Makefile, `pyproject.toml`, `tox.ini`, CI config,
   README). Lint/type commands the same way; if the project has none, skip them and say so under "What was not
   checked". No test command at all: stop and report it. Run the tests covering the files in scope (else the whole
   suite) and record the result. A red baseline: stop and report it; never refactor on red.
3. Every branch you will restructure must be reached by a test. Where none reaches it, add a characterization test
   that pins today's observable output, odd cases included (run it green, keep it), or, when a test would have to
   live outside the repo's conventions, an equivalence harness in `$RUN` that compares the snapshot with the
   refactored code over the same inputs.

## 3. Find

1. `python3 "$RB/scan.py" --json "$RUN/scan.json" <args from §1>`; exit 2 means a detector error or unparsable file:
   list them, continue with the rest. In `scan.json`, `changed` maps each changed file to its changed line spans; an
   untracked file is one span `[1, 9223372036854775807]` (the whole file).
2. Ledger: one row per rule R1–R89 (filtered by `--only`), never skipped. Detector hits are definite candidates with
   `path:line`.
3. Model pass over the code in scope (the `changed` spans, read as whole enclosing functions and classes):
   - every rule whose tier contains `semantic` (`llm` field): read `## Rule` and `## LLM scan` of its `rule.md`;
   - every `ast`-tier rule: read `## Rule`; a violation its detector missed is ledgered `model-found` and fixed like
     any other, and the detector gap is listed under "What was not checked".
   Open a rule's `bad.py` / `good.py` only when it has a candidate in scope. Work in batches of at most 10 rules so
   none is skimmed. Record each violation with `path:line` and the clause id.
4. Check every candidate against the rule text and `good.py` look-alikes; drop false hits with the reason in the
   ledger.

## 4. Fix, one rule at a time

Order: structural moves (new classes, modules, hierarchies) before local edits. When fixing one rule creates or
settles another rule's candidate (a new enum → a `match` → its fallback), fix them in that dependency order and ledger
each one. For each confirmed violation:

1. Snapshot the files you will touch (`cp` to `$RUN/snap/`); for a file the owner had already modified the snapshot
   is the only way back, so never use `git checkout` / `git restore` / `git stash` on it.
2. Apply the rule's correct form (`## Correct`, `good.py`), the smallest change that satisfies every clause. Update
   every caller, import and fixture the change reaches. Tests are callers: their call sites, imports and local style
   may change mechanically to the new API, but what an assertion checks never changes. A fix that would change an
   assertion's expected value or type (a dict becoming a dataclass under `assert x == {...}`) is `needs-owner`.
3. Run the tests from §2, plus lint/type checks when the project has them.
   - Green, and `scan.py` no longer reports the hit and reports no new hit: keep it, ledger `fixed`.
   - A new hit you refute with a clause (two rules conflict, or a detector is wrong): keep the fix, ledger the hit as
     a false positive naming the refuting clause, and list it under "What was not checked" as a rulebook defect.
   - Red: restore the snapshot, ledger `reverted` with the failing test. Never weaken, skip or delete a test to pass.
   - The fix needs a decision the rule does not settle (public API break, changed assertion, data migration,
     cross-team module, a name only the owner knows): do not apply it; ledger `needs-owner` with the question.

Never commit, stage or push. Never change behaviour: output, errors raised, I/O and public signatures stay as they
were unless every caller is updated within the rules above.

## 5. Verify and report

1. Rerun §3.1 on the same scope and the full test command from §2: both must hold (no hit the ledger calls `fixed`,
   tests green).
2. Outcomes: `fixed`, `model-found` (fixed, detector missed it), `reverted`, `needs-owner`, `clean` (the rule's subject
   occurs in scope and complies), `n/a` (the subject does not occur in scope). A row whose clauses split takes the
   worst outcome (`needs-owner` > `reverted` > `fixed`); its note lists each clause's outcome.
3. Report, in this order:
   - `Refactor: <scope> · <n> fixed · <n> model-found · <n> reverted · <n> needs-owner · <n> clean · <n> n/a` and the
     test command with its before/after result.
   - Ledger table, one row per rule: `id | title | outcome | path:line (where applicable) | note`.
   - The `needs-owner` questions, numbered.
   - Files changed (`git diff --stat` limited to files you touched) and any characterization tests added.
   - What was not checked: detector errors, unparsable files, excluded paths, skipped lint/type checks, detector gaps
     and refuted detector hits.
