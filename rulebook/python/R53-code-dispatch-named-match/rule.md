---
id: R53
title: Code-to-object dispatch is one named match, never an inline ladder or a dict
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 636, Fowler Refactoring catalog (Replace Conditional with Polymorphism, Move Function)
---
## Rule

- Mapping a code to the object it selects (a status code to an error class, a key to a builder) lives in one named method at the layer that owns the codes. (C1)
- The dispatch is not repeated inline at call sites, such as `if code == 403: raise ...` at every fetch site. (C2)
- The method body is a `match`, not an `if`-ladder. (C3)
- The mapping is not a module-level dict literal: a dict erases the order the arms are consulted in, hides whether a default was considered, and reads the same whether a missing key was a decision or an oversight. (C4)
- The pair "module-level mapping dict defined beforehand + a free function that does nothing but read it (`return MAPPING.get(key)`)" is a violation: delete both and put one `match` or `from_*` constructor on the type that owns the answer. (C5)
- Exception: a dict is acceptable for a closed set of more than about eight keys that is pure data with no ordering, default, or fallback meaning. (C6)
- Exception: a dict is acceptable when the mapping is itself a first-class value that callers enumerate. (C7)

## Incorrect

- An `if`/`elif` ladder on a response status, each arm raising a different error, at a fetch site.
- The same dispatch as sibling `if` statements at a second fetch site (literal on either side of `==`).
- A module-level dict of parsers plus a free function returning `MAPPING.get(kind)`.
- An annotated module-level dict keyed by tuples plus a documented free function returning `MAPPING[key]`.
- An inline dict literal indexed on the spot (model only).
- A ladder mapping status codes to message strings.

## Correct

- One `match` in a named client method, ending in an explicit default.
- A small dict that a caller enumerates with `.items()` (C7).
- A twelve-key pure-data table read without a default (C6).
- A single `==` test; an `==` ladder whose branches rebind a value instead of returning or raising.
- Recursion base cases `if n == 0: return 0` / `if n == 1: return 1`.

## Detection

Covers C2/C3 and C5 with the C6/C7 exceptions. Ladders: in every statement list, a run of two or more branches from
`elif` chains or sibling `if` statements, each testing the same subject `== <literal>` and each body a single
`raise <exception>` or `return <string literal, name, attribute or call>` (a message or object selected; number,
`None`, bool or arithmetic returns, such as recursion base cases, compute a value and do not count); one hit per run at its first `if`. Pairs: a top-level function whose body (docstring
aside) is only `return NAME.get(...)` or `return NAME[...]`, where `NAME` is a module-level dict literal of the same
module; one hit at the function. Exempt when `NAME` is enumerated anywhere in the scanned modules (`for _ in NAME`,
`NAME.items()/keys()/values()`, `list(NAME)`, ...) (C7), or when it has more than eight keys and is read by subscript
without a default (C6).

## LLM scan

Beyond the detector: report code-to-object mappings that are not in one named method on the layer that owns the codes
(C1) — for example the same single `if status == 403: raise ...` repeated at several call sites (C2), or a `match` in
a call site instead of in the owner's method. Also report `==` ladders whose arms return numbers or other computed values when the
literal being tested is a code (status, kind, key) and the returned value is what that code selects, as opposed to a
computation such as a recursion's base cases. Report module-level dict literals used as code-to-object dispatch even
without a dedicated reader function, including inline dict literals indexed on the spot (C4). Do not flag dicts that
are enumerated by callers (C7), large pure-data tables with no default or ordering meaning (C6), configuration data,
or `match` statements already inside a named method or `from_*` classmethod of the owning type.
