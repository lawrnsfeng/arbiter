You are the final author of arbiter's human-facing report design, second and last pass. You get exactly one prompt: this one. Work autonomously to completion; never ask questions. Repo: /home/lawrence/relic/arbiter (cwd). Today: 2026-11-26.

# Context (unchanged from your first pass)
- Owner has ADHD; core problem: humans cannot absorb a wall of agent-generated text. Reports must deliver more meaning with less reading. Two readers: a decider (merge / fix / check by hand, in seconds) and a technical reader (flows, states, branches; UML-like diagrams welcome when they earn it). Files are viewed offline from a Windows browser over \\wsl$.
- arbiter: Python CLI (`dependencies = []`) for evidence-gated code review, plus e2e-design / e2e-judge skills. Data model: README.md (report section), arbiter/report.py, skills/e2e-judge/SKILL.md (Outputs), skills/e2e-design/references/obligations.md. Real run: eval/results/martian/20261123233602/calcom-cal-com-pull-22532/.

# What you produced last pass (read all of it first)
- research/research-report-components.md (RM keys): rich-text presentation, the five components (verdict line; table ≤ 5 cols × 10 rows; evidence block; `<details>` fold; one must-check callout), runners-up, UML choices DG1-DG5 with triggers, text twins and ≤ 15 nodes / ≤ 20 edges.
- research/research-report-ux.md: the definitive design (E1-E16, layers L0-L3, §3.7 components, §3.8 diagrams, §3.9 renderer degrade, schema, D1-D11, plan U1-U6).
- research/mockups/report-calcom.html and research/mockups/report-calcom.md.
- Earlier evidence files: research/research-report-cognition.md (RC), research-report-prior-art.md (RP), research-report-render-stack.md (RS).

Review notes from the orchestrator on that pass:
- The HTML mock-up renders at 1440 and 390 px, no horizontal scroll, but it is 7,366 px tall at 390 px: still long for a low-working-memory reader. Question whether everything below L1 earns its place by default.
- Gate status: you claimed eslint/tsc/`npm test` "never executed" while gates.json records `status: ran` with exit 1 / 1 / 127. Verify that claim from the run's files (arbiter.log, exec/, tools/, sandbox.json) and state the evidence, or soften it.
- Requirement ids R1-R14 and finding↔requirement links were your hand join; keep that labelled.
- Only ~8 of the cited sources were re-checked by you; the rest rest on earlier agents. Re-check the load-bearing ones (any source a top rule or a cap depends on).

# Your task
1. **Research: how agents should report to humans across situations.** Survey (web_search + read primary sources; cite every claim with a URL; `[unverified]` / `[INFERENCE]` marks) the best approaches used by production agents and by human-AI interaction research, per reporting situation. Cover at least these situations:
   - S1 final result of an autonomous run (review verdict, task done)
   - S2 progress / status during a long run (minutes to hours; what to show while working, heartbeats, ETA)
   - S3 asking for a decision or approval (plan approval, choose an option, permission prompt)
   - S4 blocked / failed / partial result (what failed, what was tried, what is needed)
   - S5 handoff to another human or agent (context transfer, resumability)
   - S6 research / investigation answer (findings with confidence and sources)
   - S7 diff / change summary (what changed, risk, what to check)
   - S8 alert / incident / regression notice (interruptive; severity; next action)
   Sources to include, among others: Microsoft's Guidelines for Human-AI Interaction (Amershi et al. CHI 2019), Google PAIR People + AI Guidebook, Apple HIG on ML, Anthropic's published guidance on agents and on Claude Code behaviour/communication, OpenAI's agent / Codex / deep-research reporting formats, GitHub Copilot coding agent PR summaries, Devin, Cursor, Jules, OpenHands, Replit agent, Manus, Perplexity / deep-research citation UIs, incident-communication practice (Google SRE book, PagerDuty, Atlassian incident templates, status pages), military/business BLUF and SBAR (healthcare handoff), pilot/ATC readback and checklists, uncertainty communication (calibrated confidence, verbal probability terms, IPCC likelihood scale), notification/interruption research (cost of interruption, alert fatigue), progress-indicator research (Myers 1985, Harrison et al. on progress bars), explanation research (contrastive and selective explanation, Miller 2019). For each situation produce: the question the human has, the best-evidenced shape (ordered parts), length budget, components from the five (or a justified addition), what to never do, and an example.
2. **Map to arbiter.** Which of S1-S8 arbiter and e2e-judge actually hit (final report, live progress during a 13-47 min run, `--decide` / decision replies, INCOMPLETE runs, PR comment handoff, CI alert on BLOCK, etc.) and what each should emit. Include the terminal/live progress view if it earns it.
3. **Revise last pass's outputs** in place, keeping them terse (tables over prose, message-bearing headings, no filler):
   - research/research-report-components.md: add a situations section (or a separate file research/research-report-situations.md with key prefix `RA` if it would grow the components file past ~800 lines; then cross-link). Re-check load-bearing sources and fix or downgrade any claim that does not hold. Revisit whether the five components still win once S1-S8 are considered.
   - research/research-report-ux.md: integrate the situation model, fix anything the review notes or your new research contradict, shorten where possible. Keep source-file references valid.
   - research/mockups/report-calcom.html and .md: apply the revisions. Aim for a much shorter default view at 390 px (everything not needed for the decision folded), keep the honest "not measured" state and the clearly labelled sample panel, fix the gate-status wording to match the evidence. Add research/mockups/ examples for at least two other situations with real or clearly labelled sample data: an INCOMPLETE/blocked run (S4) and a live progress view (S2) as terminal text or HTML.
4. **Self-check the mock-ups** in a headless browser at 1440 and 390 px (no horizontal scroll, no network request, report the default-view height at 390 px before and after), and render-check every Mermaid block.

# Rules
- Edit only under research/. Do not commit or push. Do not run arbiter's tests or evals.
- Save incrementally so partial work survives a stop.
- Finish with a ≤ 25-line summary: per situation S1-S8 the recommended shape in one line; what changed in each revised file; the gate-status evidence; default-view height before/after; what you could not verify.
