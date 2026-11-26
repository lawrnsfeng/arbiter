---
id: R34
title: Interpolated user-facing output is a named template in the subsystem's messages module
tier: ast+semantic
severity: should-fix
status: ok
refs: https://click.palletsprojects.com/en/stable/api/#click.echo, https://docs.python.org/3/library/string.html#format-string-syntax, owner convention
---
## Rule

- Interpolated user-facing output text is a named template defined in the subsystem's messages module. (C1)
- No inline f-string at the output call site (e.g. `click.echo(f"...")`). (C2)
- Templates are attributes of a `class Messages:` and are instances of the project's `Template(str)` type (see R39). (C3)
- Templates are invoked with keyword arguments. (C4)
- No `.format(...)` at the output call site. (C5)

## Incorrect

- `click.echo(f"...")` with a format-spec date field and a `!r` conversion.
- `secho("...".format(...))` at the call site.
- A messages template called with positional arguments.
- `%`-interpolation inside the output call.
- An f-string built into a local and echoed on the next line (model only).

## Correct

- A `class Messages:` of `Template` attributes, aliased `Msg`, invoked as `Msg.X(name=..., ...)`.
- Look-alikes: a plain literal echoed, an f-string without fields, a logging call, and `.format` used outside an
  output call.

## Detection

For output calls (`print`, `echo`/`secho` as names or attributes, e.g. `click.echo`, `typer.echo`), reports a first
argument that is an f-string with at least one field (C2), a `.format(...)` call (C5) or `%`-interpolation of a string
literal (C1); and reports any call `Msg.X(...)` / `Messages.X(...)` given positional arguments (C4).

## LLM scan

- Flag interpolated text that reaches an output call indirectly (assigned to a variable first, returned by a helper,
  joined from pieces) instead of coming from a messages template (C1, C2, C5).
- Flag templates defined outside the subsystem's messages module, or outside its `class Messages:`, or as plain
  strings instead of the project's `Template` type (C1, C3).
- Do not flag log calls, exception messages, or plain literals without interpolation.
