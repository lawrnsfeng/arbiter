---
id: R54
title: A helper needed by two or more subsystems lives in the package's utils
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog (Move Function, Extract Function), The Pragmatic Programmer (DRY)
---
## Rule

- A helper used by two or more subsystems of a package lives in `<pkg>/utils/`. (C1)
- It does not stay in the subsystem that wrote it first. (C2)
- It is never copied or duplicated, for example the same helper in two classes. (C3)
- Shared helpers are not loose top-level modules of the package (such as `<pkg>/disk.py`); they go under `<pkg>/utils/`. (C4)
- `<pkg>/utils/` modules import only the stdlib, `<pkg>.errors`, and `<pkg>.messages`, never a subsystem. (C5)

## Incorrect

- One subsystem importing a helper from another subsystem's module (model only).
- The same method body in two view classes.
- The same body copied into a renamed module-level function.

## Correct

- Both views call one helper imported from `<pkg>/utils/`.
- Small identical bodies (`self.title = title`, `return self.title`) that are idioms, not helpers.

## Detection

Covers C3 and the subsystem part of C5. C3: every function or method whose body (docstring aside) is structurally
identical to an earlier one in the scanned modules and has at least 20 syntax nodes; one hit per later copy, naming the
first. C5: in a module under `<pkg>/utils/` (where `<pkg>` has an `__init__.py` and is not inside another package), every
import, absolute or relative, of `<pkg>.<name>` where `<name>` is not `errors`, `messages` or `utils`.

## LLM scan

Beyond the detector: find helpers (small, domain-neutral functions or classes: formatting, time, disk, text, retry)
defined inside one subsystem and imported by another subsystem, and report the definition (C1, C2). Report shared
helpers placed as loose top-level modules of the package instead of under `<pkg>/utils/` (C4). Report copies the
detector misses: the same logic with renamed variables or small edits in two places (C3). Report third-party imports
in `<pkg>/utils/` modules (C5 allows only the stdlib, `<pkg>.errors` and `<pkg>.messages`). Do not flag a subsystem's
public API that other subsystems are meant to call (services, models, serializers), the package's `errors`/`messages`/
`constants` modules, or code used by a single subsystem.
