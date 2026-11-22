# Python severity guidance

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
