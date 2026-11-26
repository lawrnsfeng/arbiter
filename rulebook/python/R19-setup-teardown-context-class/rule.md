---
id: R19
title: Paired setup/teardown resources are a context-manager class
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 343, Python docs: Context Manager Types (object.__enter__/__exit__), Python docs contextlib.contextmanager, Fowler: Combine Functions into Class
---
## Rule

- A resource with paired setup and teardown is a context-manager class with `__enter__` / `__exit__`. (C1)
- If the callers of a `@contextlib.contextmanager` generator each re-implement the same steps around the `yield` (e.g. seek, read, parse the yielded handle), those steps move into a class. (C2)
- In that class, `__enter__` does the setup (and the shared reads), named methods do the operations (e.g. `.save(...)`), and `__exit__` does the teardown. (C3)

## Incorrect

- `@contextmanager` `claimed_printer()` yielding a device; two callers each `reset()` then `select_tray(...)`.
- `@contextmanager` `scratch_kitchen()` yielding a temp dir; two callers each `shutil.copytree(...)` then `os.chdir(...)` it.
- A function that pairs `power_on()` with `power_off()` in `try/finally` by hand (model only).

## Correct

- `class PrintJob`: `__enter__` claims, resets and selects the tray; `.print_page(page)` prints; `__exit__` releases.
- Look-alike: a `@contextmanager` timer whose callers do unrelated things inside the `with` block.

## Detection

`check.py` finds every `@contextmanager` / `@asynccontextmanager` function in the scanned code and every
`with <that function>(...) as <name>:` block. For each block it records the first two steps the block takes on the
bound name, in source order: a method call on it (`.seek`) or a call that receives it as an argument
(`json.load()`). When two or more blocks start with the same two steps, it reports the generator's `def` line once.
Covers C2.

## LLM scan

Look for paired setup/teardown that is not a context-manager class (C1): open/close, acquire/release, connect/
disconnect, begin/commit or rollback done by hand in `try/finally`, or a resource object with `open()`/`close()`
methods but no `__enter__`/`__exit__`. Check the detector's hits and any other `@contextmanager` whose callers repeat
work around the yielded value, and propose the class shape of C3. Do not flag a `@contextmanager` whose callers each
do different work with the yielded value, or a one-off generator with a single caller and no repeated steps.
