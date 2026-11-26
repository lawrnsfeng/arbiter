---
id: R84
title: A docstring is the shortest form that states what the code cannot
tier: ast+semantic
severity: should-fix
status: ok
refs: PEP 257 (Docstring Conventions), Google Python Style Guide 3.8 (comments and docstrings), ruff rules D413 and D417 (pydocstyle), Python docs doctest
---
## Rule

- Every docstring has exactly one summary line stating the contract or intent: the one sentence the name cannot. (C1)
- After the summary, at most one short paragraph (four lines at most), and only for a fact the body cannot show. (C2)
- A `Raises:` section appears only where the trigger is not derivable from the `raise` site (an ordering rule, a cap mirrored from another system, the distinction between two similar errors). (C3)
- A `Raises:` section is followed by a blank line (D413). (C4)
- Never `Args:`/`Returns:` entries that restate a parameter's name, its type, or the return annotation. (C5)
- Never a module docstring longer than two lines; it names the boundary the module enforces or the sibling it must be told apart from. (C6)
- A module docstring never describes its imports, call graph, or dependency rationale. (C7)
- Never prose that narrates the body ("first we …, then we …"). (C8)
- A docstring claim the body no longer honours is a defect. (C9)
- Never a bare string literal after an assignment or other statement (the bare-string rule). (C10)
- Trimming never deletes a fact: units, caps another system enforces, invariants, security boundaries, accepted trade-offs and surprising cases stay in substance. (C11)
- `>>>` doctest examples stay: they execute. (C12)
- Compression removes prose only; it never re-words, re-orders, summarises, or "cleans up" code. (C13)
- Never thin a docstring that is a contract a consumer relies on (documented example paths, a public return shape). (C14)

## Incorrect

- A five-line module docstring narrating its imports and the order of calls.
- A function docstring with a wrapped summary and two paragraphs narrating the body.
- A `Raises:` section that runs straight into the closing quotes.
- An `Args:`/`Returns:` block restating parameter names and types (model only).
- A short "first we …, then we …" narration within the line budget (model only).

## Correct

- A two-line module docstring naming the boundary it enforces.
- A function docstring: one summary line, one three-line paragraph stating a unit and a cap, a `Raises:` section followed by a blank line.
- Look-alikes: a docstring whose long part is `>>>` doctest examples; single-line class and method docstrings.

## Detection

`check.py` reports, at the docstring's closing line:

- a module docstring with more than two non-blank lines (C6), not counting two kinds of line: in a migration module
  (binds both `revision` and `down_revision`), the tool-generated `Revision ID:`/`Revises:`/`Create Date:` header
  lines, so prose above or below them still counts; and lines of a patterns module's example list, i.e. a line
  opening with a backticked name the module binds to `re.compile(...)`, which is a consumer contract (C14);
- a class/function docstring whose prose lines (all lines before the first section header such as `Args:` or
  `Raises:`, doctest paragraphs excluded) exceed the summary line plus four (C1, C2: a wrapped summary or extra
  paragraphs beyond that budget);
- a `Raises:` section running to the closing quotes with no blank line after it (C4).

## LLM scan

- Within the line budget, report summaries that wrap over two lines (C1) and a second short paragraph (C2).
- For every module docstring, including those within two lines, check it names the boundary the module enforces or
  the sibling module it must be told apart from; report one that does neither (C6).
- Judge the lines the detector skips: an example-list line that narrates instead of giving one example of the named
  pattern counts toward the two-line limit, and a migration docstring's message line must still be one line (C6).
- Report `Raises:` sections whose trigger is obvious from the `raise` site (C3), `Args:`/`Returns:` entries that restate
  a name, type, or return annotation (C5), module docstrings describing imports, call graph or dependency rationale
  (C7), narration of the body (C8), and claims the body no longer honours (C9). Bare strings after statements are C10.
- When proposing a shorter docstring, keep every unit, external cap, invariant, security boundary, trade-off and
  surprising case (C11), keep `>>>` examples (C12), change prose only, never code (C13).
- Treat each detector hit as a candidate: dismiss it when the docstring is a contract a consumer relies on (a public
  return shape, documented example paths) (C14), and say so.
