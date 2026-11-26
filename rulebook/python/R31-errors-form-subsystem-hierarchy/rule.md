---
id: R31
title: Project errors form a subsystem hierarchy under one root error
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions, Effective Python 2nd ed. Item 87 (Define a Root Exception to Insulate Callers from APIs)
---
## Rule

- Every error the project defines sits in one hierarchy under the package's root error class. (C1)
- A concrete error of a subsystem never subclasses the root error directly when that subsystem has a base error; it subclasses the subsystem base. (C2)
- Subsystem errors live in their subpackage's errors module (`<pkg>/<subsystem>/errors.py`). (C3)
- Cross-cutting errors (not owned by one subsystem) stay direct children of the root error, in the package's top-level errors module (`<pkg>/errors.py`). (C4)

## Incorrect

- A courier error subclasses the root error although a courier base error exists.
- A scanner error does the same with a second subsystem base.
- A label-printer error hangs off the root while the printer subsystem has no base error yet (model only).
- A project error subclasses `Exception` directly, outside the hierarchy (model only).

## Correct

- Root error, subsystem bases, concrete errors under their subsystem base.
- A cross-cutting error as a direct child of the root.
- A look-alike whose name merely starts with a base's prefix inside a longer word (`Courierless…`) stays silent.

## Detection

Reports a class whose base is a project-defined `…Error` class (the root) when a sibling class `<Prefix>Error` with the
same root has subclasses of its own (a subsystem base) and the reported class's name starts with `<Prefix>` followed
by an uppercase letter (C2, for subsystems named by prefix). Bases are matched by name across all scanned modules.

## LLM scan

- Flag project error classes that subclass `Exception`/`BaseException` (or a third-party error) instead of the
  project's root error (C1).
- Flag a concrete error that belongs to a subsystem whose base is named differently from the concrete error, or a
  subsystem with several concrete errors on the root and no base yet; the fix is to add or use the subsystem base (C2).
- Flag subsystem errors defined outside their subpackage's errors module, and cross-cutting errors defined outside
  the top-level errors module or under a subsystem base (C3, C4).
- Do not flag a cross-cutting error (configuration, I/O shared by every subsystem) that is a direct child of the root.
