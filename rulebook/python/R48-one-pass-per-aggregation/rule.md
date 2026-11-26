---
id: R48
title: One pass over a sequence per aggregation, not one pass per counter
tier: ast
severity: should-fix
status: ok
refs: Python docs collections.Counter
---
## Rule

- Computing several counts or sums over the same sequence uses one pass (one loop or one `Counter`), not one pass per counter such as one `sum(...)` generator each. (C1)

## Incorrect

- Three `sum(...)` generators over the same list for three counters.
- Two `len([...])` filtered list comprehensions over the same attribute.
- Two `.count(value)` calls on the same list.
- Two `sum(...)` passes over the same per-item sequence inside a loop body.

## Correct

- One `for` loop updating every counter.
- One `Counter(...)` over the sequence.
- Sums over two different sequences.
- A lambda with its own single pass (scopes are separate).
- Zero-argument `.count()` calls (query counts, not passes).
- Sums in mutually exclusive branches (`if`/`else`, or after an early `return`): only one runs.

## Detection

Covers C1. Within one function scope (nested functions and classes excluded), every call of the forms
`sum(<comprehension>)`, `len(<comprehension>)` (keyed by the first `for` clause's iterable) and `S.count(v)` with one
argument (keyed by `S`), when two or more such calls share the same key and can run on the same path; one hit per
such call. Calls in mutually exclusive branches (`if`/`else` arms, `match` arms, conditional-expression arms, and the
code after an `if` whose body ends in `return`/`raise`/`continue`/`break` versus that body) are never paired. The key
compares the iterable expression structurally, so `shelf.books` twice is one sequence.
