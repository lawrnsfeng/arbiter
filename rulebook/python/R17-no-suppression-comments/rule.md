---
id: R17
title: No checker-suppression comments without approval
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 484 (type: ignore), mypy docs: Silencing type errors, Ruff docs: Error suppression, Google Python Style Guide 2.1 Lint
---
## Rule

- No `# type: ignore` comment (or another type checker's equivalent, e.g. `# pyright: ignore`, `# mypy: ignore-errors`) without approval. (C1)
- No `# noqa` comment (or another linter's equivalent, e.g. `# ruff: noqa`, `# pylint: disable`, `# nosec`) without approval. (C2)
- Fix the design so the checker has nothing to complain about: typed data instead of casting a raw value, a narrow `except` instead of silencing a broad-except lint. (C3)
- Ask first; use a suppression only when every real fix is genuinely more expensive, and say so when asking. (C4)

## Incorrect

- `schedule[parcel_id]  # type: ignore[index]` on an `Optional` dict that was never narrowed.
- `to_kilograms = lambda ...  # noqa: E731` and a six-parameter `dispatch(...)  # noqa: PLR0913`.
- A file-wide `# ruff: noqa`, a `# pyright: ignore[...]` and a `# pylint: disable=...` comment.
- `cast(int, getattr(...))` used only to quiet the type checker about an untyped value (model only).

## Correct

- The `None` case raises a typed error, so the index needs no ignore; the lambda becomes a `def`; the long
  parameter list becomes a `Shipment` parameter object.
- Look-alikes: a docstring and a string constant that mention `# noqa` / `# type: ignore` in prose.

## Detection

`check.py` tokenizes each module and reports every comment token containing a suppression directive: `type: ignore`,
`noqa` (incl. `ruff: noqa`), `pyright: ignore`, `pylint: disable`, `mypy: ignore-errors`, `nosec`. One hit per
comment line. Covers C1 and C2; whether the suppression was approved (C4) is outside the code.

## LLM scan

For each reported suppression, state the real fix that would remove it (C3): typed data at the boundary, a narrowed
`except`, a corrected signature, a split function. If a nearby comment records an approval and why the real fix is
more expensive (C4), say so and leave it. Beyond the detector, flag code that dodges the checker without a comment:
`typing.cast(...)` or an `Any` annotation used only to silence an error on untyped data, an `assert isinstance(...)`
added only to narrow a type the design should already guarantee. Do not flag `cast` where the type system genuinely
cannot express a proven fact (e.g. after a runtime check in another function) and the code says why.
