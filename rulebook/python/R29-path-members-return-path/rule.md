---
id: R29
title: A _path member returns a pathlib.Path, never a str
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 519 (os.PathLike), PEP 428 (pathlib), Python docs pathlib, Python docs subprocess (args accept path-like objects)
---
## Rule

- A member (method, property or attribute) whose name ends in `_path` returns or holds a `pathlib.Path`. (C1)
- It never returns or holds a `str`: no f-string, `os.path.join` or string-concatenation path building. (C2)
- Callers that need a `str` convert at the point of use (`str(x_path)`, `os.fspath(x_path)`). (C3)
- Do not convert for `subprocess` argv: it accepts a `Path` directly. (C4)
- A `*_path` member that takes only `self`, reads no variable from an outer scope (an enclosing function, or module-level mutable state) and does no I/O (it only derives a value, e.g. `self.root / "thumbs"`) is a `@property`, not a method; small conflicts with other rules resolve in favour of the property. Imported names, builtins and module-level UPPER_CASE constants are not outer-scope variables. A member that does I/O (creates a directory, makes a temp dir, reads a file) stays a method. (C5, owner ruling)

## Incorrect

- `def thumbnail_path(self) -> str: return f"{self.root}/thumbs/{self.slug}.png"`: a str, and a method instead of a
  property.
- `def export_path(self) -> str: return str(self.root_dir / "export")`: a Path built, then thrown away as text.
- A `cache_path` property built with `os.path.join(...)`; `self.index_path = self.root + "/index.json"`.
- `def archive_path(self)` deriving only from `self` (should be a property); `subprocess.run([str(...), ...])`.
- A `_path` method annotated `-> str` that returns a string from elsewhere (model only).

## Correct

- `@property def thumbnail_path(self) -> Path: return self.root / "thumbs" / f"{self.slug}.png"`; `archive_path` is a
  property reading an imported constant; the attribute holds a `Path`.
- The archive `Path` goes into the subprocess argv unconverted (through the project's command builder);
  `str(path)` only where an API needs text.
- Look-alikes: a local variable `log_path = f"..."` (not a member); route properties `url_path` / `route_path` that
  start with a literal `/` (not filesystem paths); `str(x_path)` in a log message; `page_path(number)` (takes an
  argument) and `mirror_path()` (reads module-level mutable state), which stay methods; `scratch_path()`
  (`tempfile.mkdtemp()`) and `cache_path()` (`.mkdir()` then return), which do I/O and stay methods.

## Detection

`check.py` reports:

- a function or method named `*_path` with a `return` of filesystem-style string building: an `os.path.*` call,
  `str(...)` of a pathlib value (`a / b`, `Path(...)`, a `*_path` / `*_dir` name), an f-string that starts with a
  formatted value and continues with a literal starting with `/` or `\`, or `<value> + "/..."` (C1, C2). Strings
  that start with a literal `/` are treated as routes and left to the model;
- an assignment of the same kinds of value to an attribute or class/module-level name ending in `_path` (C1, C2);
- a `subprocess.run/call/check_call/check_output/Popen` call whose argv list contains `str(...)` or
  `os.fspath(...)` of a `*_path` expression (C4);
- an undecorated method named `*_path`, defined directly in a class, whose only parameter is `self` and whose body
  reads no name other than its own locals, builtins, the module's imports, defs, classes and UPPER_CASE constants,
  and whose every call is a pure builtin (`len`, `str`, ...), a capitalised imported or defined constructor
  (`Path(...)`) or a value method (`.with_suffix()`, `.joinpath()`, `.replace()`, ...): any other call may do I/O,
  so the method is left alone (C5).

## LLM scan

Check `_path` members the detector cannot classify: annotated `-> str`, returning a string from a config value or
another function, `Optional[str]` attributes. Flag them (C1, C2) when they are filesystem paths and propose `Path`.
Flag `str()`/`os.fspath()` conversions done eagerly far from the API that needs text, instead of at the point of use
(C3). Do not flag URL paths or route strings that are not filesystem paths, nor conversions at an API that really
requires `str` (a JSON payload, a log message). For C5, check `*_path` methods the detector skipped because they are
decorated (e.g. `@abstractmethod`, `@cache`) or nested: if they take only `self` and read no outer-scope variable,
propose a property (`functools.cached_property` for a cached one); leave overrides of a third-party method alone.
