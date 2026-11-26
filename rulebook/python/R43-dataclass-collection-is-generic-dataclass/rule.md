---
id: R43
title: A list of one dataclass plus free functions over it is a generic frozen dataclass
tier: ast+semantic
severity: should-fix
status: ok
refs: https://refactoring.com/catalog/encapsulateCollection.html, https://refactoring.com/catalog/combineFunctionsIntoClass.html, https://peps.python.org/pep-0695/, https://docs.python.org/3/library/dataclasses.html#frozen-instances
---
## Rule

- Module functions that each take a list of one dataclass type (and collapse, confirm or report it) become methods of
  a collection class. (C1)
- The collection is a generic (PEP 695 syntax) frozen dataclass holding a `tuple[Item[T], ...]`. (C2)
- It provides a `from_*` constructor taking the raw pairs (e.g. `from_tuples(*pairs)`) and `__iter__`. (C3)
- It is not a `list` subclass, and not pinned to `object`: it is immutable and keeps its element type. (C4)

## Incorrect

- Three free functions each taking `list[Substitution]` / `Sequence[Substitution]`.
- A `list[object]` subclass standing in for the collection.
- A `list[Substitution]` subclass, mutable and tied to `list`.
- An unannotated orchestrator threading the same list through the free functions (model only).

## Correct

- `Substitutions[T]`: frozen generic dataclass over `tuple[Substitution[T], ...]` with `from_tuples`, `__iter__`, methods.
- Look-alikes: a single function over a list of the records, functions over lists of plain values, a `list[str]`
  subclass unrelated to any record.

## Detection

Reports every module-level function of a module where two or more functions take, as first parameter, a `list` /
`Sequence` / `Iterable` / `Collection` / `tuple[..., ...]` of the same class decorated `@dataclass` in the scanned
modules (C1); and every class with a `list[object]` base or a `list[X]` base where `X` is such a dataclass (C4).
Other `list` subclasses (scalar lists, bare `list`) are left to the model.

## LLM scan

- Flag unannotated or loosely annotated free functions that receive the same list of records and are always called
  together on it (C1).
- Flag collection classes that are mutable, not generic over their element type, hold a `list` instead of a `tuple`,
  or lack a `from_*` constructor or `__iter__` (C2, C3, C4).
- Flag bare `list` subclasses that serve as the collection of one record type (C4).
- Do not flag a single helper over a list, functions over lists of scalars, or framework-required list subclasses.
