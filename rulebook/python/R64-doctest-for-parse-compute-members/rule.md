---
id: R64
title: Parse/compute members and str/bytes/int subclasses carry a `>>>` example
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/doctest.html, https://peps.python.org/pep-0257/, Google Python Style Guide 3.8 (Comments and Docstrings), owner convention
---
## Rule

- A simple parse/compute member whose inner logic is hard to review carries a docstring example: one `>>>` line followed by its exact output. (C1)
- A time-dependent example carries `# doctest: +SKIP`. (C2)
- Every `str` subclass carries a `>>>` example in its docstring, because its form is the contract and nothing else states it. (C3)
- Every `bytes` subclass carries a `>>>` example. (C4)
- Every `int` subclass carries a `>>>` example. (C5)
- The example shows the constructor's accepted inputs and the exact text/bytes/number it yields; it is what a refactor (e.g. to `from_*` / `__init__`) is checked against, not optional decoration. (C6)
- A subclass whose `__new__` refuses a value shows the refusal as an example: the `Traceback` line and the error type. (C7)
- A prose-only docstring that describes the format without an example does not satisfy the rule. (C8)

## Incorrect

- `class IsbnText(str)` with a prose-only docstring: no example of the accepted input and produced text.
- `class Grams(int)` with no docstring at all.
- `class ShelfTag(bytes)` with a docstring that states the format in words only.
- `class Celsius(int)` with a `>>>` example but a `__new__` that raises and no `Traceback` example of the refusal.
- A `>>>` example calling `datetime.now()` without `# doctest: +SKIP`.
- (LLM) `def parse_reading(text)` that splits and scales a sensor string, documented in prose only.

## Correct

- `class IsbnText(str)` whose docstring shows `>>> IsbnText("978-0-13-468599-1")` and `'9780134685991'`.
- `class Celsius(int)` whose docstring shows both a valid example and the `Traceback (most recent call last):` / `BelowAbsoluteZero: -300` refusal, raising a project error subclass.
- A time-dependent example marked `# doctest: +SKIP`.
- Look-alikes: `class Unit(str, Enum)` (the members state the form), a `UserString` subclass, a plain class with a prose docstring, and a deterministic example building a `time(6, 0)` value.

## Detection

Reports, at the class line, every class whose bases include `str`, `bytes` or `int` (and no `*Enum`/`*Flag` base) whose docstring is missing or has no `>>>` line (C3, C4, C5, C8). For such a class with an example, reports its `__new__` when it contains a `raise` but the docstring lacks a `Traceback` line or the raised error's name (C7). In any docstring, reports a `>>>` line calling a clock (`now(`, `utcnow(`, `today(`, `monotonic(`, `perf_counter(`, `time_ns(`, `time.time(`) without `doctest: +SKIP` (C2); a `datetime.time(9, 30)` value is not a clock call.

## LLM scan

- Flag parse/compute functions and methods (string splitting, unit conversion, formatting, arithmetic over fields) whose logic is hard to review and whose docstring has no `>>>` example with exact output (C1).
- For str/bytes/int subclasses with an example, check the example shows real accepted input and the exact produced value, not a placeholder (C6).
- Flag time-dependent examples whose clock call is hidden behind the member under test (e.g. `>>> reading.stamped()` that reads the current time) and lack `# doctest: +SKIP` (C2).
- Check indirect subclasses (a subclass of a project `str` subclass) the detector does not resolve (C3–C5, C7).
- Do not flag enum mixins (`class X(str, Enum)`): the member values state the form. Do not flag trivial accessors or members whose output is obvious from the signature.
