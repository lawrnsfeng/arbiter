---
id: R40
title: A function returning a tuple of structured values is a missing dataclass
tier: ast+semantic
severity: should-fix
status: ok
refs: Effective Python 2nd ed. Item 19 (Never Unpack More Than Three Variables When Functions Return Multiple Values), https://docs.python.org/3/library/dataclasses.html#frozen-instances, https://refactoring.com/catalog/combineFunctionsIntoClass.html
---
## Rule

- A function returning a tuple of two or more elements that are each structured objects is not allowed. (C1)
- It is replaced by a frozen dataclass holding those values. (C2)
- The old resolution logic becomes a `from_*` classmethod on that dataclass. (C3)
- Callers read attributes (`route.depot`) instead of unpacking a tuple. (C4)
- Exception: tuples of plain scalars, such as coordinate pairs or `(name, value)` rows, are fine. (C5)

## Incorrect

- A private resolver annotated `-> tuple[Depot, Courier]`, unpacked by its caller.
- A `typing.Tuple` of three structured values.
- An async function with string forward references in the tuple.
- An unannotated function returning two looked-up objects as a tuple (model only).

## Correct

- A frozen dataclass with a `from_parcel` classmethod; callers read its attributes.
- Look-alikes: a coordinate pair, a `(name, count)` row, a pair of paths, a homogeneous `tuple[Depot, ...]`, a pair of
  `NewType` temperatures, a pair of enum members, a pair of `str`-subclass ids.

## Detection

Reports a function whose return annotation is `tuple[...]` / `Tuple[...]` with two or more fixed elements, every one of
them (bare, dotted or a string forward reference) a class defined in the scanned modules that is not a scalar value:
classes deriving, directly or through a scanned base, from `str`, `int`, `float`, `bytes`, `bool`, `complex` or an
enum base are scalars, and so are `NewType`s, builtins and third-party types, which are not scanned classes
(C1, C2, C3, C5).

## LLM scan

- Flag unannotated functions, or ones annotated with a type alias, that return a tuple of two or more structured
  objects (records, clients, entries, models), and call sites unpacking such results (C1, C4).
- Flag annotated tuples of structured third-party classes (framework requests, ORM models from a library), which the
  detector does not see as structured (C1).
- Flag tuples mixing optional structured members (`Depot | None`) when the members are structured (C1).
- Do not flag tuples of scalars, coordinate pairs, `(key, value)` rows, or homogeneous variable-length tuples.
