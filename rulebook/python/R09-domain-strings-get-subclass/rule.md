---
id: R9
title: Domain strings and bytes get a subclass with a parsing classmethod
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog "Replace Primitive with Object" (https://refactoring.com/catalog/replacePrimitiveWithObject.html), Fowler "Primitive Obsession" code smell (Refactoring 2nd ed., ch. 3), Python docs "Customizing class creation" / subclassing str (https://docs.python.org/3/reference/datamodel.html#object.__new__)
---
## Rule

- When a plain `str` parameter actually means something structured, it gets a named `str` subclass. (C1)
- The same holds for `bytes` parameters: they get a named `bytes` subclass. (C2)
- The subclass is constructed and parsed through a parsing classmethod (for example `from_path`). (C3)
- A free function whose only input is one domain value (for example `def f(code: str)`) is a missing property of
  that subclass and becomes one. (C4)

## Incorrect

- A free function splitting a shelf mark at `/` to read its floor.
- A free function matching an ISBN against a regex to read its group.
- A free function parsing a due-date slip with `strptime`.
- A free function decoding a `bytes` library-card payload with `json.loads`.
- A free function cutting a fixed-position branch code out of a call number.
- Methods of a lending desk that each take `shelf_mark: str` and split it again (model only).

## Correct

- `class ShelfMark(str)` built through a `from_label_file(path)` parsing classmethod that reads its source, with a
  `floor` property; `class CardPayload(bytes)` built through `from_reader(reader)`, with a `member_id` property; each
  class documents a real value in a `>>>` example.
- Look-alikes: generic text utilities (`first_line(text)` via `splitlines`, `words(text)` via whitespace `split()`,
  truncation `blurb[:80]`), and a function formatting (not parsing) a shelf label from two parameters.

## Detection

`check.py` reports an undecorated module-level function with exactly one parameter, annotated `str` or `bytes`, whose
body parses that parameter structurally: `split` / `rsplit` / `partition` / `rpartition` / `removeprefix` /
`removesuffix` with an explicit argument, a fixed-position slice with both bounds (`v[4:7]`), or the parameter passed
to `match` / `fullmatch` / `search` / `findall` / `finditer` / `loads` / `strptime` / `fromisoformat` (C4, and C1 / C2
for that parameter). Generic text handling (`splitlines`, whitespace `split()`, `v[:80]`) does not count.

## LLM scan

- Report `str` / `bytes` parameters across functions and methods that carry a structured value (codes, keys, paths,
  identifiers with parts, encoded payloads) and are parsed or validated in more than one place; suggest a named
  subclass (C1, C2).
- Report domain-string subclasses constructed by ad-hoc parsing at call sites instead of a parsing classmethod (C3).
- Report free functions taking one domain value in shapes the detector misses (unannotated, or with a defaulted
  second parameter) (C4).
- Do not flag functions over genuinely free text (messages, prose, user input before validation), or generic string
  utilities that apply to any text.
