---
id: R2
title: The environment is read once, in one class
tier: ast+semantic
severity: should-fix
status: ok
refs: The Twelve-Factor App "Config" (https://12factor.net/config), pydantic-settings (https://docs.pydantic.dev/latest/concepts/pydantic_settings/), Python docs os.environ (https://docs.python.org/3/library/os.html#os.environ)
---
## Rule

- Every read of `os.environ` (`.get`, subscript, `os.getenv`, membership and the like) goes through one environment
  class in the package's `env` module; no other module reads the environment directly. (C1)
- The environment is read once: that class is the single read point, and callers use its accessor (for example a
  `current()` classmethod returning the loaded settings) instead of reading again. (C2)
- Exception: the package's paths module may read the XDG base-directory variables (`XDG_*`). (C3)
- Exception: code may pass the whole environment through to a subprocess as `{**os.environ, **extra}`. (C4)
- Those exceptions are accepted because they are not configuration reads; any other environment read, notably one
  with a fallback default such as `os.environ.get("USER", "nobody")`, is a violation. (C5)

## Incorrect

- A function falling back to `os.environ.get("NAME", "default")` for a setting.
- A subscript read `os.environ["..."]` and an `os.getenv(...)` call in ordinary modules.
- A membership test `"X" in os.environ` deciding behaviour.
- A copy `os.environ.copy()` taken to read and extend later.
- A settings class outside the environment module re-reading `os.environ` on every property access.

## Correct

- Callers going through `Settings.current()`, the accessor of the one settings class that lives in `env.py`.
- Look-alikes: a subprocess called with `env={**os.environ, **extra}`, a test patching the environment with
  `patch.dict(os.environ, ...)`, writes `os.environ["X"] = ...`, `del os.environ[...]` and `os.environ.update(...)`.

## Detection

`check.py` reports every `os.environ` / `environ` read and every `os.getenv` call (C1, C5), except: inside a class
defined in a module named `env.py` (the environment class, C1); a `XDG_*` string-key read in a module named `paths.py`
(C3); `**os.environ` unpacked into a dict literal (C4); assignment or deletion targets and `update` / `pop` / `clear`
writes; `os.environ` passed to a `*.dict(...)` patch call.

## LLM scan

- In the environment class itself, check the environment is loaded once (a cached classmethod, a module-level
  singleton or a frozen settings object) and that properties read the loaded values, not `os.environ` again (C2).
- Report a second environment class or settings loader alongside the first (C1, C2).
- Report callers that copy the environment (`os.environ.copy()`, `dict(os.environ)`) to read from it later (C1, C5).
- Do not flag the paths module's XDG reads, the subprocess pass-through `{**os.environ, **extra}`, or test code that
  sets the environment.
