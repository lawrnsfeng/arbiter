---
id: R45
title: A function built around one structured parameter is a method of that parameter's class
tier: ast+semantic
severity: should-fix
status: ok
refs: https://refactoring.com/catalog/moveFunction.html, https://refactoring.guru/smells/feature-envy, https://docs.python.org/3/library/functions.html#staticmethod
---
## Rule

- A free function with exactly one structured (project class) parameter, whose body mostly reads that object's
  fields and whose other parameters are all scalars, becomes a method of that object's class. (C1)
- Confirming tell: the function's name repeats the class's name as a prefix; the prefix is dropped once it is a
  method. (C2)
- Confirming tell: the structured object is the first parameter and every later parameter is a primitive. (C3)
- Confirming tell: the function, with its private helpers, is used only by that one class's code. (C4)
- Private helpers that do not take the class but are called only from the promoted methods move with them as
  `@staticmethod`s. (C5)
- Mixed I/O stays outside: the computation moves to the class, and the caller (e.g. a prompt) only does its own job
  (size, ask, delete). (C6)
- Not this rule: functions crossing several classes. (C7)
- Not this rule: functions whose structured parameter is second or later alongside other structured parameters. (C8)

## Incorrect

- `route_eta(route: ParcelRoute, traffic: float)` reading the route's fields.
- A private `_parcel_route_has_stop` with a primitive second parameter.
- A keyword-only primitive and a string forward reference to the class.
- The private helper used only by the promoted function (model only: becomes a `@staticmethod`).
- A prompt that computes from the object's fields with no name tell (model only: computation moves, prompt stays).

## Correct

- `ParcelRoute.eta`, `ParcelRoute.has_stop` with `_normalise` as a `@staticmethod`; `Locker.free_slots` used by a
  prompt that only asks.
- Look-alikes: a function crossing two classes, one whose structured parameter is second, a decorated callback.

## Detection

Reports an undecorated module-level function whose first parameter is annotated with a class defined in the scanned
modules, every other parameter is annotated with a primitive (`int`, `str`, `float`, `bool`, `bytes`, `dict`, `list`,
`set`, `tuple`, optionally `| None`), whose name (leading underscores dropped) starts with the class name in snake case
or its trailing words (`ParcelRoute` → `parcel_route_`, `route_`), and whose body reads at least one attribute of the
first parameter (C1, C2, C3, C7, C8).

## LLM scan

- Flag functions with the C1/C3 shape but no name tell whose body is mostly reads of the object's fields and that only
  one class's code calls (C1, C4).
- Flag private helpers called only from such functions; they should become `@staticmethod`s beside them (C5).
- For functions mixing I/O with computation on the object, flag them and say which computation moves to the class
  while the I/O stays in the caller (C6).
- Do not flag functions over several structured objects, functions whose structured parameter is not first,
  framework-registered callbacks, or functions reached from many classes.
