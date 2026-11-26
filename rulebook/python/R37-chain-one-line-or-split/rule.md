---
id: R37
title: A method chain is either one line or fully split, never half-wrapped
tier: ast
severity: should-fix
status: ok
refs: https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html#call-chains, https://peps.python.org/pep-0008/#maximum-line-length
---
## Rule

- A builder or method chain is either entirely on one line or fully split with one call per line. (C1)
- A chain is never half-wrapped, with some calls sharing a line and others split. (C2)
- If the one-line form fits within the line-length limit, the chain stays on one line; a long line that is still under
  the limit is the accepted trade-off. (C3)

## Incorrect

- A head call with its first segment on one line, remaining segments split.
- A split chain where two segments share a line in the middle.
- A fully split chain whose one-line form fits the limit.
- A split chain ending in an attribute, half-wrapped after the head.

## Correct

- A short chain on one line; a long-but-under-limit chain on one line; a chain too long for one line split one call
  per line.
- Look-alikes: a head call with exploded arguments and a segment on its closing line, and a dotted single call.

## Detection

A chain is the run of attribute accesses after its head call (the innermost call with its dotted receiver, e.g.
`Builder(x)` or `Model.objects.filter(...)`); only chains with at least two segments, two of them calls, count. A
segment starts a new line when its name sits below the end of its receiver. Reports a chain where some segments start
new lines and others do not (C1, C2), and a chain where all do although the enclosing statement, unparsed onto one
line at its indentation, fits in 120 columns, the project's ruff `line-length` (C3).
