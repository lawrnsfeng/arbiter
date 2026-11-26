---
id: R41
title: User-facing lists of same-shaped items are column-aligned
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/string.html#format-specification-mini-language, https://docs.python.org/3/library/stdtypes.html#str.ljust, owner convention
---
## Rule

- Any output or help text listing items of the same shape pads each column to a fixed width, so the items read as a
  table. (C1)
- Labels are padded to the longest label's width so every value starts in the same column. (C2)
- Hand-spaced, unpadded multi-item strings are a violation. (C3)

## Incorrect

- A three-state legend whose `state:  meaning` entries start their meanings in different columns.
- A command list in implicit string concatenation with hand-typed gaps.
- An f-string summary with uneven `label: value` lines.
- Rows built with `"\n".join(f"{a}: {b}" ...)` and no padding (model only).

## Correct

- Labels padded to the widest one, literally or with a format width (`{label:<{width}}`).
- Look-alikes: single-space `key: value` data text, and docstrings.

## Detection

Reports a string literal or f-string (fields count as one character; docstrings skipped) containing at least two lines
of the same indentation shaped `label: value` or `label  value` (label of up to four words, then two or more spaces)
whose values start in different columns, when at least one such line already uses two or more spaces of padding, i.e.
it was hand-spaced (C1, C2, C3).

## LLM scan

- Flag list output assembled at runtime (joins, loops of `echo`, f-strings without a width spec) whose items share a
  shape but are not padded to a common width (C1, C2).
- Flag hand-aligned literals that use single spaces throughout, if they are user-facing lists (C3).
- Do not flag data formats (YAML, headers, config samples), prose, or single-item messages.
