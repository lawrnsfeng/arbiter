---
id: R68
title: Rendering a list of records at a call site belongs to a plural class
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring "Encapsulate Collection" / "Move Function" / "Combine Functions into Class", https://docs.python.org/3/library/dataclasses.html#frozen-instances, owner convention
---
## Rule

- A call site that renders a list of records by joining the first item's rendering with a join over the rest (`items[0].text + sep.join(... for x in items[1:])`) is a violation. (C1)
- Rendering a list of records belongs to a plural class: a frozen dataclass wrapping `tuple[Item, ...]`. (C2)
- The rendering is a property of that plural class. (C3)
- The call site constructs the plural class and reads the property (`Plural(items).prop`) instead of joining inline. (C4)

## Incorrect

- `notice = f"Overdue: {loans[0].title}"` then `notice += "".join(f"; also {loan.title}" for loan in loans[1:])`: the first record rendered in one statement, the rest appended in the next.
- An f-string `f"{stops[0].name} -> {' -> '.join(s.name for s in stops[1:])}"`: the same split inside one template.
- `steps[0].title.capitalize() + "; then " + "; then ".join([s.title for s in steps[1:]])` spread over a multi-line expression in a method.
- (LLM) A loop accumulating `out += f"{loan.isbn} due {loan.due}\n"` over records at a call site.

## Correct

- `Loans(tuple(loans)).notice`: a frozen plural dataclass over `tuple[Loan, ...]` with a `notice` property.
- Look-alikes: `stops[0]` read without rendering it next to a join over the rest, a header `rows[0].cells` and a body joined over `rows[1:]` returned separately (never concatenated), `" ".join(sys.argv[1:])` over plain strings, a delta computation reading `readings[0].value` inside the comprehension, and `stops[1:]` sliced for other purposes.

## Detection

Within one function (or the module body), reports each `sep.join(...)` whose argument is a single-loop comprehension over `X[1:]` whose element reads an attribute of the loop variable (each record is rendered), when an attribute of `X[0]` (the first record's rendering) is combined with it: read in the same statement outside the join call, or assigned to a name `s` that the join's statement extends with `s += ...`. A header and body kept in separate values, joins over plain values (`" ".join(argv[1:])`) and `X[0]` used inside the comprehension are not reported. Covers C1 and the call-site half of C4.

## LLM scan

- Flag other call-site renderings of a list of records (string accumulation loops, `"\n".join(r.text for r in records)` repeated at several call sites) that belong as a property on a plural frozen dataclass (C2, C3, C4).
- Where a plural class exists, check it is a frozen dataclass over `tuple[Item, ...]` (C2) and exposes the rendering as a property, not a method or free function (C3).
- Do not flag joins of plain strings that are not records, or rendering already inside the plural class.
