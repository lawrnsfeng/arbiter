---
id: R57
title: Booleans are is_* or a precise compound naming what they gate, keyword-only
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog (Remove Flag Argument), PEP 3102, Effective Python (keyword-only arguments), flake8-boolean-trap (FBT)
---
## Rule

- Boolean parameters are named `is_*` or a precise compound naming what they gate, not a bare word such as `off`. (C1)
- Boolean attributes likewise: not a bare `enabled`, but a compound such as `sorting_enabled`. (C2)
- Boolean parameters are keyword-only. (C3)
- Call sites never pass bare positional `True`/`False` literals. (C4)
- The user-facing CLI flag may keep its name (e.g. `--off`) while the Python name is `is_off`. (C5)

## Incorrect

- A bare-word `bool` class attribute.
- A bare-word positional `bool` parameter of `__init__`.
- A bare-word `bool` instance attribute set in `__init__`.
- A bare-word positional `bool` parameter with a default.
- A bare-word keyword-only `bool` parameter.
- A well-named but positional `bool` parameter.
- A vague compound name (`do_it`) that does not say what it gates (model only).
- Positional `True`/`False` at two call sites.

## Correct

- `is_*` and precise compound names, all keyword-only, passed by keyword.
- An upper-case class setting and a boolean local variable.
- A click flag `--off` mapped to the Python name `is_off`.
- `True`/`False` passed as stored values to `dict.get`, `getattr`, `setdefault`.
- A property setter whose `value: bool` parameter is fixed by the protocol.

## Detection

Covers C1 and C2 for bare words, C3, and C4. Parameters annotated `bool` (also `bool | None`, `Optional[bool]`), except
in property setters and `@override` methods whose signature the protocol fixes: one hit per parameter that is a single lower-case word without an underscore (C1) and/or positional (C3). Per class, the
first declaration of a bare-word boolean attribute: `self.name = True/False`, `self.name: bool`, or a class-body
`name: bool` / `name = True/False` (C2). Every `True`/`False` literal passed positionally, except to callees that store
values (`get`, `pop`, `setdefault`, `getattr`, `setattr`, `append`, `add`, `set`, `print`, ...) (C4). C5 is a
permission and needs no check.

## LLM scan

Beyond the detector: report boolean parameters and attributes whose compound name still does not say what it gates
(`do_it`, `flag_value`, `mode_on`) (C1, C2), and unannotated parameters that are booleans by their default or use
(`def f(x, strict=False)`) and are bare words or positional (C1, C3). Do not flag a CLI option string that keeps a
short user-facing name (C5), parameters required by a framework or overridden signature the code does not own, or
`True`/`False` passed positionally to a callee whose parameter holds data rather than toggling behaviour.
