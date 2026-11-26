---
id: R20
title: Never name a variable or attribute data or contents
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler: Rename Variable, Google Python Style Guide 3.16 Naming, PEP 8 Naming Conventions
---
## Rule

- No variable named `data`. (C1)
- No variable named `contents`. (C2)
- No attribute named `data` or `contents`. (C3)
- A name says what the value is (a ledger, a reading, parsed state), not "what the file contains". (C4)

## Incorrect

- `data = json.load(fh)` for a parsed ledger; `contents = path.read_text()` for a recipe card.
- `for data in batches:` loop target; `with open(p) as contents:` handle.
- `self.data = {...}` attribute and a class-level field `contents: list[str]`.
- `payload = json.loads(body)`: another name that says what the file holds, not what it is (model only).

## Correct

- `ledger = json.load(fh)`, `card_text = path.read_text()`, `self.ingredients = …`.
- Look-alikes: a keyword argument `data=` to a third-party call, attribute *reads* like `response.data`, names that
  merely contain the word (`metadata`, `table_of_contents`).

## Detection

`check.py` reports every binding of the exact name `data` or `contents`: assignment, annotated or augmented
assignment, `for`/`with`/walrus/comprehension target, `except … as`, and every store to an attribute with that name
(`self.data = …`). Class-body fields count as bindings. Function parameters and keyword arguments are not reported
(they are often forced by a caller or framework signature). Covers C1, C2, C3.

## LLM scan

Look for other names that describe the container instead of the value (C4): `payload`, `content`, `body`, `blob`,
`raw`, `result`, `info`, `obj`, `stuff`, and parameters named `data`/`contents` in signatures the project owns.
Flag them and propose a name that says what the value is (`ledger`, `forecast`, `recipe_card`). Do not flag a name
that is forced by a third-party API (a keyword argument, an overridden method's parameter) or a well-established
domain term (`request.body` of an HTTP framework).
