# Python idioms

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

## Community review practice

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
