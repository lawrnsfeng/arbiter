---
id: R4
title: Message templates live in the package's messages module
tier: ast+semantic
severity: should-fix
status: ok
refs: string.Template (https://docs.python.org/3/library/string.html#template-strings), Fowler Refactoring catalog "Replace Magic Literal" (https://refactoring.com/catalog/replaceMagicLiteral.html)
---
## Rule

- Message templates live in the package's `messages.py` module. (C1)
- Exceptions format a template from the messages module rather than building message text themselves. (C2)
- No multi-line message strings (for example a multi-line f-string or a `"\n".join(...)` of lines) are assembled
  inline inside functions or methods. (C3)
- The template is filled in the exception's `__init__`. (C4)

## Incorrect

- A module-level `Template(...)` message constant defined outside the messages module.
- An exception `__init__` passing a three-part, multi-line f-string to `super().__init__`.
- A function joining message lines with `"\n".join` into a local and raising it.
- A triple-quoted multi-line message raised inline.
- A function building a multi-line message for the user and printing it (model only).

## Correct

- Templates imported from the messages module and filled with `substitute` in the exception's `__init__`.
- Look-alikes: multi-line text that is not a message (a rendered recipe card, an SQL query), a docstring, a one-line
  message.

## Detection

`check.py` reports, outside modules named `messages.py`:
- a module-level assignment of a `Template(...)` call or of a string to a name ending in `TEMPLATE` (C1);
- a multi-line message (a string or f-string whose text contains `\n`, or a `"\n".join(...)`; one line wrapped across
  source lines is not multi-line) passed to a raised exception or to `__init__` / `super().__init__` inside a function,
  reported at the call (C2, C3, C4);
- the same built into a local that is later raised or passed to `super().__init__`, reported at the assignment (C3).

## LLM scan

- Report exception constructors that compose their wording themselves (concatenation, several f-strings, conditional
  pieces) instead of filling a template from the messages module (C2, C4).
- Report multi-line user-facing messages (printed, echoed, logged, returned for display) assembled inline in a
  function (C3).
- Report message templates defined anywhere but the messages module, including class attributes that inline the
  wording instead of referring to the messages module (C1).
- Do not flag docstrings, SQL or other non-message multi-line text, or one-line messages written in the call.
