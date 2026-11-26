---
id: R15
title: Framework-required unused parameters keep their required name
tier: ast+semantic
severity: should-fix
status: ok
refs: ruff ARG001-ARG005 unused-arguments (https://docs.astral.sh/ruff/rules/unused-method-argument/), ruff per-file-ignores setting (https://docs.astral.sh/ruff/settings/#lint_per-file-ignores), Click Command.format_help (https://click.palletsprojects.com/en/stable/api/#click.Command.format_help)
---
## Rule

- An unused parameter that a framework requires is prefixed with `_` when the framework allows renaming it. (C1)
- When the framework requires the exact name (it passes the argument by keyword, binds it by name, or the override
  signature is fixed), the parameter keeps the required name. (C2)
- In that case the unused-argument lint is silenced by a documented per-file ruff ignore in the project's ruff
  configuration, not by an inline suppression. (C3)

## Incorrect

- An overridden help-formatting method silencing its unused `ctx` with an inline `# noqa: ARG002`.
- A file-level `# ruff: noqa: ARG001` directive at the top of the module.
- A `# noqa: ARG001` placed after another comment (`# pragma: no cover  # noqa: ARG001`).
- A signal handler keeping an unprefixed unused `frame` parameter although it is called positionally (model only).

## Correct

- A positional-only callback with `_frame`; a positionally called override keeping its name, with a comment pointing
  to the per-file ignore in the ruff configuration, which is where the lint is silenced.
- Look-alike: `ARG002` and `noqa` mentioned inside a string literal.

## Detection

`check.py` reports every comment holding an in-source suppression of an unused-argument code `ARG001`-`ARG005`: a
line `# noqa: ...` or a file-level `# ruff: noqa: ...`, wherever it sits in the comment (C3).

## LLM scan

- Report unused parameters of framework callbacks and hooks that the framework calls positionally and that the code
  is free to rename, but that are not prefixed with `_` (C1). An override of a base-class method keeps the base's
  parameter names (its signature is fixed, C2): do not report it, only check that its lint is silenced in the ruff
  configuration (C3).
- Report parameters renamed with `_` although the framework binds them by name (a keyword-passed hook argument, a
  pytest fixture name, a dependency-injection parameter), which breaks the call (C2).
- Report other inline ways of silencing an unused framework parameter (`del ctx`, `_ = ctx`, a bare `# noqa` on the
  signature) where a per-file ruff ignore belongs, and per-file ignores in the ruff config without a comment saying
  why (C3).
- Do not flag unused parameters that are simply dead code to delete, or ignores in the ruff configuration file.
