---
id: R70
title: Mutually exclusive fields are a discriminated union, not an "exactly one" validator
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions, https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra, https://docs.pydantic.dev/latest/concepts/validators/#field-before-validator, Fowler Refactoring "Replace Type Code with Subclasses", owner convention
---
## Rule

- A model whose variants share one class through several optional (`X | None`) fields, with a validator counting non-`None` fields to enforce "exactly one of these", is a violation: a sum type in disguise. (C1)
- Each variant is its own model class. (C2)
- Each variant carries a `Literal` tag field. (C3)
- The union of the variants uses `Field(discriminator=...)` on the tag. (C4)
- Each variant declares `extra="forbid"`, so a payload carrying another variant's key is rejected, not silently dropped. (C5)
- An invariant spanning several fields of one variant lives on the variant that owns those fields. (C6)
- An invariant spanning the whole tree stays on the containing model. (C7)
- Legacy payloads without the tag are normalized by exactly one `BeforeValidator` at the union boundary. (C8)
- A per-variant fallback for untagged payloads is prohibited. (C9)

## Incorrect

- `class Delivery(BaseModel)` with `address`, `locker`, `pickup_point` all optional and a `model_validator` checking `sum(... is not None ...) != 1`.
- A dataclass `__post_init__` checking `[email, phone, post].count(None) != 2`.
- Variants `HomeDrop` / `LockerDrop` in an `Annotated[..., Field(discriminator="kind")]` union, one lacking `extra="forbid"` and one lacking its `Literal` tag.
- A variant with its own `model_validator(mode="before")` filling in a missing tag.
- (LLM) A plain `HomeDrop | PickupDrop | None` union field with no discriminator, and a locker-slot invariant (one variant's own fields) placed on the containing `Order` model instead of on `LockerDrop`.

## Correct

- `HomeDrop` / `LockerDrop` / `PickupDrop` as frozen pydantic dataclasses, each `@dataclass(frozen=True, config=ConfigDict(extra="forbid"))` with a `kind: Literal[...]` tag, joined in the containing field as `list[Annotated[HomeDrop | LockerDrop | PickupDrop, BeforeValidator(tag_legacy), Field(discriminator="kind")]]`; the locker-slot invariant lives on `LockerDrop`, the tree-wide "at most three home drops" on `Order`, each raising a project error subclass.
- Look-alikes: a validator that counts items in a list (not `None` checks), an "at least one of" validator (`sum(v is not None for v in (...)) == 0`), a "not exactly two of three" validator (`... == 2`), a count of missing values in a data list (`sum(1 for r in self.readings if r is None) > 1`), and a model with one optional field.

## Detection

Reports: a count over a literal tuple or list of fields of the set ones (`sum(v is not None for v in (self.a, self.b, ...))`, `len([...])` of the same shape) or of the `None` ones (`sum(v is None ...)`, `[self.a, self.b, ...].count(None)`), inside a validator method (`model_validator`, `root_validator`, `validator`, `field_validator`, `__post_init__`, `__init__`) of a class with at least two optional fields, when the count (directly or through the name it is assigned to) is compared so that exactly one or at most one field may be set: set count `== 1`, `!= 1`, `> 1`, `>= 2`; `None` count `== n-1`, `!= n-1`, `< n-1`, `<= n-2` for n fields. "At least one" (`== 0`) and other bounds (`== 2`) are not reported (C1). Also every member class of an `Annotated[..., Field(discriminator="tag")]` union (resolved by name across the scanned modules, inheriting through bases) that lacks `extra="forbid"` (as a class keyword, in a decorator's `config=ConfigDict(...)`, or in the body) or a `Literal`-annotated tag field, at the class line (C3, C5); and a `model_validator(mode="before")` defined on such a member (C9).

## LLM scan

- Flag "exactly one / at most one" enforcement written in other shapes (chained `if a and b`, `bool(a) + bool(b)`, early returns) over optional fields (C1), and check the replacement is one class per variant (C2).
- Flag unions of variants that lack `Field(discriminator=...)` (C4).
- Check invariants sit at the right level: per-variant invariants on the variant (C6), tree-wide invariants on the containing model (C7).
- Check legacy untagged payloads are normalized by exactly one `BeforeValidator` at the union boundary, not by several or by per-variant code (C8, C9).
- Do not flag optional fields that may legitimately be set together, nor counts of non-`None` items in data lists.
