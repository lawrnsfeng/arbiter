---
id: R79
title: No global mutable state; state belongs to an owner object with a lifecycle
tier: ast+semantic
severity: should-fix
status: ok
refs: Google Python Style Guide 2.5 (global variables), FastAPI docs Lifespan Events, Starlette docs Lifespan, Python docs contextlib, Python docs functools.lru_cache, Effective Python item "Use context managers"
---
## Rule

- Applies to every application kind (web app, worker, CLI, serverless function, script, test helper, migration); no exemption. (C1)
- `global` plus an assignment to that name inside a function is a violation. (C2)
- A module-scope `dict`/`list`/`set`/map that a function fills or mutates at runtime is a violation. (C3)
- A memoized client held at module level is a violation. (C4)
- A module-level mutable registry (e.g. keyed by module or name, filled at runtime) is a violation. (C5)
- `@lru_cache`/`@cache` on a factory with no eviction and no `close` is a violation. (C6)
- A module-level mutable container used as a cache (`_CACHE: dict[...] = {}`) is a violation. (C7)
- A module-level `name = None` sentinel filled on first use is a violation. (C8)
- A module-scope client instance (e.g. an HTTP client or session) is a violation. (C9)
- A lazily created module-level connection is a violation. (C10)
- Immutable constants (a number, a `StrEnum`, a compiled regex, a frozen collection) are not state and stay module-level. (C11)
- Fix: the owner is an object with attributes, constructed where the process is composed, never inside the function that first needs it. (C12)
- Fix: the owner has an explicit lifecycle (`start`/`close`, `aclose`, `__enter__`/`__exit__`, or `dispose`). (C13)
- A request-serving process binds the owner to the framework's lifecycle (ASGI `lifespan`, an app-ready hook plus a shutdown signal, before-serving/teardown hooks) and stores it on the app or container, never on the module. (C14)
- A worker, CLI, script, or test binds the owner to a `with` block (or the entry point's `try/finally`) so every exit path releases it. (C15)
- A test constructs its own owner, so two tests never share a loop, pool, or cache. (C16)
- The test to apply: the thing that owns the process can reach, replace, and release the state; needing a "reload" means a singleton in disguise. (C17)

## Incorrect

- A module-level `None` loop sentinel that a function rebinds through `global` on first use.
- A zero-argument factory wrapped in `@lru_cache` that returns a client nobody closes.
- A module-level dict of readings that a function appends into.
- A module-level HTTP client instance.
- A module-level parser registry that a decorator fills.
- A module-level holder object whose connection attribute a function sets lazily (model only).

## Correct

- A `WeatherService` owner with `__enter__`/`__exit__`, built in the ASGI lifespan, stored on `app.state`, and closed in `finally`; a worker using it in a `with` block; a test building its own.
- Look-alikes: a numeric constant, a `StrEnum`, a frozenset, a plain module list never mutated, an `lru_cache(maxsize=…)` on a pure function with arguments, a zero-argument `@cache` returning a frozenset, and a function mutating a parameter that shadows a module name. (A compiled regex is also a constant, but by the rulebook's patterns rule it lives in the patterns module, so it is not shown here.)

## Detection

`check.py` reports:

- each name a function declares `global` and then assigns, at the `global` statement (C2, C8, C10);
- each module-level binding to a container (literal, comprehension, `dict()`/`list()`/`set()`/`defaultdict()`/`deque()`/…)
  that some function mutates by subscript store/delete or a mutating method, unless a same-named local or parameter
  shadows it in that function (C3, C5, C7);
- each module-level binding to a call of `*Client`/`*Session`/`*Pool`/`*Engine`/`*Connection` or `create_engine`/`connect`/`client`/`resource` (C4, C9);
- each module-level function decorated with `@cache`/`@lru_cache` whose return annotation names a
  `*Client`/`*Session`/`*Pool`/`*Engine`/`*Connection` type or whose `return` builds one: the cached client can never be
  closed or evicted (C4, C6). Cached functions returning other values (a compiled regex, a frozenset) are constants (C11).

Constants are never reported (C11).

## LLM scan

- Report keyword-less globals the detector cannot see: a module-level object whose attributes a function sets at
  runtime, a class attribute used as a process-wide cache, a module-level client created behind a helper whose name
  does not look like a client factory, a lazily opened connection stored anywhere at module scope (C3, C4, C10).
- For `@cache`/`@lru_cache` on a factory the detector cannot type (no client-like annotation or constructor name) that
  returns a client, pool, connection, or other resource needing release, report it: it has no `close` (C6).
- When a change introduces an owner object, check that it is built where the process is composed (C12), has an
  explicit lifecycle (C13), is bound to the framework lifespan and stored on the app/container (C14) or to a `with`
  block / `try/finally` in workers, CLIs, scripts and tests (C15), and that each test builds its own (C16). Apply C17:
  report any state that only a module reload could reset.
- Do not flag immutable constants, enums, compiled regexes, tuples/frozensets, type aliases, `__all__`, logger
  objects, or containers only mutated at import time in the module body (C11).
