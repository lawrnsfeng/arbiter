---
id: R38
title: A module-level static lands in one of three homes
tier: ast+semantic
severity: should-fix
status: ok
refs: https://peps.python.org/pep-0008/#constants, https://peps.python.org/pep-0435/, https://refactoring.com/catalog/moveField.html
---
## Rule

- A static shared across modules lives in the package's constants module (`<pkg>/constants.py`). (C1)
- A static read by exactly one class is that class's attribute (see R36). (C2)
- A fixed set of strings sharing one meaning is a string enum (`StrEnum` / `str, Enum`; see R23). (C3)
- Within the constants module, constants are grouped into category classes, read as `Category.NAME`. (C4)
- A flat wall of prefix-named module-level constants (`LOAN_*`, `FINE_*`) in the constants module is the regression. (C5)
- Statics shared by two or more classes of one subsystem gather in that subsystem's constants module
  (`<pkg>/<subsystem>/constants.py`). (C6)
- Exception: enums and truly cross-cutting scalars (a loopback host, a source-control remote) stay module-level, not
  inside a category class. (C7)

## Incorrect

- `LOAN_*` and `FINE_*` constants flat in the constants module.
- A set of collection-kind strings as loose constants instead of an enum (model only).

## Correct

- `class Loan:` and `class Fine:` category classes, a `StrEnum` for the collection kinds.
- Look-alikes: cross-cutting scalars stay module-level and are not reported, both with distinct prefixes and as a pair
  sharing one (`PAGE_SIZE`, `PAGE_MAX`).

## Detection

In a constants module (a file named `constants.py`, or one holding only imports, constants and data-only classes),
reports every module-level `PREFIX_NAME` constant whose first underscore-separated word is shared by at least three
module-level constants (C4, C5). Cross-cutting scalars (C7) are not reported when their prefix is their own or shared
by only two of them, such as a page size and a page maximum; three or more scalars sharing a prefix are reported as a
wall even when they are cross-cutting, and the model decides those against C7.

## LLM scan

- Flag statics defined in one module but imported by several that are not in the constants module (C1), and statics
  in the shared constants module read by only one class (C2) or only by classes of one subsystem (C6).
- Flag groups of string constants that enumerate one concept (kinds, states, modes) instead of a string enum (C3).
- Judge every pair of module-level constants sharing a prefix in the constants module (the detector skips pairs): flag
  the pair when it belongs to one category and starts a flat wall (C4, C5); leave it when both are cross-cutting
  scalars every subsystem uses (C7).
- Flag cross-cutting scalars or enums that were pushed into a category class (C7).
- Do not flag a single constant per prefix, enums, or scalars every subsystem uses.
