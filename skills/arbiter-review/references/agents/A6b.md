---
id: A6b
output: findings
refs: [{"file": "design.md"}, {"file": "canon.md"}]
---
# A6b design
## Mission
Find design problems the added code introduces: logic in the wrong layer, needless abstraction, a duplicated existing helper, or a smell with a named refactoring, each backed by a rule and a measured repo fact.
## Axes
`design`, `maintainability` (research-axes.md §2b axes 13 and 15). LLM design comments are resolved only 28.6% of the time (S10): report only what you can back with a fact.
## Read these language references
`design.md`, `canon.md` (appended below).
## Checklist
1. Duplicated helper: before reporting, grep the repo for an existing function doing the same job. Cite it as `precedent`.
2. Layering: logic placed in a layer the repo keeps it out of (e.g. SQL in a handler when the repo has a repository layer). Cite the precedent that shows the house layer.
3. Needless abstraction: a class, interface, factory or wrapper with one implementation and one caller, a thin or identity wrapper, a producer-side interface (Go), a GoF pattern where the language has a simpler idiom (`design.md`).
4. Smells from `design.md` §5: name the smell and the refactoring that removes it.
5. pstack code judo (prior-mint-review-research.md, thermo-nuclear-code-quality-review): a restructuring that makes whole branches, modes, helpers or layers disappear. Presumptive-blocker list: a file pushed from under 1k lines to over 1k; ad-hoc `if`s scattered into unrelated flows; feature checks spread across shared code; thin or identity wrappers; cast-heavy or optional-heavy contracts; duplicating an existing helper; logic in the wrong layer; incidental complexity kept when a code-judo simplification is visible.
6. **Effort gate.** If the inputs say `EFFORT: deep`, a code-judo item may be `severity: block` with `code_judo: true` and a `proof_plan` of rung `E1` stating the measured fact (line count before/after, path of the duplicate helper, the import edge). Otherwise set `code_judo: true` and cap severity at `should-fix`. Any other item: `severity` at most `should-fix`, unless `rule` names a repo rule heading marked `[block]`.
7. `rule` is a canon or `design.md` key, a repo rule `file#heading`, or `pstack:<blocker name>` for code judo; `precedent` is a repo `path:line`.
## Do not report
- Taste: "could be cleaner", renames, splitting a short function, patterns the repo already uses consistently.
- Rearrangements that do not remove code or concepts.
- Idiom details (A6a), docs (A6c), bugs (A1a–A3).
- A design point whose real harm is a bug the other agents own (an unvalidated cast, a missing check, a duplicated helper that now disagrees with the original). Report the bug's design cause only if it would remain after the bug is fixed.
- Small duplication: under about 10 repeated lines, or two call sites. Hand-rolled code that a library call could replace, unless the repo already uses that call for the same job (cite it).
- Pre-existing structure this change did not make worse.
- More than one design finding per unit: keep the one a maintainer of this repo would most likely block the merge for, or none.
## Proof plan hints
- E1 measured facts only: `wc -l` before and after, the duplicate helper's `path:line`, `grep -c` of a scattered feature check, an import edge.
## Output
`{"findings": [...]}`; `axis` `design` or `maintainability`; `type` `refactor`; `rule` required; `precedent` required.
