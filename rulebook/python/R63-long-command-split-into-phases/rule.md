---
id: R63
title: A long command body moves onto a record class with resolution and phase methods
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring "Replace Function with Command" / "Extract Function" / "Split Phase", https://refactoring.guru/smells/long-method, owner convention
---
## Rule

- A command function (a CLI entry point: named `cmd_*` or registered as a command) whose body is longer than about 30 lines moves its work onto a record class. (C1)
- That record class has a resolution classmethod (e.g. `from_args`) that turns the command's raw inputs (flags, config, defaults) into the record. (C2)
- The work is split into named phase methods on that class (e.g. announce, ensure the server, transfer). (C3)
- The command function stays thin: flag dispatch plus orchestration of the phases, nothing else. (C4)

## Incorrect

- `def cmd_audit(...)`: 30+ lines resolving flags, announcing, opening a client and looping, all inline.
- `@cli.command() def sync_parcels(...)`: a click-registered command with the same long inline body.
- `async def cmd_dispatch(...)`: an async command over the threshold.
- (LLM) `def cmd_label(...)` under 30 lines that still resolves inputs and performs three phases inline.

## Correct

- `ParcelAudit.from_args(args)` with `.announce()`, `.open_client()`, `.report()` and a five-line `cmd_audit` orchestrating them.
- Look-alike: a command whose body is one 35-line table literal stays silent.

## Detection

Reports every function named `cmd_*` or decorated with a `command` decorator (`@command`, `@x.command`, `@x.command(...)`) whose body, docstring excluded, spans more than 30 source lines, at the `def` line. A multi-line literal (dict, list, tuple, set, string) counts as one line, so a command whose length comes from a single declarative literal stays silent. Covers C1 and the length side of C4.

## LLM scan

- For commands near or under the threshold, flag bodies that still do resolution and several distinct phases inline instead of on a record class (C1, C4: "about 30" is a guide, not a licence).
- Where a record class exists, check it resolves inputs in one resolution classmethod (C2) and exposes named phase methods (C3), and that the command only dispatches and orchestrates (C4).
- Do not flag long functions that are not command entry points, nor commands whose length comes from a single declarative literal.
