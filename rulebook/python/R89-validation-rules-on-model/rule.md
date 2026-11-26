---
id: R89
title: A validation rule the receiving service enforces is modelled, not hand-rolled
tier: ast+semantic
severity: should-fix
status: ok
refs: pydantic docs Fields (max_length/min_length), pydantic docs Validators (field_validator, BeforeValidator, Annotated), pydantic docs Validation errors (ctx), Fowler Refactoring "Replace Primitive with Object", "Parse, don't validate" (Alexis King)
---
## Rule

- Applies when the project depends on pydantic and a value must satisfy a rule. (C1)
- Length and size caps live on the model as `Field(max_length=...)` / `min_length=...`. (C2)
- A collection the receiver dedupes is typed as a `set` on the model. (C3)
- A cross-cutting rule is a `field_validator`. (C4)
- A type conversion is a `BeforeValidator`. (C5)
- A helper that parses or checks one value and then raises (procedural validation at call sites) is a violation. (C6)
- The model mirrors the boundary's own model; for an upstream service's rule, the field set and limits come from that service's schema. (C7)
- Detail the receiver would reject after a side effect is validated locally, before the side effect. (C8)
- A `str`/`bytes` subclass is used as a `BeforeValidator` attached with `Annotated` on the wire type, never as a field type. (C9)
- One typed error per rule: the validator raises a `ValueError` subclass. (C10)
- The model's `ValidationError` is mapped back to the specific typed error (reading the error's `ctx`) so callers can catch that type. (C11)
- A rule the model enforces itself (e.g. `Field` caps) maps to the site's general refusal error. (C12)
- Never flatten typed and general refusals into one stringly exception (building a message, then `raise ValueError(message)`). (C13)
- A model that carries service rules (`Field` limits, validators, model-wide validation) or is dumped to the receiver is a `pydantic.BaseModel`; a record that only holds data, or has simple parsing and is never dumped, is a `pydantic.dataclasses.dataclass`. (C14, owner ruling)
- Pydantic counts as adopted only when the repo declares it in its package management (`pyproject.toml` dependencies, `requirements*.txt`, `setup.cfg`/`setup.py`, `Pipfile`, a poetry/uv lock). A repo that does not is never made to depend on it for validation: the rule then lives on a `dataclasses.dataclass` (checked in `__post_init__`, one typed `ValueError` subclass per rule), and C2–C12's pydantic remedies do not apply. (C15, owner ruling)

## Incorrect

- A printer method capping a label's line count with a `%`-formatted `ValueError`.
- A postcode helper raising a `.format()`-built `ValueError` from the `else` of its check.
- A weight parser re-raising a concatenated-string `ValueError` from its `except` block.
- A `str` subclass used directly as a model field type (model only).
- A shipping function that books with the carrier first and only then checks the destination country (model only).
- A pydantic dataclass carrying `Field` caps, several field validators and a model-wide validator, then sent to the carrier (model only, C14).

## Correct

- A `Label` `BaseModel` (it carries the carrier's limits and validators and is dumped to the carrier, C14) mirroring the carrier's label schema: `Field(min_length=…, max_length=…)` on the lines, a `frozenset` of allowed services, bounded weight, a `Literal` country, a postcode `str` subclass attached as `BeforeValidator` on a `str` field, and a `field_validator` raising its own `ValueError` subclass.
- A `from_pydantic` classmethod on the general refusal error that maps `ValidationError` to the typed error found in `ctx`, or to the general refusal for a model-enforced limit; validation before the carrier is called; the postcode subclass documents its form and its refusal with `>>>` examples.
- Look-alikes: a `field_validator` raising inside the model; a `str` subclass whose `__new__` raises a typed error.

## Detection

When any scanned module imports pydantic (C1), `check.py` reports a `raise ValueError(...)`/`raise TypeError(...)`
whose first argument is a string literal, an f-string, a `"..." % x`/`"..." + x`/`"...".format(x)` expression, or a
local bound to one (C13), in the body or `else` of an `if` testing a parameter or inside an `except` handler (C6), in a
module-level function or a method of a non-`BaseModel` class that takes one or two parameters besides `self`/`cls`, is
not a dunder, and is not decorated as a pydantic validator. "Imports pydantic" stands in for C15's package-management
declaration, which a module-only detector cannot read. C14 (choosing the model class) is the model's.

## LLM scan

- Confirm each detector hit validates a value bound for a model or a service boundary; dismiss pure programming-error
  preconditions on internal calls, and say why.
- Report procedural validation the detector misses: inline cap loops and checks at call sites, helpers with more
  parameters, typed errors raised from hand-written checks that a model field could express (C2–C6).
- Check the model mirrors the receiving service's schema (field set and limits) (C7), that validation runs before any
  side effect (C8), that `str`/`bytes` subclasses are attached as `BeforeValidator` via `Annotated`, never used as the
  field type (C9), that each rule raises its own `ValueError` subclass (C10), that `ValidationError` is mapped back to
  the typed error using `ctx` (C11), and that model-enforced caps map to the general refusal (C12).
- Check C15 against the repo's package management: if pydantic is not declared there, dismiss detector hits that ask
  for a pydantic model and require instead a `dataclasses.dataclass` whose `__post_init__` raises one typed
  `ValueError` subclass per rule; never recommend adding pydantic.
- Apply C14 to every model holding service rules: a `pydantic.dataclasses.dataclass` with `Field` limits, several
  validators or a model-wide validator, or one that is dumped to the receiver, should be a `BaseModel`; a `BaseModel`
  that only holds data, parses simply and is never dumped should be a pydantic dataclass.
- Do not flag `field_validator`/`model_validator` bodies, or projects without pydantic.
