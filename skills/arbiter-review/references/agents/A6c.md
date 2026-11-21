---
id: A6c
output: findings
refs: [{"file": "idioms.md", "rows": ["Docs"]}]
---
# A6c docs
## Mission
Find documentation the change makes wrong or leaves missing: docstrings and comments that contradict the code, undocumented new public API, and comments that say what instead of why.
## Axes
`docs` (research-axes.md §2b axis 16; textual findings F1 14.3, S7).
## Read these language references
`idioms.md` rows Docs (appended below).
## Checklist
1. Contradiction: an added or untouched docstring, comment, README line or example in the unit whose statement the added code now makes false (parameter names, return value, raised errors, defaults, units). Cite both the doc line and the code line.
2. Stale reference: a doc that names a function, flag or env var the change renamed or removed (grep for the old name).
3. Missing docs on new public API, when the language canon or repo rules require them (e.g. Go exported identifiers, Rust `missing_docs` policy, PEP 257 for public modules). Cite the rule.
4. "What" comments that restate the next line; leave them as `nit` only when a repo rule bans them.
5. User-visible behaviour change with no changelog entry, when the repo keeps a changelog (glob `CHANGELOG*`).
6. `rule` is a canon key, repo rule `file#heading` or linter id; `precedent` is a repo `path:line` that follows the rule.
## Do not report
- Spelling and grammar, unless it changes meaning.
- Missing docs on private code.
- Docs rules an enabled linter enforces.
- Code behaviour itself (that is a bug for A1a).
## Proof plan hints
None needed; contradictions are shown by citing the doc line and the code line. Omit `proof_plan`.
## Output
`{"findings": [...]}`; `axis` = `docs`; `severity` at most `should-fix`; `rule` required; `precedent` required unless `rule` is a linter id.
