---
id: R10
title: Structured records are dataclasses, not raw dicts or TypedDicts
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 557 Data Classes (https://peps.python.org/pep-0557/), Python docs dataclasses (https://docs.python.org/3/library/dataclasses.html), Effective Python 2nd ed. Item 37 "Compose Classes Instead of Nesting Many Levels of Built-in Types", Fowler Refactoring catalog "Encapsulate Record" (https://refactoring.com/catalog/encapsulateRecord.html)
---
## Rule

- Structured records are `@dataclass` classes. (C1)
- Not raw `dict` aliases such as `Row = dict[str, object]`. (C2)
- Not `TypedDict`. (C3)
- Functions do not return ad-hoc dict literals with fixed, known keys as records; they return a (frozen) dataclass,
  with an explicit conversion method (for example `.as_dict()`) where a dict is needed. (C4)

## Incorrect

- A module-level alias `Reading = dict[str, float | str]` and a `type Forecast = Mapping[str, object]` alias.
- A `TypedDict` class and a functional `TypedDict("...", {...})` record.
- A function returning `{"station": ..., "celsius": ..., "taken_at": ...}`.
- A record passed around as a tuple indexed by position (model only).

## Correct

- `@dataclass(frozen=True) class Reading`, built by a `Reading.from_sensor(...)` classmethod, with `as_dict()` and
  `to_row()` conversion methods used where a dict is needed.
- Look-alikes: a dict comprehension, a dict literal with computed keys, a dict merged with `**`, a one-key dict, a
  local dict that is not returned, a `dict[str, Reading]` annotation on a parameter, a lookup-map alias
  `ByStation = dict[str, Reading]`.

## Detection

`check.py` reports:
- a module-level alias (`X = ...`, `X: TypeAlias = ...`, `type X = ...`) whose value is a `dict` / `Dict` / `Mapping` /
  `MutableMapping` with `str` keys and a loose value type (`object`, `Any`, or a union), the shape of a record's mixed
  fields (C2); an alias with a single concrete value type (`dict[str, Book]`) is a lookup map and is left to the model;
- a class deriving from `TypedDict`, and a `TypedDict(...)` call (C3);
- a `return` of a dict literal with two or more keys, all string literals, inside a function, except inside a
  conversion method (`to_*`, `as_*`, `asdict`, `dict`, `_asdict`) or a method whose name several scanned classes define
  (a framework contract such as a serializer hook) (C4).

## LLM scan

- Report records modelled as tuples, `namedtuple`s, lists indexed by position or plain classes with only `__init__`
  assignments, where a dataclass fits (C1).
- Report dicts with fixed keys built step by step and returned or passed on as a record (C4), and aliases or
  parameters typed as `dict[str, ...]` that always carry the same keys, whatever the value type (C2).
- Do not flag dicts whose keys are data (lookups, counters, maps by id), payloads whose shape is dictated by an
  external API at the boundary where they are serialised, or conversion methods such as `as_dict`.
