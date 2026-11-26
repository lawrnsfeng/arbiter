---
id: R21
title: Load shared external mutable state once per operation, never cache it across calls
tier: ast+semantic
severity: should-fix
status: ok
refs: owner convention, Python docs functools.cache / functools.lru_cache, Python docs fcntl.flock
---
## Rule

- State that another process can mutate between operations (a shared file, a registry on disk, a database row) is loaded once per operation, freshly. (C1)
- It is never cached across calls or operations: no module-level, memoised or process-lifetime cache of it. (C2)
- Re-reading it under a lock in order to mutate it atomically is allowed; that is atomicity, not redundancy. (C3)

## Incorrect

- `@functools.cache` on a loader that parses a shared inventory file.
- A module-level `_SNAPSHOT = None` filled once by a function with `global _SNAPSHOT` from `json.load(open(...))`.
- `@lru_cache(maxsize=1)` on a function that counts lines in a shared queue file.
- A module-level `ROSTER = json.loads(...)` read at import time and reused by every later command (model only).
- `low_stock()` loading the shared inventory twice in one operation, outside any lock (model only).

## Correct

- Each command calls the loader once and works on that fresh copy; the mutation path re-reads under `flock`.
- Look-alikes: `@cache` on a pure function; `@cache` on a reader of a file shipped inside the package
  (`Path(__file__).parent / ...`), which no other process mutates.

## Detection

`check.py` reports a function definition (one hit at its `def` line) when it reads a file (`open(...)`, `.open()`,
`.read_text()`, `.read_bytes()`, or `json`/`tomllib`/`yaml`/`pickle` `.load`) in its own body and either
(a) is decorated with `functools.cache`, `lru_cache` or `cached_property`, or (b) declares a name `global` and
assigns it, i.e. keeps the result for later calls. Functions that reference `__file__` or `importlib.resources` /
`pkgutil.get_data` read package data and are skipped. Covers the definite subset of C2.

## LLM scan

Decide whether the state is shared and externally mutable (C1): files other processes write, databases, remote
registries, environment set by another process. Flag caches of it the detector cannot see: module-level reads at
import time, class attributes or singletons that keep a loaded copy, instance fields reused across separate commands,
third-party caching decorators. Do not flag a re-read under a lock that exists to make a read-modify-write atomic
(C3), nor caches of immutable inputs (package data, constants, a config file the process documents as read once at
start-up). When flagging, propose loading once at the start of each operation and passing the value down.

Also flag the opposite defect (C1, C3): the same shared state loaded more than once within one operation (one command,
request or job), e.g. a helper that reloads the file its caller already loaded, or two loads in one function, when
the second load is not a re-read under a lock taken for an atomic read-modify-write. Propose loading once and passing
the loaded value to the helpers. A re-read inside the locked mutation path is atomicity, not redundancy: leave it.
