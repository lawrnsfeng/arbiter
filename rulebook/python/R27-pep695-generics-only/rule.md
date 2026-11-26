---
id: R27
title: Built-in generic syntax only; never TypeVar or Generic
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 695 (type parameter syntax), Python docs typing: Generics, Python docs: What's New in Python 3.12
---
## Rule

- Never declare type variables with `typing.TypeVar` (nor `ParamSpec` / `TypeVarTuple`); use PEP 695 type-parameter syntax (`def f[T](…)`, `class C[T]:`). (C1)
- Never subclass `typing.Generic[...]` (nor a subscripted `Protocol[...]`); write `class C[T]:`. (C2)
- When two fields or parameters have the same type by design, say so with a type parameter instead of widening both to `object` (or `Any`). (C3)
- Premise: the project requires a Python version with PEP 695 (3.12+; the owner's projects require 3.13+), so the syntax is always available; the rule applies to such projects. (C4)

## Incorrect

- `K = TypeVar("K")` plus `class Shelf(Generic[K])`.
- `P = ParamSpec("P")` for a decorator; `class Source(Protocol[K])`.
- `class Change: before: object; after: object` where both sides are the same type (model only).

## Correct

- `class Shelf[K]:`, `def logged[**P, R](fn: Callable[P, R]) -> Callable[P, R]`, `class Change[T]: before: T; after: T`.
- Look-alikes: an unsubscripted `Protocol` base, the word `TypeVar` inside a string, a
  single `object` parameter that genuinely accepts anything.

## Detection

`check.py` reports every call to `TypeVar`, `ParamSpec` or `TypeVarTuple` (bare or as `typing.` /
`typing_extensions.` attributes) (C1) and every class base that is `Generic`, `Generic[...]` or `Protocol[...]` (C2).
It does not read the project's `requires-python` (C4 is the premise the rule assumes).

## LLM scan

Look for C3: pairs of fields or parameters annotated `object` or `Any` whose values are by design the same type (a
before/after pair, a key and a default of the same kind, a comparison of two values), and propose a type parameter.
Do not flag a single `object` parameter that truly accepts any value, `Any` at an untyped third-party boundary, or
code in a project whose `requires-python` is below 3.12 (C4); say so when you skip for that reason.
