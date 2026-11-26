---
id: OOP-02
title: Type switch on isinstance
tier: semgrep
severity: should-fix
---
Pattern: an `if/elif` chain that branches on `isinstance` of the same value to pick behaviour.
Move the behaviour into the types (polymorphism), or use `functools.singledispatch` / `match` with class patterns.

× `if isinstance(s, Circle): area = ... elif isinstance(s, Square): area = ...`
✓ `area = s.area()` with `area()` defined on each shape
