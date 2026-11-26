---
id: R11
title: No typing.Any
tier: ast
severity: should-fix
status: ok
refs: mypy docs "Dynamically typed code" / the Any type (https://mypy.readthedocs.io/en/stable/dynamic_typing.html), PEP 484 "The Any type" (https://peps.python.org/pep-0484/#the-any-type), ruff ANN401 any-type (https://docs.astral.sh/ruff/rules/any-type/), mypy --strict / disallow_any_explicit (https://mypy.readthedocs.io/en/stable/config_file.html#confval-disallow_any_explicit)
---
## Rule

- Never use `typing.Any`, in any annotation, alias or generic argument: it defeats a strict type checker. (C1)
- Use a concrete type, or a dataclass with typed fields, instead. (C2)

## Incorrect

- A record alias `Row = dict[str, Any]`.
- A parameter and a return annotated `Any`.
- `typing.Any` reached through the module, and `Any` imported under another name.
- `Any` nested in a generic argument of a variable annotation and in a `cast`.

## Correct

- A dataclass with typed fields, `object` for truly unknown values, concrete unions and protocols.
- Look-alikes: a local class or variable named `Any` that is not `typing.Any`, the builtin `any()`, the word "Any" in
  a string.

## Detection

`check.py` reports every use (outside the import statement) of a name bound to `typing.Any` or
`typing_extensions.Any` by `from ... import Any [as X]`, and every `typing.Any` / `<alias>.Any` attribute where the
alias was bound by `import typing [as alias]` (C1). Using a concrete type instead (C2) is the only way to clear a hit,
so the detector decides both clauses.
