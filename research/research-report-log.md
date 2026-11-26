# Report UX research: session log (2026-11-26)

How the `research-report-*.md` files were produced, so the context survives the session. The design itself is in
[research-report-ux.md](research-report-ux.md); this file records the question, who researched what, the prompts,
and what the orchestrator checked.

## Question (owner, verbatim intent)

Research a comprehensive report of functional requirements, implementation status, logic branches and test
coverage. People cannot absorb a wall of agent-generated text (the owner has ADHD); the report needs rich formatting
and graphical components (HTML with diagrams, rich JSON views, more) that deliver more with less reading. Follow-ups:
study how agents should present data to humans in rich text, pick the 5 most comprehensible markup components, use
UML for technical readers; then research how agents report to humans across situations and revise the outputs.

## Passes

| Pass | Who | Brief | Output |
|---|---|---|---|
| 0 | orchestrator (Opus) | inventory of arbiter's report data: `arbiter/report.py`, run files of `eval/results/martian/20261123233602/calcom-cal-com-pull-22532/`, e2e-judge outputs | §1 Problem of research-report-ux.md |
| 1a | task agent (Opus) | cognition: cognitive load, visual encoding, scanning, accessibility and ADHD, SE studies on review output, coverage and alerts; ranked design rules with evidence strength | [research-report-cognition.md](research-report-cognition.md) (RC) |
| 1b | task agent (Opus) | prior art: coverage, mutation, test-report, traceability, AI-review, SARIF, risk-map and branch-view tools; pattern catalogue | [research-report-prior-art.md](research-report-prior-art.md) (RP) |
| 1c | task agent (Opus) | render stack: single-file HTML, escaping and CSP, diagram and JSON-viewer libraries with measured sizes, generative-UI specs, data standards, schema sketch | [research-report-render-stack.md](research-report-render-stack.md) (RS) |
| 1d | orchestrator | synthesis of 1a-1c | first version of [research-report-ux.md](research-report-ux.md) |
| 2 | Fable (`anthropic/claude-fable-5-2`, thinking high, `--max-cost 30`), one prompt via `omp -p` | rich-text presentation, the 5 most comprehensible markup components, UML for technical readers, final design, mock-ups | prompt: [prompts/2026-11-26-fable-report-pass1.md](prompts/2026-11-26-fable-report-pass1.md); output: [research-report-components.md](research-report-components.md) (RM), revised research-report-ux.md, [mockups/](mockups/) |
| 3 | Fable, same settings, one prompt | reporting per situation S1-S8 (final result, progress, decision request, blocked, handoff, research answer, change summary, alert); revise pass 2 outputs | prompt: [prompts/2026-11-26-fable-report-pass2.md](prompts/2026-11-26-fable-report-pass2.md); output: see §Pass 3 |

All four agents in pass 1 had the same contract: read-only, primary sources, every claim with a URL, `[unverified]`
and `[INFERENCE]` marks, a sources table with their key prefix, findings, ranked implications.

## Orchestrator checks

| Pass | Check | Result |
|---|---|---|
| 1d | Counted the baseline `report.md` | 185 lines, 8 findings, gate list repeated 15 times |
| 2 | Opened `mockups/report-calcom.html` in headless Chromium | renders at 1440 and 390 px, no horizontal scroll; 7,366 px tall at 390 px (too long: raised in pass 3) |
| 2 | Fable's "eslint, tsc, `npm test` never executed" | `gates.json` records `status: ran` with exit 1 / 1 / 127; not confirmed by the orchestrator, sent back for evidence in pass 3 |

## Pass 2 summary (Fable)

- Five components: verdict line; table (≤ 5 columns × 10 rows); evidence block (`path:line`, ≤ 6-line snippet,
  before/after); `<details>` fold; one callout with the must-check list. Runners-up: diagram, stand-alone checklist,
  status strip, definition list, cards.
- Diagrams, none by default, each with a trigger, a text twin and ≤ 15 nodes / ≤ 20 edges: DG1 requirement trace,
  DG2 activity (paths taken and asserted), DG3 flat state machine, DG4 sequence (value to failure), DG5 component.
  Not emitted: communication, class, C4, nested states.
- Found in the cal.com run: the PASS hid 4 candidates dropped by intake rules (one raised as a blocker); tier counts
  by `tier()` are 1 should-fix and 7 optional where the old report listed 6 should-fix.
- Not verified: GitHub rendering of alerts and task lists, Windows over `\\wsl$`, Firefox, Safari, screen readers;
  only about 8 sources re-checked by Fable itself; requirement ids and finding links in the mock-ups are a hand join.

## Pass 3

Output: [research-report-situations.md](research-report-situations.md) (RA1–RA57, A1–A23, new); revised
research-report-components.md, research-report-ux.md (rewritten), `mockups/report-calcom.{html,md}`; new
`mockups/report-incomplete.html` (S4, labelled sample data) and `mockups/progress-live.txt` (S2).

| Situation | Shape, in order |
|---|---|
| S1 final result | verdict word + reason → next action → one needs-you list (fixes, then checks) → folds |
| S2 progress | one status line (stage k/9, real counter, elapsed, typical range, last-event age) → one line per finished stage → warn the moment a result is lost; no percent bar, no single ETA |
| S3 decision | closed question → recommended option first → ≤ 4 numbered options with consequences → what happens with no reply |
| S4 failed / partial | non-success state word → cause + verbatim error → what was tried → what still stands → what is unknown → one command, with rerun cost |
| S5 handoff | state → goal → done with artefact paths → decisions → ordered next steps → risks → pointers; to an agent, `report.json` only |
| S6 research answer | answer → claims each beside source and strength → confidence word from a defined scale → not verified |
| S7 change summary | imperative what → why → change map with risk → what to check first → verify command |
| S8 alert | severity + symptom + where → impact → one action; only BLOCK and INCOMPLETE alert |

Other changes: the five components hold across S1–S8 (S2 adds a status line and stage list, S3 numbered options);
the callout is redefined as "what needs the human"; RM20 and RM62 corrected; E1 and E11 numbers corrected; E17–E19,
§3.10 situation map, D12–D16 and U7–U8 added; the default view is cut to verdict + needs-you list.

Gate finding (now evidenced): the commands ran, the tools did not. `gates.json` records `status: ran` for all 15
gate rows, but `exec/<id>.json` shows eslint `npx canceled due to missing packages`, tsc `ENOTCACHED`, npm test
`jest: not found`; root cause `npm install` exit 1 (`ERESOLVE`) on every fetch while `sandbox.json` reads `ready`.
The mock-ups now say "no result". Ledger row A-18.

Not verified by Fable: Myers 1985 primary (rests on Nielsen's citation); RM62 flaw thresholds; vendor numbers
(sandboxing −84% prompts, Devin merge rate); Cursor and Perplexity pages (no claim rests on them); several RA
sources read as abstracts only; GitHub rendering of alert + task list; Windows over `\\wsl$`, screen reader, print.
All budgets (px, lines, items, heartbeat interval) are inference until reader test U5 runs.

Orchestrator checks after pass 3:

| Check | Result |
|---|---|
| `report-calcom.html` at 390 px, headless Chromium | 1,958 px tall (was 7,366), no horizontal scroll |
| `report-incomplete.html` at 390 px | 1,926 px tall, no horizontal scroll; sample-data banner visible |
| Gate claim | 10 `exec/*.json` files carry the missing-package / `ENOTCACHED` / `jest: not found` errors; `ERESOLVE` present; `sandbox.json` status `ready` |
