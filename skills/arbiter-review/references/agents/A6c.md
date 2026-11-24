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
- A doc that states the intended contract while the added code violates it: the code is wrong, not the doc. That is a bug for A1a, not a docs finding. When doc and code disagree and you cannot tell from callers, tests or the commit message which one is intended, report nothing.
- Missing or wrong docs about a failure mode (panic, undefined behaviour, error, out-of-range input) of code that should not fail that way. The failure is the bug; documenting it is not the fix.
- Missing doc comments on application code, CLI entry points, handlers or internal types; only a library's exported API counts, and only when repo precedent shows its exports are documented.
## Proof plan hints
None needed; contradictions are shown by citing the doc line and the code line. Omit `proof_plan`.
## Output
`{"findings": [...]}`; `axis` = `docs`; `severity` at most `should-fix`, unless `rule` names a repo rule heading marked `[block]`; `rule` required; `precedent` required unless `rule` is a linter id.
