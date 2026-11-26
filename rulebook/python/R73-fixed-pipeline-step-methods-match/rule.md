---
id: R73
title: A fixed pipeline of named steps is step methods driven by one match, not a loop over a registry
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/enum.html#enum.StrEnum, https://docs.python.org/3/howto/enum.html#when-to-use-new-vs-init, https://peps.python.org/pep-0634/, Fowler Refactoring "Replace Loop with Pipeline" / "Replace Conditional with Polymorphism", owner convention
---
## Rule

- A closed, named step sequence (a fixed pipeline) is implemented as one method per step. (C1)
- A single driver `match`es on the step enum to run the steps. (C2)
- Per-step variation (refresh flags, the next step) folds into the match arms. (C3)
- No marker decorators on step methods. (C4)
- No attribute attachment (setting metadata attributes on functions or methods). (C5)
- No `type: ignore` in the pipeline. (C6)
- A loop over a registry of steps (a module-level step list or table, a string-dispatched step runner) is a violation. (C7)
- Resume-by-cursor compares on the step's order attribute. (C8)
- Persisted steps keep a readable string in code and in the database via the ordered `StrEnum` pattern: the member value is the stored string. (C9)
- An explicit `order: int` rides on each member through a custom `__new__`. (C10)
- Comparisons and the next-step computation use `.order`. (C11)
- `StrEnum` members are never compared with `<` / `>` directly (that compares lexicographically). (C12)
- `IntEnum` steps with name/value converter methods used at database boundaries are prohibited. (C13)
- Persisting progress and renewing a lease live in the one driver, not repeated per step. (C14)
- The stored string is parsed into the enum at the read boundary (`Stage(row["stage"])`) and the member is written at the write boundary. (C15)

## Incorrect

- `if current > Stage.LABEL:` on a `StrEnum` (lexicographic comparison).
- An `IntEnum` with `label()` / `parse()` methods converting members to and from their names for storage.
- `PIPELINE = (measure, label, load)` with `for stage_fn in PIPELINE:`.
- `HANDLERS = {"measure": measure, ...}` with `HANDLERS[name](parcel)`.
- A `needs_refresh` marker decorator setting `fn.refresh = True`, and `load.refresh = True` attached at module level.
- (LLM) Each step function saving progress to the database itself, and a `# type: ignore` inside the pipeline.

## Correct

- `class Stage(StrEnum)` with `MEASURE = "measure", 1` etc., a `__new__(cls, value, order)` setting `order`, a `next` property from `.order`, and one `run_stage` driver that `match`es `Stage` members, sets the refresh flag per arm, and persists once.
- Look-alikes: comparing `stage.order < other.order`, a loop over a module-level tuple of strings, an `IntEnum` whose only name use is a display-only `__str__`, and a CLI subcommand table `COMMANDS[args.cmd](args)` that is never iterated.

## Detection

Reports: `<`, `>`, `<=`, `>=` comparisons with an operand `Enum.MEMBER` of a `StrEnum` (or `str, Enum`) class from the scanned modules (C12, literal-member subset); non-dunder methods of an `IntEnum` (or `int, Enum`) class that read `.name`, index `cls[...]` or read `__members__` (name/value converters, C13); `for` loops over, and `.items()`/`.values()` iteration of, a module-level tuple, list or dict holding two or more module-level functions, plus `REGISTRY[key](...)` calls through such a dict when the same dict is also iterated, which marks it as a pipeline rather than a lookup table (C7); attribute assignment on a module-level function (C5); and attribute assignment on a parameter inside a function used as a decorator in the same module (marker decorators, C4/C5).

## LLM scan

- Check the pipeline shape: one method per step (C1), one driver matching the step enum (C2) with per-step variation in the arms (C3), and resume-by-cursor on `.order` (C8, C11).
- Check persisted steps use the ordered `StrEnum` pattern: stored string as value, `order: int` set in `__new__` (C9, C10), parsed at the read boundary and written as the member (C15).
- Flag `type: ignore` inside pipeline code (C6) and progress persistence or lease renewal repeated in each step instead of the driver (C14).
- Flag string-dispatched step runners the detector misses (e.g. `getattr`-based or `if name == ...` chains) (C7).
- Flag `<`/`>`/`<=`/`>=` between two `StrEnum`-typed variables or attributes (e.g. `current > target` where both are steps), which the detector only catches when one side is a literal `Step.MEMBER` (C12).
- Flag string-keyed dispatch through a step table that is never iterated (`HANDLERS[name](job)`) when the table is a closed pipeline of steps; do not flag CLI subcommand or plugin tables (C7).
- Do not flag open-ended plugin registries whose members are not a closed, named sequence.
