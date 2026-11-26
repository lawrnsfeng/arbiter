---
id: R25
title: Custom type aliases live in a typedefs.py next to the code using them
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 613 (TypeAlias), PEP 695 (type statement), Python docs typing: Type aliases, Google Python Style Guide 3.19.6 Type Aliases
---
## Rule

- Custom type aliases are defined in a `typedefs.py` module, not inline in the module that uses them. (C1)
- One `typedefs.py` per package: a shared one at the package root, and one per subpackage next to that subpackage's code (e.g. `<package>/db/typedefs.py`). (C2)
- The module is named `typedefs.py`, never `types.py` (which shadows the standard-library module). (C3)
- An annotation that nests three or more levels of subscripts is a missing alias; name it in `typedefs.py`. (C4)
- An annotation that wraps (too long to fit on one line) is a missing alias; name it in `typedefs.py`. (C5)
- A tuple annotation with four or more members is a missing alias; name it in `typedefs.py`. (C6)

## Incorrect

- `CourseList = list[tuple[str, int]]` and `type Ingredient = dict[str, float]` defined in the module that uses them.
- `Scaler: TypeAlias = …`, `RecipeId = NewType(…)` and `MaybeServings = int | None` in the same module.
- A parameter annotated `dict[str, list[tuple[str, float]]]` (three levels).
- A return annotation `tuple[str, str, int, float]` (four members).
- An annotation that spans several lines.
- An alias used only by the `db` subpackage defined in the package-root `typedefs.py` (model only).

## Correct

- `recipes/typedefs.py` holds `Ingredient`, `CourseList`, `StepRow`; the code annotates `rows: list[StepRow]`.
- Look-alikes: two-level annotations (`dict[str, list[int]]`), `tuple[int, ...]`, a three-member tuple, a module
  constant `DEFAULT_UNITS = ("g", "ml")`, flag unions `READ | WRITE`.

## Detection

`check.py` reports, in any module not named `typedefs.py`:

- each module-level alias definition: a `type X = …` statement, `X: TypeAlias = …`, `X = NewType(…)` /
  `TypeAliasType(…)`, or `X = <type expression>` where the value is a subscripted generic (`dict[…]`, `Callable[…]`,
  `Literal[…]`, …) or a `|` union of such generics, builtin types or `None` (C1; the message names C3 when the module
  is `types.py`);
- each annotation (parameter, return, annotated assignment) that nests three or more subscript levels (C4), spans
  more than one source line (C5), or is a `tuple[…]` with four or more members, `...` not counted (C6). One hit per
  annotation, at its first line.

## LLM scan

Check placement across packages (C2): an alias used only inside one subpackage belongs in that subpackage's
`typedefs.py`; an alias shared across subpackages belongs in the package root's; flag a package with alias
definitions split across several non-`typedefs` modules the detector already reports as one consolidation. Also flag
annotations that are long on a single line only because formatting was skipped (C5). Do not flag `TypeVar`
definitions, `TypedDict`/`NamedTuple` classes (they are classes, not aliases), or `typedefs.py` itself.
