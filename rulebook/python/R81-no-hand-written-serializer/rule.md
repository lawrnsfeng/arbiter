---
id: R81
title: A hand-written serializer re-invents model_dump; never write one
tier: ast+semantic
severity: should-fix
status: ok
refs: pydantic docs Serialization (model_dump), pydantic docs Fields (serialization_alias, exclude), pydantic docs computed_field, pydantic docs field_serializer, Fowler Refactoring "Remove Duplicated Code"
---
## Rule

- Applies when the project depends on pydantic. (C1)
- A method on a model-like class that returns a dict built from a literal of its own fields is a violation, whatever the method is named. (C2)
- A method that spreads `model_dump` and then overwrites a field by hand is a violation. (C3)
- A method that binds such a hand-built dict to a local and returns it is a violation. (C4)
- Judge the shape, never a list of method names. (C5)
- Serialization is `model_dump(...)`, with the mapping carried by the model's own annotations. (C6)
- A different wire name → `Field(serialization_alias=...)`. (C7)
- A nested shape → annotate the field with the nested model. (C8)
- A derived member → `@computed_field`. (C9)
- A member left out → `Field(exclude=True)`. (C10)
- A field value needing a rule (sorted, rounded, formatted) → `@field_serializer("name")`, never a method that re-dumps the model to apply it. (C11)
- A plain `@dataclass` (frozen or slotted included) holding serialized data becomes a pydantic `BaseModel` (it is dumped, see C14); a dataclass lacking a dump does not justify a hand-written one. (C12)
- Exempt: a payload whose shape is not the object's fields (an envelope, a vendor wire format); the method is then named for that format. (C13)
- Choose the model class by need: a record that is dumped or serialized, or needs many field annotations, validators or model-wide validation, is a `pydantic.BaseModel`; a record that only holds data, or has simple parsing and is never dumped, is a `pydantic.dataclasses.dataclass`. A pydantic dataclass that gets dumped (e.g. through `TypeAdapter(...).dump_python`) is therefore the wrong class. (C14, owner ruling)
- Pydantic counts as adopted only when the repo declares it in its package management (`pyproject.toml` dependencies, `requirements*.txt`, `setup.cfg`/`setup.py`, `Pipfile`, a poetry/uv lock). A repo that does not depend on pydantic is never made to: its records stay `dataclasses.dataclass`, and this rule does not apply. (C15, owner ruling)

## Incorrect

- A model method returning a dict literal of its fields, renaming one and hand-serializing a nested object.
- A model method binding that dict to a local and returning it.
- A model method spreading `**self.model_dump()` and overwriting a field.
- A model method re-dumping itself into a local, rounding one key, and returning it.
- Model methods re-dumping into a local patched with `.update(...)` or `|= {...}` and returning it.
- A frozen slotted dataclass with a `dict(street=self.street, ...)` method.
- A dict comprehension over `getattr(self, name)` for a hard-coded name list (model only).
- A `pydantic.dataclasses.dataclass` shipment record dumped through a module-level `TypeAdapter(...).dump_python`.

## Correct

- A `BaseModel` (it is dumped, C14) with `serialization_alias`, a nested model field, a `computed_field`, an excluded field, and a `field_serializer`, dumped with `model_dump(mode="json", by_alias=True)`.
- A data-only depot code that is never dumped, as a frozen `pydantic.dataclasses.dataclass` validated through a module-level `TypeAdapter` (C14).
- Look-alikes: an envelope method named for its vendor format wrapping `model_dump`; a method returning per-depot scan counts (a dict keyed by data, not by the model's fields).

## Detection

When any scanned module imports pydantic (C1), `check.py` reports a non-dunder method of a class that declares at
least two fields (class-level annotations or `self.x =` in `__init__`) when any `return` yields, directly or through a
local:

- a dict literal or `dict(k=...)` call in which at least two values, and at least half of all values, read `self.<field>` (C2, C4);
- a dict literal spreading `**…model_dump(...)` (or `.dict()`) next to explicit keys (C3);
- a local bound to `…model_dump(...)` that is then patched (subscript assignment, `.update`/`.setdefault`/`.pop`, or
  `|=`) and returned (C3, C11).

It never looks at method names (C5). Classes include plain dataclasses (C12).

It also reports, at the call, `dump_python(...)`/`dump_json(...)` on a `TypeAdapter(...)` (directly or through a name
bound to one) whose type argument is, or contains, a class decorated `pydantic.dataclasses.dataclass` in the scanned
modules — `Cls`, `list[Cls]`, `tuple[Cls, ...]`, `dict[str, Cls]`, `Cls | None`: a dumped record is a
`BaseModel` (C14). Validating through a `TypeAdapter` is not reported. "Imports pydantic" stands in for C15's
package-management declaration, which a module-only detector cannot read.

## LLM scan

- Confirm or dismiss each detector hit against C13: a payload whose shape is not the object's fields (an envelope, a
  vendor format) is exempt only when the method is named for that format; otherwise the hit stands.
- Report serializers the detector misses: dict comprehensions over `getattr(self, name)`, `vars(self)` / `asdict(self)`
  followed by manual edits, builders that append fields to a dict one statement at a time, and a re-dumped dict
  patched by any route the detector does not track (a helper that mutates it, `dict(data, key=...)`, a merge into a new
  dict) before it is returned (C2–C4, C11).
- For each finding, name the pydantic replacement: `serialization_alias` (C7), nested model annotation (C8),
  `computed_field` (C9), `Field(exclude=True)` (C10), `field_serializer` (C11), or converting the dataclass to a model
  (C12), dumped with `model_dump` (C6).
- Check C15 against the repo's package management: if pydantic is not declared there, dismiss every hit and do not
  recommend pydantic; recommend `dataclasses.dataclass` with a single, tested conversion instead.
- For each pydantic dataclass in a change, apply C14: report it when it is dumped or serialized, or carries many field
  annotations/validators or model-wide validation, and name `BaseModel`; report a `BaseModel` that only holds data, has
  simple parsing and is never dumped, and name `pydantic.dataclasses.dataclass`.
- Do not flag projects that do not depend on pydantic (C1), or `__getstate__`/`__reduce__` pickle hooks.
