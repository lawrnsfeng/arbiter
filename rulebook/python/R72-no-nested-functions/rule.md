---
id: R72
title: Never define a function inside a function
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/functools.html#functools.partial, https://docs.python.org/3/reference/executionmodel.html#resolution-of-names, Google Python Style Guide 2.6 (Nested/Local/Inner Classes and Functions), Fowler Refactoring "Move Function" / "Replace Function with Command", owner convention
---
## Rule

- A `def` or `async def` inside another function is prohibited by default: it has no name a reader can find, no type to belong to, and no test that reaches it directly. (C1)
- A closure capturing locals becomes a class (e.g. a bound logger, a small strategy object) or a method on the class that owns those locals. (C2)
- A one-off callback becomes `functools.partial`, a bound method, or a named callable at module scope. (C3)
- A helper used twice is never a closure. (C4)
- Exception condition 1: the nested function reads or writes a name that exists only in the enclosing scope (a captured local, parameter, or `self`), so it cannot move to module scope or onto another class unchanged. (C5)
- Exception condition 2: no object can carry that state instead: not a `functools.partial` of an existing callable, not a bound method of an existing class, not a `@dataclass`/`Protocol` instance holding the captured values with the body as its method. (C6)
- Exception condition 3: the consumer requires a callable object rather than an instance (a decorator factory returning its wrapper, a dependency factory handing a router a callable, a callback registered with a third-party API). (C7)
- Exception condition 4: the nested function's docstring states what it captures and why no object can hold it. (C8)
- All four exception conditions must hold; if any one fails, the nesting is a finding. (C9)
- "The framework wants a closure" alone is not sufficient for the exception. (C10)
- Only decorator-factory and framework-callback cases genuinely qualify, and even they carry the docstring; the exception is a claim a reviewer can check. (C11)
- A nested `def` that captures only names it could take as parameters is a violation; fix it as a module-level function taking them explicitly. (C12)
- A nested `def` whose body is reachable as a method of an object built from the captured names is a violation; fix it as that object. (C13)
- Every nested `def` a change adds is listed by a mechanical scan; an exception the scan cannot verify counts as a finding, not a pass. (C14)

## Incorrect

- A nested `score(book)` capturing `prefs`, handed to `sorted(key=...)` once, with no docstring.
- A nested `fmt(reading)` that captures nothing from the enclosing function.
- A nested helper called twice in the enclosing function and never handed out.
- A nested helper with a docstring and captures that is registered as a callback once but also called directly twice (a helper used twice).
- A nested sort key handed to `items.sort(key=key)` once and then called directly once more (`return key(items[0])`): two uses.
- A nested helper decorated with `@functools.lru_cache(...)`: a cache decorator does not hand the function out, and it is called twice.
- A decorator factory whose inner `wrapper` captures `times` and is returned, but has no docstring.
- (LLM) A nested `async def` with a docstring, captured state and a framework registration, whose state could be held by a small dataclass with the body as a method.

## Correct

- `PreferenceRanker(prefs).score`: the captured preferences become a small frozen dataclass and its bound method is the sort key.
- A module-level `format_reading(reading, unit)` taking its inputs explicitly.
- A decorator factory `retry(times)` whose `wrapper` is returned, captures `times`, and has a docstring naming the capture and why no object can hold it.

## Detection

Reports every `def`/`async def` directly inside a function body (not inside a nested class) unless all of these syntactic conditions hold: it has a docstring (C8); it reads, writes or declares `nonlocal` a name bound in the enclosing function: a parameter, an assigned local, or a sibling definition (C5); it is handed out as a callable: returned by name, passed by name as a call argument, or decorated by a call or attribute decorator other than a cache (`cache`, `lru_cache`, `cached_property`), such as `@functools.wraps(fn)` or `@router.get(...)` (C7); and its name is read at most once in the enclosing body, counting calls, arguments, returns and assignments alike (C4: a helper used twice, in any mix of calls and hand-outs). A nested function that captures names but is only called directly is reported as capturing names it could take as parameters (C12). The message names each failed condition. Covers C1, C4 (uses visible as the name inside the enclosing body), C5, C7, C9, C12, C14 and the presence half of C8.

## LLM scan

- For nested functions the detector lets through, read the docstring: it must name the captured names and say why no object can hold them; a generic docstring is a finding (C8, C11).
- Check no `functools.partial`, bound method, or dataclass/`Protocol` instance could carry the captured state instead (C2, C3, C6, C13).
- Treat "the framework wants a closure" with no stronger reason as a finding (C10); only decorator factories and framework callbacks qualify (C11).
- For nested functions the detector lets through, check they are not a helper used more than once in ways the name count cannot see: stored once in a container that is then called from several places, or reused through an alias (C4).
- For each nested function, check whether every captured name could simply be passed as an argument to a module-level function; if so, it is a finding even when the function is handed out (C12).
- Do not flag lambdas or nested classes under this rule.
