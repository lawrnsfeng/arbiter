---
id: R65
title: A frozen dataclass built at several sites with a shared argument subset gets a builder
tier: ast+semantic
severity: should-fix
status: ok
refs: https://refactoring.guru/design-patterns/builder, Gamma et al. Design Patterns "Builder", Fowler Refactoring "Introduce Parameter Object", owner convention
---
## Rule

- Applies to a frozen dataclass that is constructed at several sites where each site repeats the same subset of arguments. (C1)
- Such a dataclass is built through one builder class. (C2)
- The builder accumulates the shared arguments once, in its constructor. (C3)
- The builder exposes `build(...)` taking only the arguments that vary between sites. (C4)
- Repeating the shared argument subset at each construction site (several direct constructor calls passing the same shared arguments) is the violation. (C5)

## Incorrect

- Three methods of an importer each building `Ingredient(self.recipe_id, self.servings, ...)`: the shared prefix comes from the importer's own attributes.
- Three `Seat(...)` values in one dict literal, each repeating `flight=flight, cabin=cabin` in varying keyword order.
- Three functions each returning `Seat(row, letter, FLIGHT, CABIN)` with the same module-level constants.
- (LLM) A frozen pydantic model built at three sites repeating the same two keyword arguments.

## Correct

- `IngredientBuilder(recipe)` reading the shared recipe id and servings once, then `make.build(name, grams, is_optional=...)` per ingredient.
- Look-alikes: three separate functions each building `Span(start, end)` from their own parameters (same spelling, different values), and three `Span(x, 0)` calls sharing only a literal.

## Detection

Finds every class decorated `@dataclass(frozen=True)` (or `@dataclasses.dataclass(frozen=True)`) in the scanned modules and every call to it by name across all modules. An argument is a positional slot or keyword whose expression is not a literal constant, identified together with the scope its value comes from: an expression rooted at `self`/`cls` belongs to its class; any other expression belongs to the innermost enclosing function that binds its root name (as a parameter or local), or else to the module. So equal spellings of function-local names in unrelated functions are different arguments, while module-level constants shared across functions are the same argument. When at least three calls share at least two such arguments, reports each of those calls. Covers C1 and C5.

## LLM scan

- Flag other immutable records (frozen pydantic models, `NamedTuple`, `attrs` frozen classes) constructed at several sites that repeat the same argument subset (C1, C5).
- Where a builder exists, check it takes the shared arguments once in its constructor (C3) and that `build()` takes only the varying ones (C4), and that construction goes through it rather than around it (C2).
- Do not flag records built at a single site, or sites that share only a literal default.
