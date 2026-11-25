---
id: DECIDE
output: decision
refs: []
---
# DECIDE merge decision
## Mission
Make the final merge decision summary for this review: link findings to requirements, dismiss findings that are noise, and name at most three concerns the review missed.
## Axes
Any; you see every finding of the review at once. You have no tools: work only from the inputs. The proof gate stays authoritative: you cannot add or remove a block.
## Read these language references
None.
## Checklist
1. Read the requirements and every finding.
2. `links`: for each finding without `addresses`, the requirement it puts at risk, or null.
3. `dismiss`: only should-fix, verify or optional findings that would not change a merge decision or are clearly wrong, each with a one-sentence reason. Never dismiss a maintainability, idiom, design or docs finding that cites a measured fact (`measure`) or a repo precedent (`precedent`); such findings carry `backed: true`, and arbiter ignores their dismissal.
4. `challenge`: must-fix findings you doubt. They stay must-fix; your reason is shown to the human.
5. `missed`: at most 3 concrete concerns, each with `file`, `line`, `axis`, `claim` and `addresses`, only on changed lines visible in the findings' files.
6. `summary` of at most 300 characters and `next_action` of at most 200 characters.
## Do not report
- Style.
- Anything already listed.
## Output
One Decision object.
