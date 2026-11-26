---
id: R3
title: Errors subclass a project base and build their own message in their own constructor
tier: ast+semantic
severity: should-fix
status: ok
refs: Python tutorial "User-defined Exceptions" (https://docs.python.org/3/tutorial/errors.html#user-defined-exceptions), Effective Python 2nd ed. Item 87 "Define a Root Exception to Insulate Callers from APIs", string.Template (https://docs.python.org/3/library/string.html#template-strings), ruff EM101/EM102/TRY003 (https://docs.astral.sh/ruff/rules/raw-string-in-exception/), FastAPI "Handling Errors" (https://fastapi.tiangolo.com/tutorial/handling-errors/)
---
## Rule

- Errors subclass the project's base error class; a builtin such as `RuntimeError` is not raised directly. (C1)
- Never build a message string at the raise site and hand it to the exception (`msg = f"..."; raise SomeError(msg)`);
  the message belongs in the exception's own `__init__`. (C2)
- A name bound to a string and then handed to a `raise` is a violation. (C3)
- Inside `__init__`, building the message into a local and passing that local to `super().__init__`
  (`message = f"..."; super().__init__(message)`) is the same defect moved one frame down, and is not a fix. (C4)
- The message is written directly in the `super().__init__(...)` call (`super().__init__(f"... {value!r}")`), or held
  as a `Template` on the class whose parameters are substituted. (C5)
- Linter rules that flag inline exception-message literals (ruff `EM101`, `EM102`, `TRY003`) are not satisfied by
  introducing a local variable; silence those rules instead. (C6)
- One constructor, one message: an `__init__` does not choose between messages with a flag parameter. (C7)
- An `__init__` does not choose between messages with a `None` default. (C8)
- An `__init__` contains no `if` about which refusal happened, selecting which `super().__init__` runs. (C9)
- Each distinct refusal is its own exception class holding its own text and taking only the values that vary, so a
  caller can catch the cause it means. (C10)
- Target form: each error class declares its wording as a class attribute `TEMPLATE: ClassVar[Template]`, overridden
  per subclass. (C11)
- The hierarchy's base class renders the template once, in its single `__init__`, via
  `type(self).TEMPLATE.substitute(**values)`. (C12)
- A subclass constructor passes only its own values as keywords to `super().__init__` (for example
  `super().__init__(parcel_code=parcel_code)`), never a formatted string. (C13)
- Templates use `string.Template`, never `str.format` / `.format(**values)`: a message may contain a literal brace, on
  which `.format` raises. (C14)
- A leaf exception class that defines `__init__` calls `super().__init__(...)`; a constructor holding only a docstring
  leaves `Exception.args` empty and `str(error)` equal to `""`. (C15)
- A leaf exception with nothing to pass defines no `__init__` at all. (C16)
- A caller-supplied pre-rendered string (for example a validation library's error report) is passed through a `raw=`
  keyword that the base hands to `Exception` untouched, never re-substituted. (C17)
- Repeated HTTP error-response construction (same status, same detail envelope, whether a plain string or
  `{"error": {"code": ..., "message": ...}}`) is the same smell: define a project `HTTPException` subclass that carries
  the status and envelope in its `__init__`. (C18)
- With such a subclass, call sites pass only the varying message or values (`raise Archived(code)`). (C19)
- The HTTP-response clause applies when two or more sites share a status code. (C20)
- The gated shapes are: a name bound to a string and handed to `raise`; the same name handed to `super().__init__`;
  and a branch inside `__init__` selecting which `super().__init__` runs. (C21)

## Incorrect

- A message bound to a local (f-string, concatenation) and then raised with `raise LookupError(missing)`.
- `text = f"..."; super().__init__(text)` inside an exception constructor.
- One error class whose `__init__` takes `hub=None, closed=False` and picks its message with `if` / `elif`.
- A class template rendered with `self.TEMPLATE.format(**values)`.
- A leaf `__init__` holding only a docstring, and a leaf `__init__(self)` that only calls `super().__init__()`.
- `HTTPException(410, ...)` built at two sites: in a lookup loop, and with a hand-built error envelope in an `except`.
- Builtins raised directly: `raise RuntimeError("...")` and a bare `raise ConnectionError`.
- An error class deriving straight from `ValueError` although the project has a base error class (model only).

## Correct

- A base error rendering `type(self).TEMPLATE.substitute(**values)` once, with a `raw=` pass-through; leaves with
  their own `Template` and keyword values; a leaf with nothing to pass and no `__init__`.
- A second hierarchy whose leaf writes `super().__init__(f"... {value!r}")` directly in the call.
- An `Archived(HTTPException)` subclass owning the 410 status and the envelope, raised as `raise Archived(code)`.
- Look-alikes: a string bound to a name and printed, `raise err` of a caught error, a single `HTTPException` site for a
  status code, a conditional expression in the base's `raw=` pass-through, a `retryable=False` keyword stored on the
  error without choosing its message.

## Detection

`check.py` treats as an exception class every class whose base ends in `Error` / `Exception` / `Warning`, is a builtin
exception, or is (transitively) such a class anywhere in the scanned modules. It reports:
- a `raise` of a builtin exception class, called or bare (`raise RuntimeError(...)`, `raise ConnectionError`), unless
  the scanned modules define a class of that name; `NotImplementedError` (abstract stubs) and control-flow exceptions
  (`StopIteration`, `SystemExit`, `KeyboardInterrupt`, ...) are not refusals and are skipped (C1);
- a `raise X(name)` whose positional argument is a local previously bound to a string literal, f-string, `+` / `%`
  string expression, `.format(...)` or `.join(...)` (C2, C3, C6, C21);
- in an exception class `__init__`, a `super().__init__(name)` / `Base.__init__(self, name)` whose argument is such a
  local (C4, C21);
- in an exception class `__init__`, every `super().__init__` call nested in an `if` statement (C9, C21), and the
  `__init__` itself when a parameter defaulting to `True` / `False` is tested by such an `if` (C7);
- any `.format(...)` call inside an exception class (C14);
- an exception class `__init__` that never calls `super().__init__` / `Base.__init__` (C15);
- an exception class `__init__` taking only `self` whose `super().__init__()` call passes nothing (C16);
- every `HTTPException(...)` construction whose status code (the `status_code=` keyword or first positional int) is
  shared with another construction in the scanned modules (C18, C20).

## LLM scan

- Report error classes that derive straight from a builtin when the project has a base error class, and builtins
  raised through an alias or a variable the detector cannot resolve (C1).
- Report one class serving several distinct refusals (a `None` default or a conditional expression choosing the
  text, a `reason` string parameter), and suggest one class per refusal (C8, C10).
- Where the hierarchy uses templates, report subclasses that pass a formatted string to `super().__init__` instead of
  keyword values, a base that renders anything but `type(self).TEMPLATE.substitute(**values)`, and a template not
  declared as a `ClassVar[Template]` (C5, C11, C12, C13).
- Report pre-rendered text (validation reports, upstream messages) pushed through template substitution instead of a
  `raw=` pass-through (C17).
- Report `# noqa: EM101` / `EM102` / `TRY003` paired with a message local (C6) and HTTP error responses repeated through
  helper functions or `JSONResponse(status_code=...)` (C18, C19, C20).
- Do not flag `raise` of a caught exception object, `super().__init__(f"...")` written in the call, or the base's
  `raw=` conditional pass-through.
