---
id: R62
title: A function returning one project-owned type is that type's classmethod
tier: ast+semantic
severity: should-fix
status: ok
refs: https://docs.python.org/3/library/functions.html#classmethod, Effective Python item "Use @classmethod Polymorphism to Construct Objects Generically", Fowler Refactoring "Replace Constructor with Factory Function" / "Move Function", owner convention
---
## Rule

- A free (module-level) function whose return type is a single project-owned type is instead a `@classmethod` of that type. (C1)
- This holds even when every input is a primitive: the resolution logic lives next to the type's other constructors. (C2)

## Incorrect

- `def loan_for(isbn: str, member: str, days: int) -> Loan`: free factory of a project dataclass from primitives.
- `def _shelf_from_label(label: str) -> "Shelf"`: private helper with a string forward reference.
- `async def loan_from_row(row: dict) -> Loan`: async free factory.
- `def restock(code: str) -> StockShelf`: return type is a project class imported under an alias.
- (LLM) `@cache def default_shelf() -> Shelf`: decorated free factory.

## Correct

- `Loan.from_isbn(isbn, member, days)`: the same resolution as a classmethod on `Loan`.
- Look-alikes: free functions returning `list[date]` (not a single type), `date` (not project-owned) and `Loan | None` (not a single type), a `Protocol` method returning `Loan`, and a method returning `Loan`.

## Detection

Reports every undecorated module-level `def`/`async def` whose return annotation is exactly one class (bare name, quoted name, or `module.Class`) that resolves to a top-level, non-`Protocol` class of the scanned modules: defined in the same module, imported relatively, or imported from a dotted module whose path is among the scanned files. Covers C1 and C2 (inputs are deliberately ignored).

## LLM scan

- Flag decorated module-level functions (`@cache`, `@lru_cache`, registration decorators) that return a single project-owned type and could be a classmethod of it (C1, C2).
- Flag free functions returning a project type through a type alias the detector cannot resolve.
- Do not flag framework hooks whose signature the framework dictates (test fixtures, route handlers, signal receivers), nor functions returning third-party or builtin types.
