---
id: R77
title: More than five keyword arguments describing one request become a frozen options dataclass
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring "Introduce Parameter Object", Python docs dataclasses (frozen=True), Google Python Style Guide 3.19.12 (function length and arguments)
---
## Rule

- Applies to a method whose keyword parameters all describe the single request it forwards (a query's filters, a payload's optional fields). (C1)
- More than five such keyword parameters is a violation. (C2)
- The method takes one frozen dataclass (`@dataclass(frozen=True)`) of options instead. (C3)
- Each dataclass field keeps the original parameter's name and default. (C4)
- The zero-argument call sends exactly what it sent before: the options parameter defaults to `None` (or a default instance) that resolves to the old defaults. (C5)
- Exempt: a constructor-style call (e.g. a create call) that maps each keyword to one server field, while that mapping stays 1:1. (C6)

## Incorrect

- An async search method with nine keyword-only filters that all land in one query-params dict.
- A sync method with six defaulted positional-or-keyword parameters all passed as keywords into one client call.
- A method whose six keyword filters are folded into one payload dict before a single send.

## Correct

- A search method taking `options: SearchOptions | None = None`, where `SearchOptions` is a frozen dataclass with the same names and defaults.
- Look-alikes: `__init__` with many keywords; a `create_*` method mapping keywords 1:1; a method with seven keywords used in different calls (not one request).

## Detection

`check.py` reports a method (a `def` directly in a class body) with more than five parameters that have defaults
(keyword-only or positional-or-keyword), when one call or one dict literal in its body references every one of them
— the syntactic sign that they all describe the single request it forwards (C1, C2). It skips `__init__`, `__new__`
and methods named `create*` (C6 candidates, left to the model). A method taking one options parameter is silent; the
detector does not check that the dataclass is frozen, keeps the names and defaults, or preserves the zero-argument
call (C3–C5 are the model's, below).

## LLM scan

- For every `create*` method or constructor with more than five keywords: report it unless each keyword maps 1:1 to
  one server field (C6); a keyword that is renamed, merged, or transformed before sending breaks the exemption.
- For methods with more than five keywords forwarded through several statements (renamed, filtered, conditionally
  added) rather than one call: report them when the keywords still all describe the one request forwarded (C1, C2).
- When a change already introduced an options dataclass, check it is `frozen=True` (C3), that every field keeps
  the old parameter's name and default (C4), and that calling the method with no argument sends the same request
  as before (C5).
- Do not flag methods whose keywords configure behaviour of the method itself (retries, timeouts, callbacks) rather
  than the forwarded request, nor functions with five or fewer such keywords.
