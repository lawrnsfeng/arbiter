---
id: R24
title: Private helpers get a docstring like public ones
tier: ast
severity: should-fix
status: ok
refs: PEP 257, Ruff docs: D102 undocumented-public-method / D103 undocumented-public-function, Google Python Style Guide 3.8.3 Functions and Methods
---
## Rule

- Every private (`_`-prefixed) function gets a docstring of at least one line. (C1)
- Every private (`_`-prefixed) method gets a docstring of at least one line. (C2)
- The rule is self-enforced because the docstring linters (ruff `D102` / `D103`, pydocstyle) skip `_`-prefixed names by design; this detector closes that gap. (C3)

## Incorrect

- Module-level `_to_celsius(f)` with no docstring.
- A `_bucket(self)` method and an `async def _poll(self)` method with no docstring.
- A private helper with only a comment where the docstring belongs, and one with an empty `""""""` docstring.

## Correct

- The same helpers each with a one-line docstring.
- Look-alikes: a public function without a docstring (other linters' business), a dunder method such as
  `__repr__`, and an `@overload` stub.

## Detection

`check.py` reports every `def` / `async def`, at any nesting depth, whose name starts with `_` but is not a dunder
(`__x__`), that is not decorated `@overload`, and whose docstring is missing or blank. Covers C1 and C2; C3 is the
reason the detector exists.
