---
id: R46
title: A variable's first assignment states its type
tier: ast
severity: should-fix
status: ok
refs: PEP 526, Python docs dataclasses (ClassVar pseudo-fields), typing spec (enum members are not annotated)
---
## Rule

- Every local variable is annotated at its first assignment; parameters and earlier annotated declarations count as stated. (C1)
- Class attributes are annotated at their first declaration in the class body. (C2)
- A constant declared inside a `@dataclass` is annotated `ClassVar[...]`; a bare annotation silently turns it into a field. (C3)
- Rationale: the annotation is the contract, so a later assignment of an incompatible shape fails at that assignment. (C4)

## Incorrect

- An empty dict bound unannotated and filled later in a loop.
- A local first bound unannotated, then reassigned (only the first binding is reported).
- A local first bound in an `if` branch unannotated, annotated only in the `else` branch below it.
- An `await` result bound unannotated in an async function.
- A class-body attribute declared without an annotation.
- An upper-case constant in a dataclass annotated `float` instead of `ClassVar[float]`.
- Locals of a nested function and of the enclosing method, each reported in its own scope.

## Correct

- Every first binding annotated; later rebindings unannotated.
- Loop targets, `with ... as` and tuple unpacking (no annotation syntax exists) and their later rebinding, rebound parameters, and a bare `name: T` declaration followed by a plain assignment.
- Enum members (the typing spec forbids annotating them) and dunder class attributes such as `__slots__`.
- A dataclass constant declared `ClassVar[float]`.

## Detection

Covers C1–C3 (C4 is the rationale, no separate obligation). In every function, walking only its own scope (nested
functions and classes are checked on their own): the first `name = value` with a single plain-name target whose name
is not a parameter, a `global`/`nonlocal` name, already stated by an annotated assignment, or already bound
by a binding that cannot carry an annotation (tuple, `for`, `with ... as`, walrus, `except ... as`, import) (C1). In every class body
outside `Enum`/`Flag` subclasses: the first `name = value` of a non-dunder name not annotated earlier in that body (C2).
In a `@dataclass` body: an annotated upper-case name whose annotation is not `ClassVar[...]` (C3). Tuple targets, loop
targets, `with ... as`, and walrus bindings are not reported: Python has no syntax to annotate them.
