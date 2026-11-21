# Python tool-enforced layer

## 2. Tool-enforced layer (reviewer stays silent here)

Rule: read `pyproject.toml` (`[tool.ruff]`, `[tool.mypy]`, `[tool.pyright]`, `requires-python`) first. Anything an enabled rule catches → silent. If the rule exists but is disabled, raise only if it is Block-class (§7).

Ruff 0.16 default = 413 rules incl. most of B, UP, RUF, SIM, PERF, PIE, C4, ASYNC, PYI, F; **removed from defaults**: E401, E402, E701–E703, E711, E712, E713, E714, E721, E731, E741–E743, F403, F405, F406, F722 (R16). So `== None`, `type(x) == T`, `f = lambda` are not caught unless the project selects E7.

| Canon | Ruff family / codes | Mechanizes | Type checker equivalent |
|---|---|---|---|
| P8 layout | `ruff format` (Black-compatible); E/W | indentation, whitespace, quotes, line length | — |
| P8 naming | N801–N818 (N818 `Error` suffix) | CapWords classes, snake_case funcs/args | pyright `reportConstantRedefinition` (opt-in) |
| P8 prog. recs | E711/E712 (None/bool compare), E721 (type compare), E722 bare except, E731 lambda assign, PIE810 multi-startswith, RET501–503 consistent returns, SIM118 `in d.keys()` | P8 "Programming Recommendations" | — |
| P257 | D100–D107 missing docstrings, D401 imperative mood, D417 undocumented param | docstring presence/shape | — |
| P585/P604/P695 | UP006 builtin generics, UP007/UP045 `X | Y`/`X | None`, UP040 `type` alias, UP046/UP047 PEP 695 generics, UP049 private type params, UP035 deprecated imports, UP037 quoted annotation, UP008 `super()` | modern syntax per target version | pyright `deprecateTypingAliases` |
| P484/P3107 | ANN001–ANN206, ANN401 `Any` | annotations present | mypy `disallow_untyped_defs`, `disallow_incomplete_defs`; pyright `reportMissingParameterType`, `reportUnknown*` |
| P3134 | B904 raise-without-from-inside-except | `raise X from err` in handlers | — |
| P343 | SIM115 open without `with`, SIM117 nested `with`, SIM105 `contextlib.suppress` | `with` usage | pyright `reportOptionalContextManager` |
| P20 "Errors never pass silently" | BLE001 blind except, S110/S112 try-except-pass/continue, TRY203 useless try, TRY201 verbose re-raise, TRY400 `logging.exception`, TRY401, TRY300 try-else, EM101–103 | exception hygiene | pyright `reportUnusedExcept` |
| Mutable defaults | B006, B008 call in default, RUF009 call in dataclass default, RUF012 mutable class default | shared-state bugs | pyright `reportCallInDefaultInitializer` (opt-in) |
| Closures/loops | B023 loop var not bound, B020, PLW2901 redefined loop name, PLW0120 useless loop-else | late binding | — |
| Simplification (P20 "Simple…/Flat…") | SIM101–SIM401, SIM108 ternary, SIM110 any/all, SIM113 enumerate, PLR5501 elif, PLR1714, FURB110/136 | needless branching | pyright `reportUnnecessaryComparison`/`IsInstance` (opt-in) |
| RH/EP3 loops & comprehensions | C400–C420, PERF401/403 manual comprehension, PERF101 list cast, PERF102 dict iterator, FURB129 readlines, SIM911, B905 `zip(strict=)`, RUF015 `next(iter())`, RUF017 quadratic sum | idiomatic iteration | — |
| Refurb modernization | FURB188 removeprefix, FURB101/103 `Path.read_text`/`write_text` (preview), FURB118 `operator` (preview), FURB142, FURB161 | stdlib helpers | — |
| Pylint design metrics | PLR0911/0912/0913/0915/0917 (too many returns/branches/args/statements/positional), PLR2004 magic value, PLW0603 `global`, PLC0415 import-outside-top-level, PLR6301 no-self-use (preview) | size/complexity | — |
| API traps | FBT001–003 boolean trap, ARG001 unused arg, SLF001 private access, A001–A006 builtin shadowing, ERA001 commented-out code | signatures | pyright `reportPrivateUsage` (opt-in) |
| Imports/packaging | I001 isort, TID251 banned API, TID252 relative imports, TC001–TC004 type-only imports, FA100/FA102, RUF022 sorted `__all__` | import hygiene | pyright `reportImportCycles`, `reportUnsupportedDunderAll`, `reportPrivateImportUsage`; mypy `no_implicit_reexport` |
| Typing idioms | PYI019 use `Self`, PYI034, RUF013 implicit Optional, RUF036 None last in union | typing style | mypy `--strict`; pyright `strict` |
| Logging | G004 f-string in logging (GSG 3.10.1), LOG015 root logger, LOG001, TRY400 | lazy %-format logging | — |
| Async | ASYNC210/212/220–222/230/240/250/251 blocking calls in async, ASYNC100/110/115, RUF006 dangling task, RUF029 unused async (preview) | event-loop hygiene | pyright `reportUnusedCoroutine` (default error) |
| Datetime/paths | DTZ001–DTZ901 naive datetimes, PTH100–PTH124 pathlib | tz-aware, pathlib | — |
| Security | S102 exec, S307 eval, S301 pickle, S506 yaml.load, S602/S604/S605 shell=True, S608 SQL string, S113 no timeout, S324 weak hash, S501 verify=False, S701 jinja autoescape, PLW1510 `subprocess.run` without `check`, PLW1514 no encoding (preview) | bandit-class | — |
| Tests | PT006, PT011 raises too broad, PT012 multi-stmt raises, PT017, PT018 composite assert, PT027, B017 | pytest idiom | — |
| Suppression hygiene | RUF100 unused noqa; v0.16 `# ruff: ignore[CODE] reason` comments | — | mypy `warn_unused_ignores`; pyright `reportUnnecessaryTypeIgnoreComment` |

mypy `--strict` ≈ `warn_unused_configs, warn_redundant_casts, warn_unused_ignores, strict_equality, check_untyped_defs, disallow_subclassing_any, disallow_untyped_decorators, disallow_any_generics, disallow_untyped_calls, disallow_incomplete_defs, disallow_untyped_defs, no_implicit_reexport, warn_return_any, extra_checks` (MYPY, "as of mypy 1.0"; list may change). `--strict` does **not** enable `--warn-unreachable` (MYPY CLI). mypy `explicit-override` error code for PEP 698 `[from memory]`.

pyright: `typeCheckingMode` ∈ off/basic/standard(default)/strict. These are worth enabling even in strict and are off by default: `reportImplicitOverride` (P698), `reportMatchNotExhaustive`, `reportUnnecessaryTypeIgnoreComment`, `reportImportCycles`, `reportMissingSuperCall`, `reportUninitializedInstanceVariable`, `reportUnusedCallResult`, `reportPropertyTypeMismatch`, `reportShadowedImports` `[from memory]` (PYR). Which rules strict turns on: see the PYR table (not read; gap).

**What tools cannot catch (reviewer's job):** name *quality* and domain fit; exception hierarchy designed for catchers; what belongs inside `try`; whether `raise from None` drops needed context; API shape (keyword-only args, return-object vs tuple, bool flags hidden by kwargs); abstract-in/concrete-out types; `Any` laundering through `cast`; Protocol vs ABC choice; leaking mutable internals; resource ownership across call boundaries; generator/async cleanup and cancellation; thread safety under free-threading; import-time side effects; global registries; inheritance depth and mixin creep; metaclass/power features; match vs if appropriateness; walrus overuse; comprehension readability; test design (mock overuse, integration vs unit); docstring accuracy; algorithmic complexity; authz/trust-boundary logic; t-string/HTML/SQL safety beyond pattern match; backwards compatibility and deprecation path.
