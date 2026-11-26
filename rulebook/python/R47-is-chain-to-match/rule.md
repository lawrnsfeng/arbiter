---
id: R47
title: An is-comparison chain over a closed set is a match
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 634, PEP 636
---
## Rule

- A chain of `if x is A` / `if x is B` comparisons of one subject against members of a closed set (an enum) is written as a `match` statement, which reads as the full decision table. (C1)

## Incorrect

- An `if`/`elif`/`else` ladder of `stage is Stage.X` tests.
- Sibling `if` statements (no `elif`) testing one attribute subject against enum members.
- Sibling `if` statements over a `StrEnum` defined in the same code.
- An `elif` ladder inside a loop against members of an enum imported from another module (model only).
- A ladder that starts after an unrelated `is None` guard.

## Correct

- The same decision as `match stage: case Stage.X: ...`.
- A single `is` test against a member.
- Consecutive `is` tests on different subjects.
- `is` tests against instance attributes (`self.pending`), which are not members of a closed set.
- `is` tests against sentinel attributes of a plain (non-enum) class.

## Detection

Covers C1 for enums defined in the scanned code. In every statement list, a run of two or more consecutive tests,
taken from `elif` chains and from sibling `if` statements, each of the form `subject is Owner.MEMBER` with the same
subject and the same owner (`Kind` or `module.Kind`), where `Kind` is an `Enum`/`Flag` subclass defined in one of the
scanned modules. One hit per run, at the first `if` of the run. `==` comparisons and `is None` tests do not take part.

## LLM scan

Beyond the detector: report the same ladders (two or more `subject is Owner.MEMBER` tests of one subject, as `elif`
chains or sibling `if`s) when `Owner` is a closed set the detector cannot see: an enum imported from a library or from
code outside the scan, or another closed set such as a `Literal` alias. Do not flag `is` tests against sentinel
objects of a plain class, against instance attributes, or a single test.
