---
id: R82
title: A string literal after a statement is dead documentation, not a docstring
tier: ast
severity: should-fix
status: ok
refs: PEP 257 (Docstring Conventions), Python docs Glossary "docstring", pydantic docs Fields (description), Python docs enum
---
## Rule

- A bare string literal at statement position that is not the first statement of a module, class, or function is a violation; no exception. (C1)
- Delete such a string (e.g. one after an assignment), or move its fact where a machine reads it. (C2)
- For a model field, the fact goes in the field's own `description=`. (C3)
- For an enum member, the fact goes in a class docstring listing the members' meanings, or in the member name itself. (C4)
- For a module constant, the fact goes in its own name, or in `Annotated[str, Field(description=...)]` when it is data. (C5)
- For a class attribute that needs prose, the fact goes in the class docstring. (C6)

## Incorrect

- A module constant followed by a bare triple-quoted string explaining it.
- An enum member followed by a bare string describing it.
- A model field followed by a bare string instead of `description=`.
- A bare string as the first statement of an `if` block, and a bare f-string inside a function body.
- An f-string as the first statement of a function (Python attaches no docstring for an f-string).

## Correct

- Constants named for their meaning, an enum whose class docstring lists member meanings, a model field with `description=`, a class docstring for attribute prose.
- Look-alikes: module, class, function and async-function docstrings; a string used as a value (assigned, returned, passed).

## Detection

`check.py` reports every expression statement that is a string literal or f-string and is not a docstring: a plain
string that is the first statement of a module, class, `def` or `async def` body. It reports first statements of
`if`/`for`/`while`/`with`/`try` blocks and f-strings in any position, the first statement of a function included
(C1). The remedies C2–C6 are what the message asks for; any reported string violates C2 until it is deleted or moved,
so no clause needs judgement.
