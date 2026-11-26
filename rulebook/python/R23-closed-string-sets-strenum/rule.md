---
id: R23
title: A fixed, closed set of related string constants is a str enum
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs enum.StrEnum, PEP 435, Fowler: Replace Type Code with Subclasses / Replace Primitive with Object
---
## Rule

- A fixed, closed set of related string constants is a `str`-based enum (`enum.StrEnum`, or `class X(str, Enum)`), not bare module-level string constants. (C1)
- Siblings of the set that the code implies but never names (e.g. a second kind that only exists in an `else` branch) are named as members too. (C2)
- Rationale: members are still `str` at runtime, so existing `str`-typed signatures and comparisons keep working while the enum is introduced. (C3)

## Incorrect

- `FORMAT_HARDCOVER = "hardcover"`, `FORMAT_PAPERBACK = "paperback"`, `FORMAT_EBOOK = "ebook"` as bare constants.
- `DAILY_REPORT = "daily"`, `WEEKLY_REPORT = "weekly"`: the shared part is a suffix.
- A lone `AUDIO_MEDIUM = "audio"` whose implied sibling only appears as an unnamed `else` branch (model only).
- Status values compared as raw literals, `status == "lost"` / `status == "returned"` (model only).

## Correct

- `class BookFormat(StrEnum)` with `HARDCOVER = auto()`, `PAPERBACK`, `EBOOK`; `class Medium(StrEnum)` naming both
  kinds (`auto()` yields the lower-cased member name, so the runtime strings are unchanged).
- Look-alikes: a single unrelated setting `CACHE_DIR = "cache"`, `API_VERSION = "v2"`, a constant whose value is not
  part of its name.

## Detection

`check.py` reports module-level `NAME = "value"` assignments where the value is a short lower-case word and the
name is `<GROUP>_<VALUE>` or `<VALUE>_<GROUP>` (value upper-cased, `-` read as `_`), when two or more such constants
in the same module share the same `<GROUP>` part and position. One hit per constant. Covers the definite shape of C1.
C3 is a rationale and needs no check.

## LLM scan

Find closed sets the naming pattern misses (C1): string constants that are related by meaning but not by name,
string literals compared repeatedly against one variable (`kind == "lost"`, `kind == "returned"`), `Literal[...]`
unions duplicated across signatures, and single constants whose sibling is implied by an `else`/default branch (C2).
Propose a `StrEnum` naming every member, including the implied ones. Do not flag open-ended values (user input,
identifiers, file names, settings), or single constants that are not one of a set.
