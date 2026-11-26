---
id: R75
title: No explanatory comments; the code says what it does
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring "Comments" smell / "Extract Function" / "Introduce Assertion", https://refactoring.guru/smells/comments, Martin Clean Code ch. 4 (Comments), https://peps.python.org/pep-0257/, https://docs.python.org/3/library/re.html#re.VERBOSE, owner convention
---
## Rule

- An explanatory `#` comment is a violation: a failure of expression, not documentation; names, types and structure carry the meaning. (C1)
- A comment that restates the code (e.g. `# add one to the total`) is a violation. (C2)
- A comment that narrates a step (e.g. `# now check the input`) is a violation. (C3)
- A comment that apologizes for a shape (e.g. `# workaround for ...`) is a violation. (C4)
- A comment that sections a function (e.g. `# --- helpers ---`) is a violation. (C5)
- A `# TODO` comment is a violation; pin the case with code, a raised named error, or a test. (C6)
- Remedy: extract a named function whose name states the intent. (C7)
- Remedy: give the value a type or enum instead of a bare literal. (C8)
- Remedy: turn the branch into polymorphism or a method on the class owning the data. (C9)
- Remedy: split a long function into steps that read as prose; reaching for OOP (the missing class) is the intended remedy. (C10)
- Docstrings are not comments under this rule and remain mandatory. (C11)
- A docstring restating the signature (e.g. `:param name: the name`) is a violation; a docstring states what the expression cannot: the contract, the unit, the invariant, the surprising case, or a concrete example. (C12)
- Permitted: machine directives whose text is not prose (`# type: ignore[...]`, `# noqa: ...`), themselves exceptional. (C13)
- Permitted: shebang and encoding lines. (C14)
- Permitted: editor and tooling markers (`# fmt: off`, `# pragma: no cover`), with the reason expressed in the surrounding name or test, not as prose beside them. (C15)
- Permitted, only while a live review is in progress: review markers (`# review:`, `# rv:`, `# ?:`) that a reviewer writes into the code while reviewing it, as transient coordination state of the review workflow. (C16)
- Permitted: the project's designated deliberate-simplification marker (`# shortcut:`, the marker the project's simplification tooling emits), recording the simplification's ceiling and upgrade path. (C17)
- Permitted: per-part commentary inside a `re.VERBOSE` pattern, which is the pattern's own syntax. (C18)
- A regex's "line it matches" example goes in the pattern's name or docstring, never in a `#` comment above it. (C19)
- This rule overrides any other guideline asking for a comment before each regex pattern: the example lives in the docstring and the `#` line does not ship. (C20)
- A review marker is stripped as soon as the reviewer has touched the code and has the context; review markers never ship, so one left in merged or shipping code is a violation. (C21, owner ruling)
- `#` comments are disapproved in general: the permitted list (C13–C18) is exhaustive, and any other `#` comment is a finding. (C22, owner ruling)

## Incorrect

- `# first, weigh everything` above a block (narration).
- `# TODO(depot): split loads above the van limit` (deferred case).
- `# kludge: the scale reports every parcel twice` (apology).
- `# ===== van =====` inside a method (section banner).
- `# noqa: B018 temporary until the van API settles` (prose beside a directive).
- A docstring line `:param depot_code: depot code` (restates the signature).
- (LLM) `stock -= len(parcels)  # subtract the dispatched parcels from stock`, `unit = van.unit or "kg"  # unit is missing on older vans`, a `# e.g. "PX-1042"` comment above a regex constant, and a `# rv: why are the grams halved?` review marker left in shipped code (C21).

## Correct

- `van.load_of(parcels)` and a raised `OverweightLoadError` instead of the narrated steps and the deferred case, `self.inventory.release(parcels)` instead of the restating comment, an explicit `if van.unit is None: return van.default_unit()` branch, and a `ParcelId` type whose docstring carries the matched example (`>>> ParcelId("PX-1042")`) for the `PARCEL_ID` pattern imported from the project's patterns module, so no `#` example sits above a regex (C19).
- Look-alikes: shebang and encoding lines, `# type: ignore[arg-type]`, `# noqa: E501`, `# fmt: off`/`# fmt: on`, `# pragma: no cover`, `# shortcut: ...`, and a docstring whose `:param` states a unit or format. No review marker appears: the correct code is shipped code (C21).

## Detection

Tokenizes each module and reports, per comment line: `TODO`/`FIXME`/`XXX`/`HACK` comments (C6); apology wording (`workaround`, `work around`, `kludge`, `hack`, `temporary`, `for now`) (C4); section banners (three or more `-=*#~_` characters, or text framed by them) (C5); narration openers (`now`, `then`, `next`, `first`, `finally`, `step N`) (C3); and prose next to a machine directive or tooling marker in the same comment (C13, C15). Shebang/encoding lines, recognised directives (`type: ignore`, `noqa`, `fmt:`, `pragma:`, `pyright:`, `ruff:`, `isort:`, `pylint:`, `mypy:`), review markers and `shortcut:` markers are skipped (C14, C16, C17); whether a review marker belongs to a live review or has shipped (C21) is not visible in the source, so the LLM scan decides it. `re.VERBOSE` commentary lives inside strings and is never a comment token (C18). Also reports docstring lines `:param name: [the|a|an] <name words>` that only restate the parameter name (C12). Explanatory comments of other shapes (C1, C2, C22) are left to the LLM scan.

## LLM scan

- Read every remaining `#` comment: flag any that explains, restates or narrates the code (C1, C2, C3), including inline comments such as `# can be None here`; suggest the remedy that removes the need (C7–C10).
- Flag docstrings that only restate the signature in any style (Google `Args:`, NumPy), and accept those that state a contract, unit, invariant, surprising case or example (C11, C12).
- Flag a comment above a regex that shows the line it matches; the example belongs in the pattern's name or docstring (C19, C20).
- Flag every review marker (`# review:`, `# rv:`, `# ?:`) in code being merged or shipped: the reviewer strips it once they have touched the code and have the context, so a marker that survives into a branch under review for merge is a finding (C16, C21). Flag directives followed by prose (C15) that the detector missed.
- Treat any `#` comment outside the permitted list (C13–C18) as a finding, even when it reads as helpful (C22).
- Do not flag shebangs, encoding lines, bare directives, `re.VERBOSE` per-part commentary, or the deliberate-simplification marker.
