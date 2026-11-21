---
id: A6a
output: findings
refs: [{"file": "idioms.md"}, {"file": "tools.md"}, {"file": "canon.md"}]
---
# A6a idiom
## Mission
Find added code that breaks the language's canon or the repo's established idiom, citing the canon rule and a repo precedent or a linter rule id for each.
## Axes
`idiom`, `maintainability` (research-axes.md §2b axes 13–14). Language-feature findings have the lowest AI precision (F1 7.85, S7); 13% of false positives come from lack of domain knowledge.
## Read these language references
`idioms.md`, `tools.md` (the tool-silent list), `canon.md` (appended below).
## Checklist
1. Walk the `idioms.md` table for the language. For each row whose pattern appears in an added line, check the added code against the row's guidance.
2. Before reporting, find a **precedent**: a line elsewhere in this repo that already follows the rule (grep for the idiomatic form). Cite it as `precedent`. If the repo consistently does the opposite, the repo convention wins: do not report.
3. `rule` must be a canon key from `canon.md` / `idioms.md` (e.g. `P8`, `EP3 Item 37`, `C-GOOD-ERR`, `GSD`), a repo rule `file#heading`, or a linter rule id. No rule, no finding.
4. If `rule` is a linter id, check that the linter is not already enabled for that rule in the repo config (then the linter reports it, not you).
5. Repo rules in the inputs override canon (`CLAUDE.md`, `AGENTS.md`, `.claude/rules/*.md`, `CONTRIBUTING.md`).
6. Prefer few, clear findings. One finding per distinct rule per unit.
## Do not report
- Anything on the tool-silent list in `tools.md` or caught by an enabled linter or formatter.
- Formatting, import order, naming taste without a rule.
- Code silenced with an ignore comment that gives a reason.
- Design or structure (A6b), docs (A6c), bugs (A1a–A3).
- Lines this change did not add.
## Proof plan hints
None needed: evolvability findings are gated on `rule` plus `precedent` or a linter id. Omit `proof_plan`.
## Output
`{"findings": [...]}`; `axis` `idiom` or `maintainability`; `type` `refactor` or `nit`; `severity` at most `should-fix`; `rule` required; `precedent` required unless `rule` is a linter id.
