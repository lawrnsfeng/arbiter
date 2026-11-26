---
id: R16
title: No get_/set_ prefixes; use a property, a noun accessor or a verb for the action
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 8 (Designing for Inheritance: plain attributes over accessor/mutator methods), Google Python Style Guide 3.15 Getters and Setters, Python docs built-in property, Fowler: Rename Function
---
## Rule

- Do not name a function or method with a `get_` prefix. (C1)
- Do not name a function or method with a `set_` prefix. (C2)
- Instead use a property (with a setter where writing is needed), a verb naming the actual action (e.g. `.save()`, `.reserve()`), or a noun-named accessor (e.g. `store.holder(isbn)`). (C3)

## Incorrect

- Module-level `get_units()` / `set_units(system)` pair over a `global` setting.
- `get_code()` method returning one attribute.
- `set_offset(sensor, delta)` / `get_offset(sensor)` pair over a calibration dict.
- `get_peak_gust(readings)` that computes a result: still a `get_` name (model only).

## Correct

- The unit system becomes a `Units` enum passed to the station; `code` is a property.
- `calibrate(sensor, delta)` names the action; `offset(sensor)` is a noun accessor; `peak_gust(readings)`.
- Look-alikes: `reset_offsets`, `budget_minutes`, `asset_tag` (the prefix is not `get_`/`set_`), and a
  `get_queryset` hook on a class with a third-party base.

## Detection

`check.py` reports the definite accessor subset of C1/C2, one hit per definition:

- a `get_*` function or method whose body (docstring and `global` aside) is a single `return` of a stored value: an
  attribute/subscript chain rooted at `self`/`cls`, or at a module-level name (optionally ending in `.get(...)`);
- a `set_*` function or method whose body is a single assignment to such a stored value (`self.x = …`,
  `_REGISTRY[key] = …`, or a name declared `global`).

Methods are reported only when every base class of their class is defined in the scanned code (or is `object`,
`ABC`, `Protocol`, `Generic`): a method of a class with a third-party base may be a framework hook the name is forced
by. Decorated definitions are skipped for the same reason.

## LLM scan

Look at every other `get_`/`set_`-prefixed function or method the detector did not report: ones that compute,
query, fetch or mutate. Flag each (C1/C2) and propose the replacement per C3: a property for a cheap read of state, a
noun for a lookup (`holder(isbn)`), a verb for work (`fetch_…` is still a prefix smell: name the action, e.g.
`download`, `reserve`, `save`). Do not flag a name the code must keep because it overrides a third-party hook (e.g.
a framework's `get_queryset`), implements a protocol defined outside the project, or is part of a published API
that cannot be renamed; say why when you skip one.
