---
id: A1a
output: findings
refs: [{"file": "idioms.md", "rows": ["Control flow"]}]
---
# A1a logic
## Mission
Find added code that computes the wrong result on intended inputs: wrong conditions or operators, off-by-one, wrong variable, stale state or partial updates.
## Axes
`logic` only (research-axes.md §2a axis 1: logic defects are 65 of 78 defect comments, S3).
## Read these language references
`idioms.md` rows Control flow (appended below).
## Checklist
1. For each added condition, check the operator and its bounds: `<` vs `<=`, `and` vs `or`, negation, inverted branch, wrong early return.
2. Check every range, slice, index and loop bound for off-by-one against the documented intent (docstring, name, caller usage).
3. Check that the right variable is used: copy-paste leftovers, shadowed names, loop variable vs outer variable, wrong field.
4. Check state: a value read before it is updated, a cache not invalidated, a flag not reset, a partial update where one of two related fields changes.
5. Check units and conversions: ms vs s, bytes vs chars, 0- vs 1-based.
6. Find the intended behaviour from the spec, docstring, type, test or caller, not from the code under review. Read the callers (grep the function name) to see what they expect.
7. Each finding needs a concrete `trigger`: specific input values and the wrong output they produce.
## Do not report
- Missing validation of malformed input (A1b), error handling (A2), security (A3), races (A4), style.
- Behaviour that the spec or a test explicitly asks for, even if it looks odd.
- Anything you cannot show with a concrete input. "Could be wrong" is not a finding.
- Lines this change did not add.
## Proof plan hints
- E4: a test with the trigger input, asserting the output the oracle (docstring, spec, caller) requires. Name the oracle line in `idea`.
- E3: a one-line snippet showing the expression's value when the claim is about language semantics.
- E6: a property test when the bug shows for a class of inputs (e.g. any list longer than the page size).
## Output
`{"findings": [...]}`; `axis` = `logic`; `severity` `block` when a reachable input gives a wrong result, else `should-fix`.
