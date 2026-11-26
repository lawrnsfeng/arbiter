---
id: R35
title: A str subclass built from one plain str puts its logic in the constructor
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/reference/datamodel.html#object.__new__, https://docs.python.org/3/reference/datamodel.html#object.__init__
---
## Rule

- A `str` subclass constructed from a single plain `str` does not use a `from_*` classmethod for that conversion; the
  logic goes in the constructor. (C1)
- `from_*` classmethods are for multiple alternative constructors or for inputs that are not a plain `str`. (C2)
- Setup-only logic, which does not change the string value, goes in `__init__`. (C3)
- `__new__` is used only when the value itself changes, because `str` is immutable and `__init__` runs after the
  value exists. (C4)

## Incorrect

- A sole `from_isbn(cls, isbn: str)` classmethod returning `cls(<value rearranged from the isbn>)`.
- A sole `from_text` classmethod that validates and reformats through a local before `cls(...)`.
- A `__new__` that passes its argument unchanged to `str.__new__` and only sets attributes (setup-only work).
- An unannotated sole `from_*` converter whose argument is a plain string in practice (model only).

## Correct

- `__new__` doing the normalisation; `__init__` doing setup-only work.
- Look-alikes: a class with two `from_*` constructors, a `from_*` taking a non-`str` input, and a non-`str` class.

## Detection

Reports, in a class with a `str` base: a `from_*` `@classmethod` that is the class's only `from_*` method, takes
exactly one parameter after `cls` annotated `str`, and returns `cls(...)` (C1, C2); and a `__new__` that hands one of
its parameters, never reassigned, unchanged to `super().__new__` / `str.__new__` (C3, C4).

## LLM scan

- Flag sole `from_*` converters on `str` subclasses whose single argument is unannotated or annotated loosely but is a
  plain string at every call site (C1, C2).
- Flag `__new__` overrides that leave the value unchanged by other means (e.g. re-deriving the same string) and
  `__init__` overrides that try to alter the value (C3, C4).
- Do not flag `str` subclasses with several alternative constructors or constructors from bytes, paths, numbers or
  structured objects.
