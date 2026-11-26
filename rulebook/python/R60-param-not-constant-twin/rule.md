---
id: R60
title: A parameter is never the case-twin of the constant it overrides
tier: ast+semantic
severity: should-fix
status: ok
refs: owner convention
---
## Rule

- A parameter's name is never the lower-case twin of a constant it overrides or shadows (`UPPER_NAME` → `upper_name`); renaming the constant into a parameter does not make the value configurable, it forks the name. (C1)
- Name the parameter for the concept it carries (e.g. `root`). (C2)
- The constant is read at call time by the caller, which passes it explicitly. (C3)

## Incorrect

- An optional parameter named as the lower-case twin of a module constant, falling back to the constant.
- An unannotated parameter twin of an imported constant.
- A method parameter twin of a module constant, on its own line of a multi-line signature.
- A concept-named parameter whose function still falls back to the constant itself instead of the caller passing it (model only).

## Correct

- Parameters named for the concept (`limit`, `window_days`, `shelf`), required, and the caller passing the constants.
- A local variable (not a parameter) named as the constant's twin.
- A `uuid` parameter beside the stdlib class `UUID`.
- A `t: list[T]` parameter beside a PEP 695 type parameter `T`.

## Detection

Covers C1: every parameter of every function whose upper-cased name equals, and differs from, an upper-case name bound
at module level or imported from a non-stdlib module (`from x import NAME`) in the same module (stdlib names such as `UUID` are classes; `TypeVar`/`ParamSpec`/`TypeVarTuple`/`NewType` assignments and one-letter names
are types, not constants); one hit per parameter, at its line.

## LLM scan

Beyond the detector: report parameters that override a constant under a slightly altered name (`data_root_dir` beside
`DATA_ROOT`, a class-level constant `Limits.MAX` beside a `max_value` parameter) when they only rename the constant
(C1), suggesting a name for the concept (C2). Report functions that take an optional parameter and fall back to a
module constant themselves (`value or CONSTANT`) instead of having callers read the constant and pass it (C3). Do not
flag parameters whose name describes a different concept that happens to share a word with a constant, or locals.
