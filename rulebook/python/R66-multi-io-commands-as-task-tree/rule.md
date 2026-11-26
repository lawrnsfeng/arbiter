---
id: R66
title: A command doing many independent IO calls runs them as a task tree, not a sequential loop
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread, https://docs.python.org/3/library/asyncio-task.html#task-groups, owner convention
---
## Rule

- Applies to any command whose work is a tree of independent IO calls (status checks, audits, probes). (C1)
- Such a command runs through the project's shared flow module (one `flow` module per package) using its task-tree executor. (C2)
- Blocking leaves of the tree run via `asyncio.to_thread`. (C3)
- The run uses the flow's verbose progress narration (a progress reporter narrating the tree as it runs). (C4)
- A new sequential IO loop inside a command (e.g. `for station in stations: probe(station)` inline in the command function) is the regression. (C5)

## Incorrect

- `cmd_health` looping `for station in stations: probe(station)`.
- A click command looping `for host, port in mirrors: reachable = ping(host, port)`.
- An async command awaiting `fetch(url)` one URL at a time in a `for` loop.
- (LLM) A command loop whose IO call is wrapped inside a collection call (`sizes.append(os.path.getsize(path))`).

## Correct

- `cmd_health` building a `StationsTask` of `StationProbe` leaves, each running the blocking `ping_station` through `asyncio.to_thread`, and handing the root to `run_tree(..., progress=FlowNarrator(verbose=True))` from the package's flow module.
- Look-alikes: a command looping only to `print`/log results, a command folding chunks into an accumulator (`summary = fold(summary, chunk)`, each call needs the previous result), and a non-command helper with a loop.

## Detection

Inside a command function (named `cmd_*` or decorated with a `command` decorator), outside nested scopes, reports each `for`/`async for` loop whose body has a top-level statement (expression, assignment, or `await`) calling something with the loop variable as a direct argument, where the callee is not an output or collection call (`print`, `echo`, `secho`, `append`, `add`, `extend`, `update`, `write`, logging methods, `len`, `str`, `repr`, `format`, `join`, `sorted`) and no argument reads a name the loop body rebinds (a loop-carried dependency). These are candidates for C5, not definite findings: syntax cannot tell an independent IO call from pure computation, or from an ordered sequence whose dependency is not visible as data flow (e.g. applying migrations in order), so the LLM scan confirms each one.

## LLM scan

- Confirm each loop the detector reports really performs independent IO per item; dismiss loops over pure computation and ordered sequences whose items depend on each other through side effects (e.g. applying migrations in order).
- Flag sequential IO in commands the detector misses: IO hidden inside a collection call, a comprehension of IO calls, or a `while` loop paging through independent requests (C1, C5).
- Where a command already uses a task tree, check it goes through the package's shared flow module and executor (C2), blocking leaves use `asyncio.to_thread` (C3), and a progress reporter narrates (C4).
- Do not flag dependent sequences (each call needs the previous result) or loops outside command entry points.
