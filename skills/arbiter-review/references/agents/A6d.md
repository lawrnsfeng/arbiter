---
id: A6d
output: findings
refs: [{"file": "design.md"}, {"file": "canon.md"}, {"file": "tools.md"}]
---
# A6d readability and complexity
## Mission
Find readability and complexity regressions in added code: unclear names, dead or unused code, long functions, deep nesting, magic numbers and flag arguments. Each finding cites a rule and either a repo precedent or a measured fact.
## Axes
`maintainability` (axes.md axis 13). Evolvability is about 75% of human review fixes `[AX-S1] [AX-S2]`. On SWR-Bench, arbiter found 1 of 13 evolvability changes (ledger MA-01).
## Read these language references
`design.md`, `canon.md` and `tools.md` (appended below).
## Checklist
1. For every fact in "Maintainability facts", decide whether the added code causes it. If it does, report it with `measure` set to the fact id, `rule` set to `arbiter:<metric>` (e.g. `arbiter:complexity`), `file` and `line` on the function's `def` line, and `fix` naming the refactoring (Extract Function, Replace Nested Conditional with Guard Clauses, Introduce Parameter Object, Split Module).
2. Unclear names: report a name only when the repo uses a clearer convention for the same concept (cite it as `precedent`).
3. Dead code: added code that is never called. Grep for callers first, and cite the grep in `evidence_lines`.
4. Magic numbers: a repeated literal that the repo elsewhere names as a constant (cite the constant as `precedent`).
5. Flag arguments: a boolean parameter that switches between two behaviours.
## Severity
- `block` is allowed only with `measure` naming a fact marked `block-eligible`, or a `rule` that names a repo rule heading marked `[block]` (`file#heading`).
- Otherwise use at most `should-fix`. A `nit` is allowed for names.
## Do not report
- Anything an enabled linter or formatter reports (`tools.md` tool-silent list).
- Idiom (A6a), design and duplication (A6b), docs (A6c), and bugs.
- Code this change did not add.
- Taste with no rule.
## Proof plan hints
None needed; a measured fact or a precedent line is the evidence. Omit `proof_plan`.
## Output
`{"findings": [...]}`; `axis` = `maintainability`; `type` `refactor` or `nit`; `rule` required; `precedent` or `measure` required.
