---
id: R7
title: Functions sharing a project-class parameter become methods of that class
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog "Combine Functions into Class" (https://refactoring.com/catalog/combineFunctionsIntoClass.html), Fowler Refactoring catalog "Move Function" (https://refactoring.com/catalog/moveFunction.html), Fowler Refactoring catalog "Extract Class" (https://refactoring.com/catalog/extractClass.html)
---
## Rule

- If every function in a module takes the same parameter typed with a project-owned class, they become methods of
  that class and the parameter becomes `self`. (C1)
- Likewise if every method on a class takes the same parameter typed with a project-owned class. (C2)
- The parameter's position in the signature does not matter. (C3)
- The rule applies recursively: after extracting the class, re-check its methods for a second repeated parameter;
  that parameter becomes another class one layer deeper. (C4)

## Incorrect

- Every function of a module taking `station: Station`, at the first, second or only position (a `test_*` function in
  the same module, taking the fixture, stays silent).
- Every method of a recorder class taking `sensor: Sensor`.
- After extraction, every method of an archive class still taking the same `folder: Path` (model only).

## Correct

- `Station` owning `calibrate`, `export_csv` and `last_reading`; `Sensor` owning `record` and `reset`; an
  `ArchiveFolder(folder)` class owning `store` and `prune`.
- Look-alikes: module functions that take different project classes, a class where only some methods take the shared
  parameter, parameters typed with builtin or stdlib types.

## Detection

`check.py` treats a class as project-owned when a class of that name is defined in the scanned modules and the module
does not import that name from an outside package. Test modules (`test_*.py`, `*_test.py`, `conftest.py`) and
`test_*` functions are skipped: tests receive fixtures by parameter. It reports each function when a module has two or
more remaining module-level functions and every one of them has a parameter, at any position, annotated with the same
project-owned class
(`Name`, `"Name"`, or `Name | None`) (C1, C3), and each method when a class has two or more non-dunder, non-static
methods whose names no other scanned class defines (a shared name is an overridden or framework contract) and every
one of them has such a shared parameter besides `self` / `cls` (C2, C3, C4 for project-owned types).

## LLM scan

- After the detector's pass, check each class for a second parameter repeated across all or nearly all of its methods
  whose type is not yet a project class (a `Path`, an id, a connection); report it as the next class to extract one
  layer deeper (C4).
- Report modules or classes where nearly every function shares such a parameter and the exceptions are incidental
  (C1, C2).
- Do not flag framework callbacks or hooks whose signature is fixed by the framework, test functions receiving
  fixtures, or functions that merely accept a project object among many unrelated ones.
