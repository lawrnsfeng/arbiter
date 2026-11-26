---
id: R67
title: An isinstance ladder on one subject is a `match` with class patterns and a `case _` arm
tier: ast+semantic
severity: should-fix
status: ok
refs: https://peps.python.org/pep-0634/, https://peps.python.org/pep-0636/, https://docs.python.org/3/reference/compound_stmts.html#class-patterns, owner convention
---
## Rule

- Two or more `isinstance` tests on the same subject in an `if` ladder (an `if`/`elif` chain, or consecutive `if` statements each of which leaves the block) are a violation. (C1)
- The ladder is written as a `match` statement on the subject with class patterns (`case SomeClass():`). (C2)
- The `match` ends with a `case _:` fallback arm, per the project's match-fallback rule: the subject's type is not a closed set. (C3)

## Incorrect

- `if isinstance(reading, Rain): ... elif isinstance(reading, Snow): ...`: an elif ladder.
- `if isinstance(err, Timeout): return ...` followed by `if isinstance(err, Refused): return ...`: consecutive ifs on the same subject.
- `if isinstance(item, (Book, Magazine)): ... elif ... elif isinstance(item, Map): ...`: tuple-of-classes tests in a longer chain.
- `match parcel: case Letter(): ... case Box(): ...` with no `case _:` arm.

## Correct

- `match reading: case Rain(): ... case Snow(): ... case _: ...`.
- Look-alikes: a single `isinstance` guard, two tests on different subjects, `isinstance(a, X) and isinstance(b, Y)` in one condition, consecutive normalising `if isinstance(...)` steps that fall through, a `match` over literal values ending in `case _: raise`, and an exhaustive class-pattern `match` over a parameter annotated with the closed union `Circle | Square`, without `case _`.

## Detection

Walks every statement list. A run is an `if`/`elif` chain, extended by the next `if` statement only while every branch of the previous chain ends in `return`, `raise`, `continue` or `break` (then the next `if` behaves as an `elif`). Within a run, groups the tests that are exactly `isinstance(subject, ...)` by subject; a subject tested two or more times is reported once, at the first test's `if` (C1, C2). Also reports a `match` with a class pattern and no unguarded `case _:` arm when its subject is a parameter that is unannotated or annotated with a type that is not a union (`A | B`, `Union[...]`, `Literal[...]`, or a name bound to a union in the scanned modules) (C3, the open-type subset).

## LLM scan

- For `match` statements the detector skips (subjects that are locals, attributes, or annotated with a union), decide whether the subject's type is a closed set: if it is not, require `case _:` (C3); if it is a closed union covered exhaustively, do not require it.
- Flag isinstance ladders the detector misses: tests combined with other conditions (`if isinstance(x, A) and x.ready`), ladders spread over `if` statements that do not leave the block but still dispatch on type (C1, C2).
- Do not flag sequential normalising steps (`if isinstance(tags, str): tags = [tags]` followed by another independent conversion) where a `match` would change behaviour.
