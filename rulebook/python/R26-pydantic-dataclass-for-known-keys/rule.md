---
id: R26
title: A dict with known keys gets one frozen pydantic dataclass with one parser method
tier: ast+semantic
severity: should-fix
status: ok
refs: pydantic docs: Dataclasses, pydantic docs: TypeAdapter, pydantic docs: Validators (raising ValueError in validators), pydantic docs: Performance (reuse TypeAdapter instances), Fowler: Encapsulate Record
---
## Rule

- A "wild" dict with known keys read from outside is modelled as one frozen `pydantic.dataclasses.dataclass`. (C1)
- The record has one parser method (e.g. `from_record`) that is the boundary. (C2)
- The boundary validates through `TypeAdapter(cls).validate_python(raw)`. (C3)
- Where parsing runs per entry, the `TypeAdapter` is built once at module level and reused, not rebuilt per call. (C4)
- A `ValidationError` is mapped to the call site's own typed error through a classmethod on that error class (e.g. `ParcelError.from_pydantic(err)`). (C5)
- pydantic `BaseModel` is not used for a record that only holds data, or has simple parsing logic, and is never dumped; it is used when the model is dumped/serialized or needs model-wide validation. (C6, owner ruling)
- Hand-rolled `isinstance` ladders, one check per field, are the regression this rule forbids. (C7)
- Blind nested key access into the raw dict (e.g. `raw["courier"]["name"]`) is forbidden. (C8)
- Exception: a single-value union (e.g. a value that is either a number or a date string) stays hand-parsed. (C9)
- Exception: a deliberately lenient load (e.g. the project's configuration loader that tolerates unknown or missing input) stays hand-parsed. (C10)
- Keys the record does not own but must carry through (passthrough keys) go in a declared `passthrough` field filled by a `model_validator(mode="before")`, because pydantic dataclasses drop `extra="allow"` keys on dump. (C11)
- Absent versus explicitly empty is preserved with `X | None = None` fields, not empty-value defaults. (C12)
- At a plain-validator boundary the parse error is a `ValueError` subclass that sets its message in `__init__` (pydantic turns it into a `ValidationError`). (C13)
- Never a bare `raise ValueError(...)` with an inline message at such a boundary. (C14)
- Choose the class by need: a record that only holds data, or has simple parsing logic and is never dumped, is a `pydantic.dataclasses.dataclass` (it adds the validation plain `dataclasses.dataclass` lacks). (C15, owner ruling)
- A complex need (the model is dumped with `model_dump`/`model_dump_json`, needs many field annotations or validators, or needs model-wide validation) is a `pydantic.BaseModel`. (C16, owner ruling)
- pydantic is used only when the repository adopts it: declared in its package management (`pyproject.toml` dependencies, `requirements*.txt`, `setup.cfg` / `setup.py`, `Pipfile`, a poetry/uv lock file). A repository that does not depend on pydantic is never made to: the record falls back to `dataclasses.dataclass`, parsed by its one parser method. (C17, owner ruling)

## Incorrect

- `class Parcel(BaseModel)`: a data-only record that is never dumped and has no validators.
- `@pydantic.dataclasses.dataclass` record without `frozen=True`.
- `TypeAdapter(Scan).validate_python(raw)` built inside a per-entry parse function.
- `isinstance(raw["tracking_id"], str)` then `isinstance(raw["weight_g"], int)`: an isinstance ladder.
- `raw["courier"]["name"]`: blind nested access.
- `raise ValueError(f"...")` inside a `field_validator` and inside a function used as `AfterValidator`.
- `extra="allow"` used to carry unknown keys, and `note: str = ""` erasing absent-vs-empty (model only).
- `import pydantic` added to a repository whose package manifests do not declare pydantic (model only).

## Correct

- Frozen pydantic dataclass `Parcel` with `note: str | None = None`, a `passthrough` field filled by a before
  model validator, one `from_record` boundary using a module-level `TypeAdapter`, `ParcelError.from_pydantic(err)`,
  and `BlankPostcodeError(ValueError)` raised from the postcode validator.
- Look-alikes: `BaseModel`s a web framework dumps (`response_model=TrackingView`, a route returning `-> Receipt`) and
  one whose fields carry `Field` constraints (C16); a stdlib `@dataclass` without `frozen`; a
  single value checked against two types (C9); integer indexing `grid[0][1]`; a `ValueError` subclass raised in a plain function
  that is not a validator.

## Detection

`check.py` reports:

- a class whose base is `BaseModel`, in a module that imports pydantic, when the class is data-only by structure: no
  method decorated `field_validator` / `model_validator` / `validator` / `root_validator`, no `model_config` or
  inner `Config`, no field with a `Field(...)` constraint (`ge`, `max_length`, `pattern`, ...), and the class is not
  dumped: no module that mentions its name calls `.model_dump()`, `.model_dump_json()`, `.dict()`, `.json()` or
  `.model_json_schema()`, it is not named in a `response_model=` keyword, and it is not in the return annotation of
  a decorated (route) function (C6, C15);
- a class decorated with pydantic's `dataclass` (`pydantic.dataclasses.dataclass` or the name imported from
  `pydantic.dataclasses`) without `frozen=True` (C1);
- a `TypeAdapter(...)` call inside a function body (C4);
- in one function, `isinstance` checks on two or more different string keys of the same dict (`raw["k"]`,
  `raw.get("k")`, or a local assigned from one), one hit at the first check (C7);
- a string-key subscript of a string-key subscript, `x["a"]["b"]`, reported once per chain (C8);
- a `raise ValueError(...)` (or bare `raise ValueError`) inside a function decorated `field_validator`,
  `model_validator`, `validator` or `root_validator`, or passed to `BeforeValidator` / `AfterValidator` /
  `PlainValidator` / `WrapValidator` in the same module (C13, C14).

## LLM scan

Judge what the detector cannot: whether a dict with known keys read from outside has a record at all (C1), whether
the record has exactly one parser method that is the boundary (C2) and validates through `TypeAdapter` (C3), whether
`ValidationError` is mapped to the site's typed error through a classmethod (C5), whether unknown keys the code must
keep ride in a declared `passthrough` field filled by a before model validator rather than `extra="allow"` (C11), and
whether optional fields use `X | None = None` so absent and empty stay distinct (C12). Dismiss isinstance ladders
and nested access that fall under the exceptions: a single value that may be one of several types (C9) and a
deliberately lenient loader such as the project's configuration loader (C10); say which exception applies.

Then judge the model class by need (C6, C15, C16): a `BaseModel` the detector reported is fine if it is serialized
somewhere the detector cannot see (returned from a web framework that dumps it, passed to a library that calls
`model_dump`) or has model-wide validation; a pydantic dataclass that is dumped or carries many validators should be a
`BaseModel`. Check adoption (C17): read the repository's package manifests (`pyproject.toml`, `requirements*.txt`,
`setup.cfg` / `setup.py`, `Pipfile`, `poetry.lock` / `uv.lock`); if pydantic is not declared, flag every pydantic
import and every recommendation of pydantic, and propose a `dataclasses.dataclass` with its one parser method
instead. In such a repository the detector's isinstance-ladder and nested-access hits still stand, but the fix is the
stdlib dataclass, not pydantic.
