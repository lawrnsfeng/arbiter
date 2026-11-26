---
id: R56
title: Every member of a paths-providing class shows an example path in its docstring
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 257, XDG Base Directory Specification
---
## Rule

- Every member of a class that provides paths has a docstring. (C1)
- That docstring shows one concrete, full example or default path (e.g. "(e.g. ~/.local/state/<pkg>/server.log)"), not only the name of the concept; the XDG base directories are stable enough to show. (C2)

## Incorrect

- A `Final[Path]` attribute whose line in the class docstring only names the concept.
- A `Path`-built class attribute the class docstring never mentions.
- A `Path` property whose docstring only names the concept.
- A `Path`-returning method with no docstring.
- A directory-creating method of the same class with no docstring.
- A class of unannotated `os.path.join` methods with concept-only docstrings (model only).

## Correct

- Each method's docstring, and each class attribute's line in the class docstring, shows a full example path: `~/…`, `$XDG_…/…`, in backticks or after "e.g.".
- A directory-creating method of the class whose docstring also shows the path it creates.
- A dataclass record with two `Path` fields per instance, which is not a paths-providing class.
- A class with a single path member, which is not a paths-providing class.

## Detection

Covers C1 and C2 for classes the detector can recognise as paths-providing: classes providing at least two paths,
where a provided path is a method or property annotated to return `Path` (also `Path | None`, `Final[Path]`, ...), or
a class attribute with a value that is annotated `Path` or calls `Path(...)` / `Path.home()`. In data records
(dataclasses, attrs classes, `NamedTuple`, `TypedDict`, pydantic models) annotated attributes are per-instance fields
and count only when declared `ClassVar`/`Final`. In such a class, reports every non-dunder method and class attribute
with no documentation (C1) — a method's own docstring; for a class attribute, the lines of the class docstring that
name it (a bare string after an assignment is not a docstring) — and every one whose documentation holds no token with at least two path separators starting at `/`, `~`, `$VAR`, `<placeholder>`, a drive or
a dot (C2).

## LLM scan

Beyond the detector: find classes whose job is to provide paths but whose members are not annotated as `Path`
(string paths built with `os.path.join`, f-strings, or settings lookups), and apply C1 and C2 to every member of
them. Also judge whether a detected example is concrete: a docstring path made only of placeholders (`<dir>/<file>`)
does not show the layout. Dunder methods of a paths-providing class also need a docstring with an example path when
they produce or accept a path. Do not flag data records that merely hold paths per instance, or classes that hold one
path among other data.
