---
id: R36
title: Constants used by exactly one class are attributes of that class
tier: ast
severity: should-fix
status: ok
refs: https://refactoring.com/catalog/moveField.html, https://peps.python.org/pep-0008/#constants
---
## Rule

- A module-level constant used by exactly one class is declared as a class attribute of that class instead. (C1)
- Class-scoped constants carry no leading underscore: the class is the namespace. (C2)

## Incorrect

- A private module constant read only inside one class's method.
- A public module constant read only inside one class.
- A class attribute constant with a leading underscore.

## Correct

- The constant declared inside the class, without underscore.
- Look-alikes: a constant read by two classes, one read by a class and a module function, one read only at module
  level, one used in a class decorator, a name imported from another module, and a cached adapter built from the
  class that reads it.

## Detection

Reports a module-level `UPPER_CASE` constant (with or without leading underscore) whose every read in its module sits
inside the body of one top-level class (bases and decorators excluded), with at least one read, and whose name no
other scanned module imports or accesses as an attribute (C1). A constant whose value names the class that reads it
(e.g. a module-level `TypeAdapter(TheClass)` cache) is skipped, since it cannot be built inside that class. Reports
every `_UPPER_CASE` constant assigned in a class body (C2).
