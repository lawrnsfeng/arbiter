---
id: R49
title: Ellipsis is permitted without asking only in type positions
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs Ellipsis constant, PEP 484 (overload, stubs), PEP 544 (Protocol)
---
## Rule

- `...` may be used without approval in type positions, such as `tuple[str, ...]` and `Callable[..., T]`. (C1)
- An ellipsis standing in for a body (Protocol methods, `@overload` stubs, placeholders) changes what the file claims to define, so adding one requires asking the owner first. (C2)
- Ellipsis bodies that were approved when written (existing Protocol bodies) stay; every new one needs approval. (C3)

## Incorrect

- A one-line Protocol method whose body is `...`.
- A documented method whose body after the docstring is `...`.
- Two `@overload` stubs with `...` bodies.
- A `...` statement as a placeholder branch body.
- `...` as a parameter default and as a module-level placeholder value.

## Correct

- `...` inside subscripts and annotations: `tuple[str, ...]`, `Callable[..., None]`.
- A method that raises `NotImplementedError` instead of a stub body.
- Array indexing `grid[..., 0]` (a subscript position).
- The string `"..."`.

## Detection

Covers C1 and C2: every `...` constant that is not inside a subscript slice, a parameter or return annotation, an
annotated assignment's annotation, or a `type` alias value. The message says whether it is a statement (a body or
placeholder) or a value. Every such occurrence is reported; C3 (which ones were already approved) is the model's.

## LLM scan

The detector reports every `...` outside a type position. For each reported line, decide whether it is new: when
reviewing a change, keep only ellipses added by that change (C3: bodies that already existed, such as long-standing
Protocol methods, were approved when written and are not findings). Report a new ellipsis body or placeholder as
needing the owner's approval (C2), naming what it claims to define. Do not flag `...` in `.pyi` stub files, or an
ellipsis the change's own description says the owner approved.
