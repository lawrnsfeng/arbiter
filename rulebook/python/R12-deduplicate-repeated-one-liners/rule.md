---
id: R12
title: Deduplicate a one-liner the moment it repeats
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog "Extract Function" (https://refactoring.com/catalog/extractFunction.html), Hunt & Thomas "The Pragmatic Programmer" - DRY principle, Fowler "Duplicated Code" code smell (Refactoring 2nd ed., ch. 3)
---
## Rule

- As soon as a one-line expression is repeated, even only twice, extract it into a named (private) helper used by
  every site. (C1)

## Incorrect

- The same `title.strip().lower().replace(" ", "-")` chain in two branches of one function.
- The same `path.read_text().splitlines()` chain in two functions.
- The same `datetime.now(UTC).date()` chain twice in one expression.
- The same transformation written with different variable names at two sites (model only).
- A short formula (`grams / serves`) written twice in one function (model only).

## Correct

- A private `_slug(title)` helper used by both branches; a `_lines(path)` helper; the date computed once.
- Look-alikes: two chains that differ in a method or an argument, a single chain.

## Detection

`check.py` reports every occurrence of a method-chain expression of two or more chained calls (outermost chain only)
that appears textually identical (same AST) at least twice in one module, naming the first occurrence (C1).

## LLM scan

- Report every other one-line expression that repeats, however short: repeated single calls (`x.strip()` written
  twice), the same expression with only renamed variables or reordered operands, repeated comprehensions and
  arithmetic formulas, within a module or across modules of a package (C1).
- Do not flag expressions that only look alike but compute different things (a different method, argument or
  operand).
