---
id: R44
title: Multi-step CLI output lives in a rendering class, not loose private helpers
tier: ast+semantic
severity: should-fix
status: ok
refs: https://refactoring.com/catalog/combineFunctionsIntoClass.html, https://refactoring.com/catalog/extractClass.html
---
## Rule

- A commands module whose private (`_`) functions all print output (rows, sections, prompts) is a renderer without a
  class; it gets a rendering class instead. (C1)
- Rendering functions are grouped into a class per output flow. (C2)
- The class constructor holds the run's subject, the object being rendered. (C3)
- The class follows the project's existing rendering-class (view) pattern. (C4)
- Command entry functions (`cmd_*` or framework-decorated commands) stay thin flag dispatch. (C5)
- The rendering class lives in its own view module of the subsystem, not loose in the commands module. (C6)

## Incorrect

- A header, a row and a section helper, each private and printing, beside a decorated command.
- A command function that renders and prompts itself instead of dispatching (model only).

## Correct

- A view class built with the subject and flags, with `show`, `loan_line` and `fines` methods; the command only
  dispatches.
- Look-alike: a module whose private helpers do not all print.

## Detection

In a module with a command (a function decorated `@<x>.command` / `@command`, or named `cmd_*`), reports every private
module-level function when there are at least two and every one of them calls an output function (`print`, `echo`,
`secho`, `prompt`, `confirm`, `pause`) (C1).

## LLM scan

- Flag command functions that format or print rows themselves, loop over output, or prompt, instead of dispatching to
  a view (C5).
- Flag rendering classes that mix several output flows, take the subject per method call instead of in the
  constructor, live in the commands module, or ignore the project's existing view pattern (C2, C3, C4, C6).
- Do not flag a single one-line echo helper or a module with no command functions.
