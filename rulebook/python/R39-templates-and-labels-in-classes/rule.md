---
id: R39
title: Message templates and command labels live in classes, not flat module constants
tier: ast+semantic
severity: should-fix
status: ok
refs: https://refactoring.com/catalog/combineFunctionsIntoClass.html, owner convention
---
## Rule

- In every messages module, output templates are attributes of a `class Messages:`, not flat module-level
  constants. (C1)
- `Messages` is aliased `Msg = Messages` so call sites read `Msg.X(...)`. (C2)
- Plain-string command properties (option labels, help strings) live in a separate `class Labels:`. (C3)
- Output text and command properties are not mixed in one class: they serve different purposes. (C4)

## Incorrect

- Templates assigned at module level, annotated or not.
- A `class Messages:` without the `Msg` alias.
- A plain help string inside `Messages`, and a template inside `Labels`.
- A command help string as a flat module constant (model only).

## Correct

- `class Messages:` of templates with `Msg = Messages`, and `class Labels:` of plain strings.
- Look-alike: a template built locally inside a function is not a module constant.

## Detection

Only in messages modules (a file named `messages.py`, or a module defining a top-level `class Messages` or
`class Labels`), reports a module-level assignment whose value is a `Template(...)` call (C1); a module-level
`class Messages` with no module-level `Msg = Messages` (C2); a plain string literal attribute inside `class Messages`
and a `Template(...)` attribute inside `class Labels` (C3, C4). Other modules are never reported.

## LLM scan

- Flag plain strings used as command labels, help or prompt text (`help=`, `prompt=`, option names) defined as flat
  module constants of a messages module instead of `Labels` attributes (C3).
- Flag templates held in other containers (dicts, other classes) of a messages module (C1).
- Do not flag templates or labels defined inside the class bodies, or modules that are not messages modules.
