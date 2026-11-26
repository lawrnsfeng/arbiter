---
id: R30
title: Once a multi-parameter signature wraps, every parameter gets its own line
tier: ast
severity: should-fix
status: ok
refs: Ruff docs: Formatter, magic trailing comma, Black docs: The magic trailing comma, PEP 8 Indentation
---
## Rule

- When a signature with more than one parameter no longer fits on one line, every parameter goes on its own line. (C1)
- Whenever the signature wraps, add a trailing comma after the last parameter; it forces `ruff format` (and Black) to keep one parameter per line. (C2)
- No partially wrapped signature: no parameters sharing a continuation line, and no parameter left on the `def` line. (C3)

## Incorrect

- `def schedule(` then `self, recipe, servings, oven_c` all on one continuation line, `)` on its own line.
- A signature with the first parameter on the `def` line and the rest hanging below it.
- One parameter per line but no trailing comma after the last one.

## Correct

- `def schedule(` then `self,`, `recipe: str,`, `servings: int = 2,`, `oven_c: int | None = None,` each on its own
  line, then `) -> Plan:`.
- Look-alikes: a signature that fits on one line; a wrapped single-parameter signature; a one-line signature whose
  return annotation wraps.

## Detection

`check.py` looks at every `def` / `async def` with two or more parameters (`self`/`cls` included) whose closing
parenthesis is on a later line than `def`. It reports the function once, at the `def` line, when any parameter
shares a line with the `def` or with another parameter (C1, C3), or when no comma follows the last parameter before
the closing parenthesis (C2).
