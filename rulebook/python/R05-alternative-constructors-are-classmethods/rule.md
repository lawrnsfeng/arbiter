---
id: R5
title: Alternative constructors are classmethods named from_*
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs classmethod (https://docs.python.org/3/library/functions.html#classmethod), Effective Python 2nd ed. Item 39 "Use @classmethod Polymorphism to Construct Objects Generically", stdlib precedent datetime.fromtimestamp / dict.fromkeys (https://docs.python.org/3/library/datetime.html#datetime.datetime.fromtimestamp)
---
## Rule

- A function that constructs an instance of a class from some other input is an alternative constructor and is a
  `@classmethod` on that class, not a free function returning the class. (C1)
- Alternative-constructor classmethods are named `from_*`. (C2)

## Incorrect

- A module function `load_loan(path) -> Loan` reading a file and returning `Loan(...)`.
- A private module function `_loan_from_row(row) -> "Loan"` returning `Loan(*row)`.
- A classmethod `parse(cls, line)` returning `cls(...)`.
- A classmethod `create(cls, ...)` returning `cls(...)` built from a mapping.
- A module function building an instance through a local, setting attributes, and returning it (model only).

## Correct

- `Loan.from_json_file(path)` and `Member.from_csv_line(line)` classmethods.
- Look-alikes: a pytest fixture returning an instance, a function returning a stdlib type (`Path(...)`), a function
  delegating to `Loan.from_json_file`, a no-argument classmethod returning a canned instance, a function annotated
  with a project class that returns an existing object.

## Detection

`check.py` reports:
- an undecorated module-level function whose return annotation names a class defined in the scanned modules and that
  returns a direct call of that class (C1);
- a `@classmethod` taking at least one argument besides `cls`, not named `from_*`, that returns `cls(...)` (C2).

## LLM scan

- Report module-level functions and static methods that build an instance of a project class from another input in
  shapes the detector misses: through a local that is then mutated and returned, without a return annotation, or
  through `object.__new__` (C1).
- Report classmethods that construct the class from an input through a helper or a local and are not named `from_*`
  (C2).
- Do not flag test fixtures and factories, no-argument named presets (`Settings.default()`), plain `__init__`
  overloads, or functions returning a different class than their input's owner.
