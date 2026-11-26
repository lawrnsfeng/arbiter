---
id: R78
title: A private module-level function is promoted onto its type or states why it stays free
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring "Move Function", Fowler Refactoring "Combine Functions into Class", Fowler "Feature Envy" smell, Python docs classmethod/staticmethod
---
## Rule

- A private (underscore-prefixed) module-level function is a smell: promote it onto a type, or justify it. (C1)
- Tell (a): its body mostly reads one structured parameter's fields → make it a method of that parameter's type. (C2)
- Tell (b): the same project-owned parameter type recurs across the module's private functions → that parameter is `self`; the family becomes one class. (C3)
- Tell (c): its body only constructs or returns one project-owned type → make it that type's `@classmethod`. (C4)
- Tell (d): the module's private functions render or text-format → gather them into a renderer class. (C5)
- Tell (e): every caller is one class's code → make it that class's `@staticmethod` (a helper taking no instance still belongs to the class that calls it). (C6)
- The destination is decided mechanically by the tell, never by taste. (C7)
- A helper whose callers span two classes may stay free, but must state why. (C8)
- A helper a framework registers before any instance exists may stay free, but must state why. (C9)
- A free function with no tell (e.g. a predicate over primitives) is legitimate but still needs a stated reason. (C10)
- The reason is a docstring line starting `Stays free:` that names the type that would have to change, or the layering that forbids the move. (C11)
- Nested `def`s are out of scope (another rule covers them). (C12)
- The check is a mechanical gate: every private free function a change adds is listed with its tell. (C13)

## Incorrect

- A private function that reads two fields of one parameter and nothing else (tell a).
- Two private functions both taking the same project class as a parameter (tell b).
- A private function whose every return constructs one project class (tell c).
- A private slug helper referenced only from inside one class (tell e).
- Two private text-rendering functions next to each other (tell d, model only).
- A private predicate over primitives with no `Stays free:` line (C10, model only).

## Correct

- The same logic as methods, a classmethod, a staticmethod, and a renderer class.
- Look-alikes: a private helper used by two classes with a `Stays free:` line; a primitive predicate with a `Stays free:` line; a module `__dir__` dunder. (Nested `def`s are out of scope (C12) and the rulebook's nested-function rule allows almost none, so no example is shown; the detector only reads module-level `def`s.)

## Detection

For every module-level `def _name` (not a dunder) whose docstring has no line starting `Stays free:` (C1, C11),
`check.py` reports the first tell that holds, naming it in the message (C7, C13):

- (b) one of its parameters is annotated with a class defined in the scanned modules, and at least two private
  functions of the module take that annotation (C3);
- (e) every reference to the function's name in the module lies inside one class (C6);
- (c) every `return` is a call to the same class defined in the scanned modules (C4);
- (a) attribute reads on one parameter cover at least two distinct fields and more than half of the body's name
  reads (C2).

Nested functions are never examined (C12). Callers spanning two classes give no (e) tell (C8).

## LLM scan

- Tell (d): report private module functions that render or text-format (build strings, markup, tables) when the
  module has two or more of them: they belong in one renderer class (C5).
- For each private module function the detector did not report and that has no `Stays free:` docstring line, report
  it as missing its stated reason (C10, C11), unless it is a framework-registered callback (C9) or used by two
  classes (C8) and its docstring already says so in other words — then report only that the line must start
  `Stays free:`.
- Check that an existing `Stays free:` line names the type that would have to change or the layering that forbids the
  move; a vague reason ("utility", "helper") is a finding (C11).
- Do not flag public functions, dunders (`__getattr__`, `__dir__`), nested functions, or methods.
