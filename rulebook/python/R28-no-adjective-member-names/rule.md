---
id: R28
title: Method and property names are verbs or nouns, never bare adjectives
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler: Rename Function, PEP 8 Naming Conventions, Google Python Style Guide 3.16 Naming
---
## Rule

- A method name is a verb (or a noun), never a bare adjective or past participle (e.g. `reconnected`). (C1)
- A property name is a noun (or a verb), never a bare adjective. (C2)
- Rationale: an adjective reads as a description of state, while the member does work. (C3)

## Incorrect

- `def compacted(self, year)` that drops volumes in place.
- `def shuffled(self, count)` and `def _indexed(self)` that build and return new values.
- `def finished(self) -> bool`: a bare adjective even for a yes/no answer; name it `is_finished`.
- A `@property def stale(self)` that queries the remote catalogue (model only).

## Correct

- `compact(year)`, `sample(count)`, `@property def volumes_by_isbn`, `@property def is_finished`,
  `@property def staleness(self)`.
- Look-alikes: multi-word names such as `mark_returned`, verbs that happen to end in "ed" (`embed`, `proceed`), and a
  module-level function (not a member).

## Detection

`check.py` reports methods (functions defined directly in a class body, not properties, not dunders) whose name,
leading underscores stripped, is a single lower-case word of five or more letters ending in `ed` (not `eed`, not a
listed verb or noun such as `embed`, `shred`, `hundred`). Boolean predicates are reported too: C1 has no predicate
exception, the fix there is an `is_`/`has_` name. Covers the past-participle subset of C1.

## LLM scan

Look at method and property names the detector does not cover: other adjectives (`ready`, `active`, `fresh`,
`stale`, `empty`, `valid`), multi-word names ending in an adjective or participle (`cache_cleared`), and properties
(C2). Flag one when the member does work (I/O, construction of a new object, mutation, an expensive computation) and
propose a verb or noun (C3). For a property or method that only reports a boolean state, propose an `is_`/`has_`
predicate rather than leaving the bare adjective. Do not flag names forced by a protocol or third-party base class
(e.g. `io.IOBase.closed`, `readable`) and say so when you skip one.
