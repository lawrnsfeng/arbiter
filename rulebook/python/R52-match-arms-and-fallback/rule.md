---
id: R52
title: A match needs two or more arms and ends in case _ unless the subject is a closed set
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 634, PEP 636, typing docs assert_never (exhaustiveness checking)
---
## Rule

- A `match` statement has at least two arms; a single-arm match reads as an incomplete decision table and is written as an `if`. (C1)
- A `match` whose subject is not an enum or other closed set (strings, framework types, tuples, …) ends in `case _`, even when today's cases look complete. (C2)
- A `match` over an enum or other closed set has no `case _` fallback: the members are exhaustive, and a dead `case _` hides a missing case. (C3)
- Every path returns or raises explicitly; no arm falls through to an implicit `None` where the caller expects a value. (C4)

## Incorrect

- A single-arm `match` on an enum member that falls through to `None`.
- A `match` on string literals with no `case _`.
- A `match` on builtin type class patterns (`int()`, `str()`) with no `case _`.
- A `match` covering every enum member plus a dead `case _`.
- An arm that prints and returns nothing while the other arms return a value (model only).
- A dead `case _` after covering every value of a `Literal` alias subject.
- A `match` on a `Literal` parameter that misses one value and falls through to `None`.

## Correct

- The single-arm decision written as `if` plus an explicit `return`.
- A `match` over all enum members without a fallback.
- A string `match` ending in `case _: raise ...`.
- A tuple-pattern `match` ending in `case _`.
- A `match` on a `Literal` parameter covering every value, with no fallback.
- A `match` on an unannotated parameter whose arms name enum members, ending in `case _` (the subject is open).

## Detection

Covers C1 fully, and C2/C3/C4 where the subject's kind is visible. C1: every `match` with fewer than two arms, at the
`match`. A subject is closed when it is a function's parameter or annotated local declared `Literal[...]` (directly or
through a module-level alias) or as an `Enum`/`Flag` subclass defined in the scanned modules. C2: a `match` on a subject
not known to be closed, without an unguarded `case _`, whose patterns include a literal value, a sequence, a mapping,
or a builtin-type class pattern (`str()`, `int()`, …), at the `match`. C3: an unguarded `case _` on a subject declared as a
scanned enum, after arms that are all `Owner.MEMBER` values of a scanned enum, or after arms covering every value of the subject's `Literal`, at the
`case _`. Closedness comes from the subject's declared type only, never from the
patterns. C4: a `match` on a `Literal` subject without `case _` that leaves some of its values uncovered, at the
`match`.

## LLM scan

Beyond the detector: decide C2 and C3 when the patterns do not show the subject's kind — dotted values of classes that
are not enums defined in the scanned code (a plain class of integer constants is an open set and needs `case _`; an
enum imported from a library is a closed set and must not have one), and user-class patterns (`case Circle():`, closed
only when the subject's annotation is a union of exactly those classes). Check C4: in a function that returns a value,
report every arm (and the end of the `match`) that can finish without `return` or `raise`. Do not flag a `case _`
that raises or calls `assert_never` on an open subject, or a `match` inside a function that returns `None` by design.
