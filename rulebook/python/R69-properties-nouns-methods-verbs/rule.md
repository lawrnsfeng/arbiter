---
id: R69
title: Property names are nouns; method names are verbs
tier: ast+semantic
severity: should-fix
status: ok
refs: https://peps.python.org/pep-0008/#naming-conventions, Google Python Style Guide 3.16 (Naming), https://docs.python.org/3/library/functions.html#property, owner convention
---
## Rule

- A property's name is a noun naming the thing it derives. (C1)
- A method's name is a verb naming the action it performs. (C2)
- A method named with a participle, adjective or noun form (e.g. `normalized`) is a violation; use the verb (`normalize`). (C3)
- A property named with a verb (e.g. `render`, `get_label`) is a violation; rename it to the noun it derives (e.g. `label`, `text`). (C4)

## Incorrect

- `@property def calculate_area(self)`: verb-named property.
- `@cached_property def get_label(self)`: `get_` property.
- `@property def fetch(self)`: bare verb property.
- `def normalized(self)` and `def sorted_by_due(self, ...)`: participle-named methods.
- (LLM) `def summary(self)`: a noun-named plain method (should be a property, or a verb like `summarize`).

## Correct

- `@property def area(self)`, `@property def label(self)`, `def normalize(self)`, `def sort_by_due(self)`.
- Look-alikes: noun properties whose first word is also a verb (`run_id`, `check_digit`, `format`), methods named `embed`, `proceed` or `shred` (verbs ending in `ed`), a `@label.setter`, and dunder methods.

## Detection

Reports a `@property` / `@cached_property` whose name (leading underscores stripped) starts with an action verb that is never a noun modifier (`render`, `compute`, `calculate`, `fetch`, `get`, `make`, `create`, `parse`, `convert`, `generate`, `validate`, `resolve`, `collect`, `execute`, `normalize`, `serialize`, `extract`), or is exactly one of `apply`, `send`, `save`, `build`, `load`, `run`, `process`, `check` (as prefixes these form nouns: `run_id`, `check_digit`) (C1, C4). Reports a non-property, non-dunder method in a class whose first name word (snake or camel case) ends in `ed`, is at least six letters, and does not end in `eed` (`proceed`, `succeed`), so `normalized` and `sorted_by_due` are reported and `shred`, `embed` are not (C2, C3).

## LLM scan

- Flag methods named as nouns or adjectives without the `-ed` ending (`def summary(self)`, `def total(self)`, `def valid(self)`) that should be a verb or a property (C2, C3).
- Flag properties named with verbs outside the detector's list (C1, C4).
- Judge boolean-predicate properties (`is_*`, `has_*`) against C1 like any other property: the name must state the thing derived; do not exempt them by prefix.
- Do not flag names a framework or protocol dictates (`def save(self)` on an ORM model, `def get(self, request)` on a view, `keys()`/`items()` on mappings).
