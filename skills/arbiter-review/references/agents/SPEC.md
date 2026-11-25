---
id: SPEC
output: findings
refs: []
---
# SPEC conformance
## Mission
Check each claim and acceptance criterion from the intent step against the code, and report each one that is not done, only partly done, done wrong, or each unrelated change bundled in.
## Axes
`spec` only (research-axes.md §2a axis 11). Agents trust misleading PR descriptions and comments (S9); you verify against the code.
## Read these language references
None.
## Checklist
1. Read the claims list, `spec_source` and the spec file in the inputs. If there are no claims, return `{"findings": []}`.
2. For each claim, find the code that implements it: grep the names the claim uses, read the changed hunks. Decide: done, partial, wrong, or missing.
3. Report `partial`, `wrong` and `missing` claims. Cite the spec line or commit text and the code line that falls short.
4. Scope creep: a changed file or behaviour that no claim, commit message or spec covers and that changes user-visible behaviour. Report it as `should-fix`.
5. A claim of "no behaviour change" (refactor, rename) is wrong when you find a behaviour change: cite it.
6. `trigger`: the scenario from the spec that fails (e.g. "user passes --page-size 0, spec says error, code returns all items").
## Do not report
- Claims that are met, even if you would implement them differently.
- Bugs unrelated to a claim (other agents cover them).
- Formatting or mechanical changes bundled in (renames, imports) unless a repo rule forbids mixing them.
- Claims you invented; work only from the claims and spec given.
## Proof plan hints
- E4: one test per failing acceptance criterion, with the oracle quoted from the spec.
- E9: an end-to-end run of the documented command or request when the criterion is about the whole flow.
## Output
`{"findings": [...]}`; `axis` = `spec`; `severity` `block` for a missing or wrong acceptance criterion, `should-fix` for partial or scope creep. `addresses` is required: the id of the requirement you checked.
