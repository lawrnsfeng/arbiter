---
id: R71
title: Near-clone calls sharing an argument prefix and varying on an enumerated tail are one dispatch
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring "Combine Functions into Class" / "Parameterize Function" / "Replace Conditional with Polymorphism", https://refactoring.guru/smells/duplicate-code, https://docs.python.org/3/library/enum.html, owner convention
---
## Rule

- A family of call sites, or of sibling functions, passing the same many arguments where the leading N are identical (typically a dependency/payload prefix) and only the last few differ is a hand-unrolled dispatch, and is a violation. (C1)
- The shape counts whenever the variation is governed by an enumerated or flag-like value anywhere in the tail: a parameter, a `Literal`, or a value embedded in the callee's name (`notify_<kind>`, `record_<event>`). (C2)
- The identical prefix becomes one class's constructor (the class that owns those dependencies). (C3)
- Where dependencies arrive as injected products, the recurring ones become one service object behind a single provider. (C4)
- The varying tail becomes a method taking the governing enum as an explicit argument (e.g. `notify(event, payload)`). (C5)
- That method has per-value branches (e.g. per-value private methods) named for what makes each value different, not for what is shared. (C6)
- The enum is an existing domain enum; minting a new enum just for these call sites is prohibited. (C7)
- If no stored/domain enum fits, the dispatch key is wrong (rethink it), not missing (do not invent one). (C8)
- When the enum value is decided deeper in the stack, call sites forward it; they never hardcode or re-derive it. (C9)

## Incorrect

- `shelve_by_author(index, scanner, journal, book, ...)` and `shelve_by_code(index, scanner, journal, book, ...)` in two `match` arms: the varying value lives in the callee name.
- `export_report(store, renderer, archive, period, fmt="csv", ...)` in one function and `fmt="pdf"` in another: a string flag in the tail.
- `self.price(catalogue, tariff, rates, basket, Tier.GOLD)` repeated with `Tier.STANDARD`: an enum member in the tail.
- `desk.enqueue(ledger, clock, hold, "reserved")` / `"released"` in sibling functions `on_reserve` / `on_release`, whose identical parameter lists are the sibling-function shape (LLM).

## Correct

- `Shelver(index, scanner, journal).shelve(book.section, book)`: the shared dependencies become the constructor, `Section` is the catalogue's existing enum, the per-value branches are named for what differs (`_place_by_surname`, `_place_by_call_number`), and the caller forwards the section stored on the book.
- Look-alikes: calls sharing a prefix but differing only in computed arguments, calls differing only by numbers (`scale(..., 0.5)` / `scale(..., 2.0)`), and calls whose shared leading arguments are literals.

## Detection

Within each module, groups calls having at least three positional arguments whose first three are names or attribute chains, by those three arguments plus the callee's stem (dotted callee with its last `_word` dropped). A group of two or more calls is reported, every call at its line, when the exact callee names differ (C2's name-embedded value) or when at least one differing tail slot holds a literal or a dotted attribute (e.g. an enum member) in every call (C1, C2's parameter/`Literal` value).

## LLM scan

- Flag sibling functions (not only call sites) whose parameter prefixes and bodies are identical up to an enumerated value (C1, C2).
- For reported or found families, check the remedy: the shared prefix is one class's constructor (C3) or one injected service behind a single provider (C4); the tail is a method taking the enum explicitly (C5) with branches named for what differs (C6).
- Check the governing enum is an existing domain enum rather than one minted for the call sites (C7, C8), and that call sites forward an enum value decided deeper in the stack instead of hardcoding or re-deriving it (C9).
- Do not flag calls whose shared prefix is incidental (e.g. the same two loop variables passed to unrelated helpers) or whose tail differs by computed data rather than an enumerated value.
