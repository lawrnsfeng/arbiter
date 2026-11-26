---
id: R51
title: No personal names anywhere in code, comments, or tests
tier: semantic
severity: should-fix
status: ok
refs: owner convention
---
## Rule

- No real person's name appears in code: identifiers, string literals, default values. (C1)
- No real person's name appears in comments or docstrings. (C2)
- No real person's name appears in tests or fixtures. (C3)
- Examples, fixtures, and principal or sample values use generic identities such as `user`, `tester`, `alice` / `bob`. (C4)
- Exception: functional values that genuinely contain an account string, such as a git remote read from the real configuration, are allowed. (C5)

## Incorrect

- A module `__author__` naming a real person.
- A seed fixture row whose holder is a real person's full name.
- A comment telling the reader to ask a named colleague, using a generic-looking first name that identifies a real person.
- A test function named after a real person.

## Correct

- Seed rows with generic identities (`alice`, `bob`) used as placeholders.
- A comment naming the role (the circulation desk), not a person.
- A test named for the behaviour, not a person.
- A git remote URL read from the real configuration at run time (functional value, exempt).
- An algorithm named after a person, used as a technical term.

## LLM scan

Read every identifier, string literal, comment, docstring, test and fixture. Report each place a real person's name
or personal handle appears: a full name, a first name used to identify someone (a colleague, reviewer, author,
customer), a personal e-mail local part or username (C1–C3). A generic identity (`alice`, `bob`, `user`, `tester`)
is only generic when it is a placeholder; when the context shows it points at a real individual (credit, ownership,
"ask X", "X approved", a contact, a real colleague's principal), report it like any other name. Suggest a generic
identity or a role in its place (C4). Do not flag: generic identities used as placeholders in examples, fixtures and
sample values; names of libraries, products or algorithms that happen to be surnames (`Dijkstra`, `Gaussian`,
`Levenshtein`) when used as technical terms; licence and copyright headers required by a third-party licence; values
read at run time from real configuration or the environment, such as a git remote or the current account (C5).
