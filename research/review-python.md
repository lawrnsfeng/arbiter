# Python Code Review Research Base

Snapshot: 2026-11-21. Every claim cites a source key from §1 that was opened this session. `[from memory]` = not verified this session.

## 1. Canon

| Key | Source | URL | Authority | Governs | Version/date |
|---|---|---|---|---|---|
| P8 | PEP 8 Style Guide | https://peps.python.org/pep-0008/ | official | layout, naming, programming recs | Active; stdlib 79/72 cols, teams may go to 99 |
| P20 | PEP 20 Zen | https://peps.python.org/pep-0020/ | official | design values ("Errors should never pass silently", "Flat is better than nested", "Namespaces…") | Active |
| P257 | PEP 257 Docstrings | https://peps.python.org/pep-0257/ | official | docstring structure (imperative summary, blank line, args/raises/side effects) | Active |
| P572 | PEP 572 walrus | https://peps.python.org/pep-0572/ | official | `:=`; style recs: prefer statements; restructure if execution order is ambiguous | Final, 3.8 |
| P3134 | PEP 3134 exception chaining | https://peps.python.org/pep-3134/ | official | `__context__` (implicit), `__cause__` via `raise … from` | Final, 3.0 |
| P695 | PEP 695 type params | https://peps.python.org/pep-0695/ | official | `class C[T]`, `def f[T]`, `type X = …` | Final, 3.12 |
| P698 | PEP 698 `@override` | https://peps.python.org/pep-0698/ | official | explicit override marker | Final, 3.12 |
| P742 | PEP 742 `TypeIs` | https://peps.python.org/pep-0742/ | official | narrowing; "most users should use TypeIs, TypeGuard reserved for rare cases" | Final, 3.13 |
| PTY | PEPs 544 Protocol (3.8), 585 builtin generics (3.9), 593 Annotated (3.9), 604 `X|Y` (3.10), 612 ParamSpec (3.10), 646 TypeVarTuple (3.11), 681 dataclass_transform (3.11) | https://peps.python.org/pep-0544/ etc. | official | typing evolution | versions confirmed from PEP headers; 484/526/3107 `[from memory]` |
| P765 | PEP 765 | https://peps.python.org/pep-0765/ | official | `return/break/continue` exiting `finally` → SyntaxWarning in 3.14 | Final |
| P779 | PEP 779 | https://peps.python.org/pep-0779/ | official | free-threaded build "officially supported" (phase II of PEP 703) | 3.14 |
| W313/W314/W315 | What's New 3.13 / 3.14 / 3.15 | https://docs.python.org/3/whatsnew/3.13.html · …/3.14.html · …/3.15.html | official | modern features to prefer | 3.15 released 2026-10-09 |
| DEVV | Status of versions | https://devguide.python.org/versions/ | official | support windows | 3.15/3.14 bugfix; 3.11–3.13 security; 3.10 EOL 2026-10-01 |
| TBP | Typing Best Practices | https://typing.python.org/en/latest/reference/best_practices.html | official (typing council docs) | `object` vs `Any`, abstract params/concrete returns, `X | None`, builtin generics | living doc |
| AIO | asyncio Tasks docs | https://docs.python.org/3/library/asyncio-task.html | official | TaskGroup, strong refs to tasks | 3.15 docs |
| GSG | Google Python Style Guide | https://google.github.io/styleguide/pyguide.html | org | language rules (§2) + style (§3) | current (mentions pyrefly) |
| DJS / DJP | Django coding style; Submitting patches (review checklist) | https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/coding-style/ · …/submitting-patches/ | org (large project) | project conventions; review checklist | dev docs |
| EP3 | Effective Python 3e (Slatkin), 125 items (TOC) | https://www.pearson.de/media/muster/toc/toc_9780138172244.pdf | community canon (book) | idioms; item headers only | 2024 |
| RH | Hettinger "Transforming Code into Beautiful, Idiomatic Python" (PyCon 2013) notes | https://github.com/JeffPaine/beautiful_idiomatic_python | community (3rd-party transcript, Py2-era) | looping/dict/unpacking idioms | 2013 |
| BR | python-patterns.guide (Brandon Rhodes) | https://python-patterns.guide/ | community | GoF patterns in Python | ©2018–2020 |
| RUFF / RUFFD / R16 | Ruff rules; default rules; v0.16 blog | https://docs.astral.sh/ruff/rules/ · https://docs.astral.sh/ruff/default-rules/ · https://astral.sh/blog/ruff-v0.16.0 | tool | mechanized canon | 0.17.x (Nov 2026); 0.16 default set = 413 rules |
| MYPY | mypy existing-code guide (`--strict` equivalent) + CLI | https://mypy.readthedocs.io/en/stable/existing_code.html · …/command_line.html | tool | strict type checking | strict list "may change over time" |
| PYR | pyright configuration | https://github.com/microsoft/pyright/blob/main/docs/configuration.md | tool | `typeCheckingMode: strict` + opt-in rules | current |
| DEVPR / DEVC | CPython devguide: PR lifecycle; Accepting PRs | https://devguide.python.org/getting-started/pull-request-lifecycle/ · https://devguide.python.org/core-team/committing/ | official | how CPython reviews | current |

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

## 3. Idiom checklist (reviewer-only)

| Area | Flag | Don't flag (exception) | Source |
|---|---|---|---|
| Naming | Names that needlessly encode the type (`id_to_name_dict`) | Disambiguating two representations of the same data | GSG 3.16.1 |
| Naming | Single-letter names outside tight scopes | `i/j/k/v` counters, `e` in except, `f` in with, private TypeVars, paper notation | GSG 3.16.1 |
| Naming | Ad-hoc abbreviations, letters deleted mid-word | Standard aliases (`np`, `pd`) | GSG 3.16, 2.2.4 |
| Naming | `__double_leading` for "privacy" | Real name-mangling need in inheritance | GSG 3.16.2; P8 Designing for Inheritance |
| Naming | Factory/helper named as a noun kind (`decimal_factory`) | Framework-mandated names | BR abstract-factory (prefer verb `build_decimal`) |
| Naming | Exception class not ending in `Error` when it signals an error | Control-flow/signal exceptions | P8 |
| Errors | Hierarchy organized by *where raised* instead of what catchers need | — | P8 ("Design exception hierarchies based on… code catching") |
| Errors | Library raising bare `Exception`/`ValueError` from many sites with no root exception | Small scripts | EP3 Item 121 |
| Errors | `try` body wider than the one call that can raise | — | P8; EP3 Items 80, 83 |
| Errors | Translating exception without `from err`, or `from None` without copying details into the new message | Deliberately hiding internals at an API boundary, with details preserved | P8; P3134 |
| Errors | Returning `None` to signal failure where caller must check | Optional lookups documented as such (`dict.get`) | EP3 Item 32 |
| Errors | `assert` used to validate input or required logic | Tests; internal invariants for type narrowing | GSG 2.4.4; EP3 Item 81 |
| Errors | `except Exception` that neither logs traceback nor re-raises | Top-level loop that logs with traceback | P8 bare-except rule |
| Errors | Catching `BaseException`/custom subclass of `BaseException` | Cleanup-then-re-raise | P8; EP3 Item 86 |
| Errors | Error messages that assume a cause, or are hard to grep | — | GSG 3.10.2 |
| Errors | `return`/`break`/`continue` inside `finally` | — (3.14 SyntaxWarning) | P765 |
| Errors | Using exception var after the `except` block | — | EP3 Item 84 |
| Resources | Resource opened in one function and closed by an unrelated one | Ownership transferred to a context-managed object | GSG 3.11; P8 |
| Resources | Generator holding a resource (file/conn) open across yields | Caller owns and passes the resource in | EP3 Item 89; GSG 2.9.4 |
| Resources | `with conn:` whose `__exit__` commits/rolls back (hidden semantics) | Explicitly named CM like `conn.begin_transaction()` | P8 |
| Resources | Hand-rolled try/finally repeated in several places | One-off | EP3 Item 82 (`contextlib`) |
| Resources | `__del__` for cleanup | — | GSG 2.19 |
| API design | >3 positional returned values unpacked by caller | Well-known pairs (`divmod`) | EP3 Item 31 |
| API design | Optional/flag params callable positionally | Single obvious positional | EP3 Item 37 (keyword-only `*`, positional-only `/`); FBT |
| API design | Dynamic default computed at def time | — | EP3 Item 36; GSG 2.12.4 |
| API design | Decorator without `functools.wraps` | — | EP3 Item 38 |
| API design | Lambda glue where `functools.partial`/`operator.*` fits | Trivial one-liners | EP3 Item 39; GSG 2.10.4 |
| API design | Getter/setter pairs that only read/write an attribute | Non-trivial cost or invalidation (use a method) | GSG 3.15; EP3 Items 58–59 |
| API design | `@property` doing I/O or heavy work, or meant for subclass override | Trivially derived values | GSG 2.13.4 |
| API design | `@staticmethod` instead of module function | Required by external API | GSG 2.17.4 |
| API design | Class with one method + `__init__` used as a function | Needs state across calls | EP3 Item 48; BR abstract-factory ("Stop Writing Classes") |
| API design | Function iterating an argument twice (iterator exhausted) | Param typed `Sequence`/`Collection` | EP3 Item 21 |
| API design | Function mutating caller's arg without saying so | Documented in-place API (`list.sort`) | EP3 Item 30 |
| API design | Public API change without deprecation path | Private/internal | DEVPR §backward-compat; EP3 Item 123 (`warnings`); W313 `warnings.deprecated` (PEP 702) |
| Types | `Any` where `object` suffices (accepts anything) | Inexpressible types | TBP |
| Types | Params typed concrete (`list[str]`) when only iterated | Mutation required | TBP |
| Types | Returns typed abstract (`MutableMapping`) for concrete impl | Protocol methods | TBP |
| Types | Union return types forcing `isinstance` at call sites | Unavoidable; then `X | Any` | TBP |
| Types | `TypeGuard` where `TypeIs` fits | Narrowing to non-subtype | P742 |
| Types | Overriding methods without `@override` in typed code | Project not on 3.12+/typing_extensions | P698 |
| Types | `cast`/`# type: ignore` without code or reason | — | GSG 2.1.4 (explain suppressions); MYPY warn_unused_ignores |
| Types | `TypeVar` declared + `Generic[T]` on 3.12+ targets | Older `requires-python` | P695 (UP046/047 if enabled) |
| Types | `NewType`/`Annotated` metadata used as runtime validation without a consumer | Framework consumes it (FastAPI, pydantic) | PTY (PEP 593) |
| Types | Bare generic `Sequence`/`Mapping` (implicit Any) | — | GSG 3.19.15 |
| Types | Circular import "solved" by string annotation hack | Clear `TYPE_CHECKING` import | GSG 3.19.14 (circular deps = smell) |
| Data modeling | Deeply nested dict/list/tuple as a domain model | Transient JSON at boundary | EP3 Item 29 |
| Data modeling | Hand-written `__init__/__repr__/__eq__` boilerplate | Custom semantics | EP3 Items 51, 56 (dataclasses, frozen) |
| Data modeling | Mutable value object used as dict key/set member | — | EP3 Item 56 |
| Data modeling | `isinstance` ladders for polymorphism | Boundary parsing; `match` on closed set | EP3 Items 49–50 (singledispatch) |
| Data modeling | Custom container not inheriting `collections.abc` | — | EP3 Item 57 |
| Data modeling | Only some rich comparisons implemented | Use `functools.total_ordering`/dataclass `order=True` | P8 |
| Data modeling | `float` for money | — | EP3 Item 106 (decimal) |
| Data modeling | Naive datetimes for wall-clock logic | — | EP3 Item 105; DTZ |
| Control flow | `match` used where 1–2 `if`s suffice | Destructuring of structured data | EP3 Item 9 |
| Control flow | Walrus where a plain assignment works; walrus making evaluation order unclear | Regex match capture, `while chunk := read()`, comprehension filter reuse | P572 style recs; EP3 Items 8, 42 |
| Control flow | `for…else` used in a way readers misread | Search loops with `break` (RH idiom) | EP3 Item 19 vs RH (tension; prefer clarity) |
| Control flow | Loop variable used after loop | — | EP3 Item 20 |
| Control flow | Comprehension with >2 control subexpressions / multiple `for` | — | EP3 Item 41; GSG 2.7.4 |
| Control flow | Complex conditional expression spanning concerns | Simple 1-line ternary | GSG 2.11.4; EP3 Item 7 |
| Control flow | Mutating container while iterating | Iterate over copy | EP3 Item 22; RH |
| Control flow | `if x:` where `x` may be a falsy non-None value (0, "", []) | Known container/str | P8; GSG 2.14.4 |
| Concurrency | Threads for CPU parallelism | Free-threaded build, deliberately | EP3 Item 68; P779 |
| Concurrency | Shared mutable state without `Lock`; relying on dict/list op atomicity | — (more risky on free-threaded 3.14+) | GSG 2.18; EP3 Item 69; P779 |
| Concurrency | Manual thread spawn per request | `ThreadPoolExecutor`/`Queue` | EP3 Items 70, 72, 74 |
| Concurrency | `asyncio.gather`/bare `create_task` for owned subtasks | Fire-and-forget with stored ref + done-callback | AIO (TaskGroup: stronger safety; store task refs) |
| Concurrency | Blocking work in event loop not caught by ASYNC rules (CPU loops, sync SDKs) | `asyncio.to_thread`/executor | EP3 Item 78 |
| Concurrency | `functools.lru_cache` on methods (leak) — B019 if enabled; also caches without lock under free-threading | — | RUFF B019 |
| Mutability | Returning internal mutable list/dict to callers | Documented ownership transfer; return tuple/`frozendict` (3.15) | W315 PEP 814 |
| Mutability | Mutable module-level state / registries | Constants; documented process-wide cache with public accessor | GSG 2.5.4; BR global-object |
| Mutability | Import-time I/O or heavy computation | Cheap constants | BR global-object ("Import-time I/O") |
| Modules | No `__all__` in public modules whose internals look public | `_`-prefixed internals | P8 Public and Internal Interfaces |
| Modules | `from x import y` of functions/classes where house style is module imports | Typing imports; project convention differs | GSG 2.2.4 (house-dependent; Django uses one-dot relative—DJS) |
| Modules | Function-local imports for startup speed | Pre-3.15 targets; cycle breaking | W315 PEP 810 `lazy import`; EP3 Item 98 |
| Modules | Nested function used only to "hide" a helper | Closure over locals | GSG 2.6.4 |
| Modules | Missing `if __name__ == "__main__":` in executable modules | — | GSG 3.17 |
| Modules | Metaclass where `__init_subclass__`/class decorator works | Framework internals | EP3 Items 62–66; GSG 2.19 |
| Testing | Test asserts only truthiness for booleans | — | DJS (`assertIs(x, True)`) |
| Testing | Exception tests that don't check message/type precisely | — | DJS (`assertRaisesMessage`); PT011 |
| Testing | Bug fix without a regression test that fails before the fix | Pure docs | DJP checklist; DEVPR ("will not be accepted without the proper tests") |
| Testing | Heavy mocking of own code where an integration test is cheap | External services | EP3 Items 109, 111–112 |
| Testing | Float equality in tests | — | EP3 Item 113 |
| Testing | Test docstrings with "Tests that…" preambles | — | DJS |
| Docs | Docstring restating signature, non-imperative summary, missing Raises/side effects | Trivial private helpers | P257; GSG 3.8 |
| Docs | Generator docstring with "Returns:" | — | GSG 2.9.4 ("Yields:") |
| Docs | Subclass docstring not saying override vs extend | — | P257 |
| Docs | Public behavior change without docs/`versionadded`/NEWS | Internal | DEVPR; DJP |
| Docs | Comments in first person ("we loop") | — | DJS |
| Performance | Optimizing without profiling evidence | — | EP3 Items 92–93; W315 `profiling` |
| Performance | `+=` string building in loops | Short fixed concatenations | P8 (`''.join`) |
| Performance | Building lists only to iterate once | Need len/reuse | EP3 Items 43–44; GSG 2.9 |
| Performance | `list.pop(0)` queues; linear search on sorted data; manual priority queue | — | EP3 Items 102–104 |
| Performance | f-strings in logging calls (eager formatting) — G004 if enabled | — | GSG 3.10.1 |
| Performance | Copying `bytes` slices in hot I/O | — | EP3 Item 99 (memoryview) |
| Security | `eval/exec` outside developer tooling | — | EP3 Item 91; S307/S102 |
| Security | SQL/HTML/shell built by f-string from untrusted input (incl. patterns S608 misses) | Parameterized APIs; t-strings with a sanitizing processor (3.14+) | W314 PEP 750; S608 |
| Security | Unpickling untrusted data; custom pickle without versioning | Trusted local caches | S301; EP3 Item 107 |
| Security | `random` for tokens | `secrets` | S311 |
| Security | `subprocess` with user input, no `check`, no timeout | — | EP3 Item 67; PLW1510; S603 |

## 4. Design patterns & architecture

| Pattern | Pythonic verdict | Native replacement | Source |
|---|---|---|---|
| Singleton (GoF `instance()`) | Anti-idiomatic | Module-level global object; `__new__` if forced | BR singleton |
| Abstract Factory | "awkward workaround for lack of first-class functions" | Pass a class or factory callable (`json.loads(parse_float=Decimal)`) | BR abstract-factory |
| Factory Method | "poor fit for Python" | Dependency injection; class-/instance-attribute factory | BR factory-method |
| Builder | Mostly convenience; immutable-pair builder "never necessary" | Keyword args w/ defaults; dataclass + `dataclasses.replace` / `copy.replace` (3.13) `[from memory]` | BR builder |
| Prototype | "isn't necessary" | Pass classes/callables | BR prototype |
| Flyweight | Good fit (interning, caches) | `sys.intern`, `functools.cache` on module functions | BR flyweight |
| Iterator | Built into syntax | Generators, `__iter__`, `itertools` | BR iterator; EP3 Items 24, 43–46 |
| Decorator (GoF) | Useful when wrapping objects you can't subclass; ≠ `@decorator` | Wrapper class / `__getattr__` delegation | BR decorator-pattern |
| Strategy / Command | Classes are ceremony | Pass functions | EP3 Item 48 |
| Visitor / type switch | — | `functools.singledispatch`; `match` with class patterns; polymorphism | EP3 Items 49–50 |
| Sentinel / Null object | Idiomatic | `None`, or unique `object()`; 3.15 `sentinel` builtin | BR sentinel; W315 PEP 661 |
| Template method / deep inheritance | Discouraged | Composition (Adapter/Bridge/Decorator); avoid "subclass explosion" | BR composition-over-inheritance |
| Mixins | Contested: BR "Dodge: Mixins"; EP3 Item 54 "Consider" | Accept small stateless mixins; flag stateful/multi-axis mixins | BR; EP3 |
| Accessors | Anti-idiomatic | Public attributes, then `@property` | EP3 Items 55, 58–59; GSG 3.15 |
| Metaclasses | Power feature | `__init_subclass__`, `__set_name__`, class decorators | EP3 Items 62–66; GSG 2.19 |
| Global mutable state | Avoid | Pass dependencies explicitly | GSG 2.5; BR global-object |

Layering/packaging:
- Package exposes a stable API through `__init__`/`__all__`. Internals take a `_` prefix (EP3 Item 119; P8 Public and Internal Interfaces).
- Give each library one root exception, with subclasses designed for catchers (EP3 Item 121; P8).
- Treat import cycles as an architecture smell. Fix them by moving shared types down a layer, not with local imports (EP3 Item 122; GSG 3.19.14; PYR `reportImportCycles`).
- Keep configuration at the edges: module-scoped deployment config (EP3 Item 120) and `main()` behind a guard (GSG 3.17).
- One class per module is not required. Group related classes and functions (GSG 3.16.2).
- Import style depends on the house: Google prefers absolute module imports (GSG 2.2.4), while Django uses one-dot relative imports for local code (DJS). Follow the project.

## 5. Language-specific smells → refactoring

| Symptom | Refactoring | Source |
|---|---|---|
| `for i in range(len(xs))` | `for x in xs` / `enumerate` / `zip(strict=True)` / `reversed` | RH; EP3 Items 17–18 |
| `if k not in d: d[k] = 0; d[k] += 1` | `d.get(k, 0) + 1`, `defaultdict`, `Counter` | RH; EP3 Items 26–27 |
| `while True: x = f(); if x == s: break` | `iter(partial(f, n), s)` or walrus `while x := f()` | RH; P572 |
| `cmp=` style / custom compare funcs | `key=` | RH; EP3 Item 100 |
| `found` flag loops | `for … else` or `next((…), default)`/`any()` | RH; EP3 Item 23 |
| Indexing tuples `t[0], t[1]` | Unpacking; catch-all `first, *rest` | EP3 Items 5, 16 |
| Return 4+ values as tuple | Dataclass / NamedTuple result object | EP3 Item 31 |
| Nested dict-of-dict-of-list state | Small classes/dataclasses | EP3 Item 29 |
| `isinstance` switch for behavior | Methods / `singledispatch` / `match` | EP3 Items 49–50 |
| Getter/setter methods | Public attribute → `@property` when needed | EP3 Items 58–59 |
| Singleton class / factory classes | Module global / pass callable | BR |
| Metaclass for registration/validation | `__init_subclass__` | EP3 Items 62–63 |
| Repeated try/finally | `@contextlib.contextmanager` | EP3 Item 82 |
| `try` around many lines | Shrink to the raising call + `else:` | P8; EP3 Item 83 |
| `raise NewError(...)` in except (no chain) | `raise NewError(...) from err` | P8; P3134 |
| `return None` on failure | Raise; document in docstring | EP3 Item 32 |
| `def f(a, b, flag=False)` called `f(1, 2, True)` | Keyword-only `*, flag=False` | EP3 Item 37 |
| `x = lambda …` | `def` | P8 |
| Comprehension with multiple `for`/`if` | Helper generator or loop | GSG 2.7.4; EP3 Item 41 |
| Return list from big producer | Generator | EP3 Item 43 |
| Thread per task / unbounded threads | `ThreadPoolExecutor`; asyncio `TaskGroup` | EP3 Item 74; AIO |
| `asyncio.gather` of owned subtasks | `async with asyncio.TaskGroup()` | AIO |
| Function-level imports for startup | `lazy import` (3.15+) | W315 |
| `_MISSING = object()` sentinels | `sentinel` builtin (3.15+) | W315 |
| `MappingProxyType` / defensive dict copies | `frozendict` (3.15+) | W315 |
| `itertools.chain.from_iterable(...)` in comprehensions | `[*xs for xs in seqs]` (3.15+) | W315 PEP 798 |
| `TypeVar` + `Generic[T]`, `TypeAlias` | PEP 695 syntax (3.12+) | P695 |
| Quoted forward refs / `from __future__ import annotations` for forward refs | Unquoted (3.14+ deferred annotations) | W314 PEP 649/749 |
| `TypeGuard` narrowing | `TypeIs` (3.13+) | P742 |

### Version-gated modernization (flag only if `requires-python` ≥ version)

| Min version | Prefer | Over | Source |
|---|---|---|---|
| 3.9 | `list[int]`, `dict[str, X]`; `str.removeprefix` | `typing.List`; slice-prefix | PTY (585); FURB188 |
| 3.10 | `X | Y`, `X | None`; `match`; `zip(strict=True)`; ParamSpec | `Union/Optional`; long if-chains on structure | PTY (604, 612); B905 |
| 3.11 | `Self`; `asyncio.TaskGroup`; TypeVarTuple; `dataclass_transform` | custom self-TypeVar; `gather` | PYI019; AIO; PTY (646, 681) |
| 3.12 | `class C[T]`, `def f[T]`, `type Alias = …`; `@override` | `Generic[T]`, `TypeAlias` | P695; P698 |
| 3.13 | `TypeIs`; `warnings.deprecated`; TypeVar defaults; `ReadOnly` TypedDict items | `TypeGuard`; ad-hoc deprecation | W313 (PEPs 702, 696, 705, 742) |
| 3.14 | Unquoted forward refs; `annotationlib`; t-strings for safe interpolation; `except A, B:` without parens; `concurrent.interpreters`; `compression.zstd` | string annotations; f-strings into SQL/HTML | W314 (PEPs 649/749, 750, 758, 734, 784) |
| 3.15 | `lazy import`; `frozendict`; `sentinel`; `*`/`**` unpacking in comprehensions; TypedDict `extra_items`; `TypeForm`; `profiling.sampling` | local imports; `object()` sentinels; `chain.from_iterable` | W315 (PEPs 810, 814, 661, 798, 728, 747, 799) |

Note: 3.15 makes UTF-8 the default encoding (PEP 686, W315). Code supporting <3.15 still needs `encoding=` (PLW1514).

## 6. How the community reviews

| Project | Practice | Source |
|---|---|---|
| CPython | Follow PEP 8 for Python and PEP 7 for C. "One or two discrepancies" get fixed by the core dev who merges. "Systematic deviations" put the PR on hold. | DEVPR |
| CPython | "Pull requests with only code formatting changes are usually rejected." Typo and docstring grammar fixes are welcome. | DEVPR |
| CPython | Backwards compatibility: "you need to have a good reason to make a change". New arguments must be optional, with defaults that keep existing behavior (PEP 387). | DEVPR |
| CPython | PRs are "not accepted without the proper tests". The full suite must pass. Keep PRs focused and small. Include docs. | DEVPR |
| CPython | Before merging: is issue discussion resolved, right branch, CI green, compatibility checked, docs updated, backport labels set, CLA signed, NEWS/What's New entries written? | DEVC |
| CPython | NEWS entry: 1–2 sentences, imperative verb ("Fix/Add/Remove…"), user-visible effect, no implementation details. | DEVPR |
| CPython | Don't force-push during review, because reviewers read individual commits. Merges are squashes. | DEVPR |
| Django | black + flake8 + isort via pre-commit, so reviewers focus on the change itself. | DJS |
| Django | "Final judgments of readability are left to the Merger's discretion." f-strings may only hold plain variable or attribute access. Don't use f-strings for translatable or log messages. | DJS |
| Django | "Don't waste time doing unrelated refactoring of existing code to adjust the formatting method." | DJS |
| Django | Patch review checklist: a regression test that fails before the fix, tests that exercise all new code, a release note, `versionadded`/`versionchanged`, a clean docs build, no spelling errors. | DJP |
| Google | Run pylint with the shared pylintrc. Write suppressions as `# pylint: disable=<symbol>` and explain them when the symbol name isn't clear. Delete unused args with `del x  # Unused.` | GSG 2.1 |
| Google | Formatting is delegated to Black/Pyink "to avoid arguing over formatting". | GSG §1 |

Comment conventions: the `Nit:` prefix and generic review etiquette are covered elsewhere (Google eng-practices). No Python-specific comment-prefix convention was found in the CPython or Django docs (see Gaps).

## 7. Severity guidance

**Block** (correctness, data loss, security, API contract):
- Exceptions swallowed with no logging or re-raise. `except BaseException`. `return`/`break` in `finally` (P8, P765).
- A resource that can leak on an error path. A generator holding a resource with no owner-side cleanup (GSG 3.11, EP3 Item 89).
- Shared mutable state across threads without a lock. Treat this as higher risk on free-threaded builds (GSG 2.18, P779).
- Dangling `create_task` with no reference kept. Blocking calls inside `async def` (AIO).
- `assert` used for input validation (GSG 2.4.4).
- Security: `eval`/`exec`, untrusted pickle or yaml, `shell=True` with input, SQL built from strings, `random` for secrets, `verify=False` (S rules, EP3 Item 91).
- A public API break with no deprecation path. Public API without types in a codebase that type-checks (DEVPR, GSG 2.21.4).
- A bug fix without a regression test (DEVPR, DJP).
- A mutable default or class attribute that leaks state between calls when no linter catches it (B006, RUF012).
- Exception translated so the cause is lost (`from None` with no details copied into the new message) at an operational boundary (P8).

**Should-fix** (design; the reviewer argues it, the author may push back):
- Exception hierarchy designed around raise sites. No root exception in a library.
- `try` blocks too broad. Union returns. `Any` where `object` fits.
- Leaking mutable internals. Positional boolean flags. Tuple results with more than 3 elements.
- Singleton or factory classes. Metaclasses where `__init_subclass__` works.
- Import-time I/O. Import cycles. Missing `@override` in strict-typed code.

**`Nit:`** (style and taste; never blocking):
- Walrus vs a plain statement. Comprehension vs loop. `for`/`else` usage.
- Ternary vs `if`. Choice of formatting method (Django: don't refactor it). Docstring wording.
- `len(seq)` vs truthiness. `dict.get` vs `in`.
- Modernization the target version allows but the PR doesn't touch.

**Silent:**
- Anything an enabled formatter or linter rule covers. A style-only refactor of untouched code (DEVPR, DJS).
- Modern-syntax suggestions above `requires-python`.
- P8's "Foolish Consistency" exceptions: local consistency wins, and don't break compatibility just to comply (P8).

## 8. Gaps

- PEPs 343, 484, 526, 634–636 and 3107 were not opened. Statements about them are `[from memory]`. PEP 703 was checked only through P779 and W313.
- PTY versions come from PEP headers via grep. The text of PEPs 544, 593, 612, 646 and 681 was not read in depth.
- The Hettinger material is a third-party transcript of a 2013 Python 2 talk. It uses `xrange`/`izip`, so its idioms were translated to Python 3 in this doc.
- Effective Python 3e: only item headings were read, not the bodies.
- python-patterns.guide was last updated in 2020. The Composite page verdict was not read.
- The pyright strict-mode rule table was not read (only the config option list). The mypy `--strict` list comes from the "as of mypy 1.0" config. The mypy `explicit-override` code is `[from memory]`.
- No CPython or Django source defines a `Nit:` or severity-prefix convention.
- Not covered: Astral `ty`, Meta `pyrefly` (mentioned in GSG 3.19.7), pylint-only checks, Hypothesis/property-testing norms, packaging (PEP 517/621, `py.typed`), the NumPy/SciPy docstring standard.
- `copy.replace` (3.13) and `itertools.batched` (3.12) are `[from memory]`.