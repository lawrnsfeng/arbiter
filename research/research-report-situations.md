# How an agent reports to a human, per situation: research (2026-11-26, prefix RA)

Scope: the shape of an agent's message in eight situations (S1–S8), and which of them arbiter and e2e-judge hit.
Adds to [research-report-components.md](research-report-components.md) (RM), [research-report-cognition.md](research-report-cognition.md) (RC)
and [research-report-prior-art.md](research-report-prior-art.md) (RP); repeats none of them. The design that uses it:
[research-report-ux.md](research-report-ux.md) §3.10. Examples: [mockups/progress-live.txt](mockups/progress-live.txt) (S2),
[mockups/report-incomplete.html](mockups/report-incomplete.html) (S4), [mockups/report-calcom.html](mockups/report-calcom.html) (S1).

Tags: `[unverified]` = source not opened or text not found in it. `[INFERENCE]` = my deduction. `[vendor]` = a
vendor's own claim, no independent test. Strength as in RM: **strong**, **moderate**, **weak**, **opinion**, **normative**.
Every RA source below was opened and the cited text found in it on 2026-11-26, except where a row says otherwise.

## 1. Sources

### 1.1 Human-AI guidance and research

| Key | Source | URL |
|---|---|---|
| RA1 | Amershi et al. (2019). Guidelines for Human-AI Interaction. CHI. 18 guidelines, tested by 49 practitioners on 20 products | https://www.microsoft.com/en-us/research/uploads/prod/2019/01/Guidelines-for-Human-AI-Interaction-camera-ready.pdf |
| RA2 | Google PAIR, People + AI Guidebook: Explainability + Trust | https://pair.withgoogle.com/chapter/explainability-trust/ |
| RA3 | Google PAIR, People + AI Guidebook: Errors + Graceful Failure | https://pair.withgoogle.com/chapter/errors-failing/ |
| RA4 | Apple Human Interface Guidelines: Machine learning (updated 2026-06-08) | https://developer.apple.com/design/human-interface-guidelines/machine-learning |
| RA5 | Miller (2019). Explanation in Artificial Intelligence: Insights from the Social Sciences. *Artif Intell* 267 (arXiv PDF, §1.2) | https://arxiv.org/pdf/1706.07269 |
| RA29 | Liu, Zhang, Liang (2023). Evaluating Verifiability in Generative Search Engines (abstract) | https://arxiv.org/abs/2304.09848 |
| RA30 | Steyvers et al. (2025). What large language models know and what people think they know. *Nat Mach Intell* 7 | https://www.nature.com/articles/s42256-024-00976-7 |
| RA31 | Kim, Liao, Vorvoreanu, Ballard, Vaughan (2024). "I'm Not Sure, But...". FAccT (abstract) | https://arxiv.org/abs/2405.00623 |
| RA32 | Vasconcelos et al. (2023). Explanations Can Reduce Overreliance on AI Systems During Decision-Making. CSCW (abstract) | https://arxiv.org/abs/2212.06823 |
| RA33 | Buçinca, Malaya, Gajos (2021). To Trust or to Think: Cognitive Forcing Functions. CSCW (abstract) | https://arxiv.org/abs/2102.09692 |

### 1.2 Agent vendors: published guidance, prompts and product docs

| Key | Source | URL |
|---|---|---|
| RA6 | Anthropic: Building effective agents | https://www.anthropic.com/engineering/building-effective-agents |
| RA7 | Anthropic: Our framework for developing safe and trustworthy agents (2025-08-04) | https://www.anthropic.com/news/our-framework-for-developing-safe-and-trustworthy-agents |
| RA8 | Anthropic: How we built our multi-agent research system | https://www.anthropic.com/engineering/multi-agent-research-system |
| RA9 | Anthropic: Effective context engineering for AI agents | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| RA10 | Anthropic: Effective harnesses for long-running agents | https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |
| RA11 | Anthropic: Beyond permission prompts (Claude Code sandboxing) | https://www.anthropic.com/engineering/claude-code-sandboxing |
| RA12 | Anthropic docs: Prompting Claude Opus 5 (user-facing progress updates, written deliverable length) | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5 |
| RA13 | Anthropic: Claude Code best practices ("ask Claude for evidence") | https://www.anthropic.com/engineering/claude-code-best-practices |
| RA14 | Claude Code docs: permission modes; permissions | https://code.claude.com/docs/en/permission-modes ; https://code.claude.com/docs/en/permissions |
| RA15 | OpenAI Codex CLI base prompt, `codex-rs/models-manager/prompt.md` (`main`) | https://raw.githubusercontent.com/openai/codex/main/codex-rs/models-manager/prompt.md |
| RA16 | OpenAI Codex CLI prompt for GPT-5-Codex, `codex-rs/core/gpt_5_codex_prompt.md` (`main`) | https://raw.githubusercontent.com/openai/codex/main/codex-rs/core/gpt_5_codex_prompt.md |
| RA17 | OpenAI Cookbook: GPT-5 prompting guide (tool preambles) | https://cookbook.openai.com/examples/gpt-5/gpt-5_prompting_guide |
| RA18 | OpenAI: Introducing Codex | https://openai.com/index/introducing-codex/ |
| RA19 | OpenAI: Introducing deep research | https://openai.com/index/introducing-deep-research/ |
| RA20 | OpenAI API docs: Deep research (inline citations, `url_citation` annotations, background mode) | https://platform.openai.com/docs/guides/deep-research |
| RA21 | GitHub Docs: Managing agent sessions; Review output from Copilot | https://docs.github.com/en/copilot/how-tos/copilot-on-github/use-copilot-agents/manage-and-track-agents ; https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/review-copilot-prs |
| RA22 | Cognition: Devin 2.1 (confidence ratings) `[vendor]` | https://cognition.com/blog/devin-2-1 |
| RA23 | Jules docs: Reviewing plans & giving feedback; Running tasks | https://jules.google/docs/review-plan ; https://jules.google/docs/running-tasks |
| RA24 | Replit docs: Replit Agent (task plan, checkpoints) | https://docs.replit.com/replitai/agent |
| RA25 | OpenHands software-agent-sdk: `finish` tool description (`main`) | https://raw.githubusercontent.com/OpenHands/software-agent-sdk/main/openhands-sdk/openhands/sdk/tool/builtins/finish.py |
| RA26 | Manus: Context Engineering for AI Agents (todo.md recitation; keep the wrong stuff in) | https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus |
| RA27 | Cognition: Don't Build Multi-Agents | https://cognition.ai/blog/dont-build-multi-agents |
| RA28 | Model Context Protocol 2025-06-18: Elicitation | https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation |

### 1.3 Uncertainty, progress, interruption

| Key | Source | URL |
|---|---|---|
| RA34 | Mastrandrea et al. (2010). IPCC AR5 Guidance Note on Consistent Treatment of Uncertainties | https://www.ipcc.ch/site/assets/uploads/2018/05/uncertainty-guidance-note.pdf |
| RA35 | Budescu, Broomell, Por (2009). Improving communication of uncertainty in the reports of the IPCC. *Psychol Sci* 20 (abstract) | https://pubmed.ncbi.nlm.nih.gov/19207697/ |
| RA36 | Budescu, Por, Broomell, Smithson (2014). The interpretation of IPCC probabilistic statements around the world. *Nat Clim Change* 4 | https://www.nature.com/articles/nclimate2194 |
| RA37 | van der Bles, van der Linden, Freeman, Spiegelhalter (2020). The effects of communicating uncertainty on public trust. *PNAS* 117 (abstract) | https://pubmed.ncbi.nlm.nih.gov/32205438/ |
| RA38 | Nielsen (1993, upd.). Response Times: The 3 Important Limits (cites Myers 1985) | https://www.nngroup.com/articles/response-times-3-important-limits/ |
| RA39 | Nielsen/NN/g. Progress Indicators Make a Slow System Less Insufferable | https://www.nngroup.com/articles/progress-indicators/ |
| RA40 | Harrison, Amento, Kuznetsov, Bell (2007). Rethinking the Progress Bar. UIST | https://www.chrisharrison.net/projects/progressbars/ProgBarHarrison.pdf |
| RA41 | Harrison, Yeo, Hudson (2010). Faster Progress Bars. CHI (abstract) | https://www.chrisharrison.net/projects/progressbars2/ProgressBarsHarrison.pdf |
| RA42 | Myers (1985). The importance of percent-done progress indicators. CHI. `[unverified: the PDF did not convert; read only as cited by RA38]` | https://dl.acm.org/doi/10.1145/317456.317459 |
| RA43 | Mark, Gudith, Klocke (2008). The Cost of Interrupted Work: More Speed and Stress. CHI | https://ics.uci.edu/~gmark/chi08-mark.pdf |
| RA44 | Iqbal & Bailey (2008). Effects of Intelligent Notification Management on Users and Their Tasks. CHI | https://interruptions.net/literature/Iqbal-CHI08.pdf |

### 1.4 Incidents, alerts, handoff, briefing, failure and change reports

| Key | Source | URL |
|---|---|---|
| RA45 | Google SRE book ch. 6: Monitoring Distributed Systems | https://sre.google/sre-book/monitoring-distributed-systems/ |
| RA46 | Google SRE book ch. 14: Managing Incidents | https://sre.google/sre-book/managing-incidents/ |
| RA47 | PagerDuty Incident Response: Incident Commander training | https://response.pagerduty.com/training/incident_commander/ |
| RA48 | Atlassian: Incident communication best practices; templates | https://www.atlassian.com/incident-management/incident-communication ; https://www.atlassian.com/incident-management/incident-communication/templates |
| RA49 | Atlassian Statuspage: Create an incident (four states) | https://support.atlassian.com/statuspage/docs/create-an-incident/ |
| RA50 | Prometheus docs: Alerting practices | https://prometheus.io/docs/practices/alerting/ |
| RA51 | AHRQ TeamSTEPPS: SBAR | https://www.ahrq.gov/teamstepps-program/curriculum/communication/tools/sbar.html |
| RA52 | Starmer et al. (2014). Changes in medical errors after implementation of a handoff program (I-PASS). *NEJM* 371 (abstract) | https://pubmed.ncbi.nlm.nih.gov/25372088/ |
| RA53 | FAA Aeronautical Information Manual 4-4-7: pilot responsibility, clearance readback | https://www.faa.gov/air_traffic/publications/atpubs/aim_html/chap4_section_4.html |
| RA54 | US Army AR 25-50 §1-38: standards for Army writing (closes RC56 `[unverified]`) | https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN42124-AR_25-50-007-WEB-13.pdf |
| RA55 | NN/g: Error-Message Guidelines | https://www.nngroup.com/articles/error-message-guidelines/ |
| RA56 | Tatham: How to Report Bugs Effectively | https://www.chiark.greenend.org.uk/~sgtatham/bugs.html |
| RA57 | Google eng-practices: Writing good CL descriptions | https://google.github.io/eng-practices/review/developer/cl-descriptions.html |

## 2. Findings

| # | Finding (n, effect, year) | Keys | Strength |
|---|---|---|---|
| A1 | **Outcome first, in one reading.** Army standard: "understood by the reader in a single rapid reading", main point at the beginning (bottom line up front), active voice. Anthropic: "lead with the outcome: your first sentence should answer 'what happened' or 'what did you find'". Codex: lead with the change, never with "summary". | RA54, RA12, RA16; RC F19–F23 | opinion (three independent guides); moderate with RC |
| A2 | **A review reports findings before any summary.** Codex prompt: findings first, ordered by severity with file and line; then open questions and assumptions; the change summary last. With no findings: say so and name "residual risks or testing gaps". | RA16 | opinion (vendor prompt) |
| A3 | **Evidence is the command and its output.** "'All tests pass' on its own tells you very little"; for a session nobody watched "it's also the only evidence you have". Codex cites terminal logs and test outputs for each step. | RA13, RA18 | opinion (two vendors) |
| A4 | **Length raises trust without raising accuracy.** Users overestimate the accuracy of LLM answers shown with default explanations; longer explanations raised confidence even when accuracy did not change. Shorter is safer, not only faster. | RA30 | moderate (experiments) |
| A5 | **Say "not sure" in the first person, where it applies.** First-person uncertainty ("I'm not sure, but…") lowered agreement with the system and raised participants' accuracy by cutting overreliance on wrong answers. Communicating uncertainty costs little trust (small decrease, mostly for verbal forms). | RA31, RA37 | moderate |
| A6 | **A bare probability word is misread.** People read IPCC terms closer to 50% than intended, even with the scale in hand; adding the numeric range to the word improved agreement in 25 samples, 24 countries, 17 languages. The IPCC separates *likelihood* (a probability range per word) from *confidence* (evidence and agreement). | RA34, RA35, RA36 | strong |
| A7 | **Confidence as a category that names the action.** PAIR: categories such as High / Medium / Low, and "clearly indicate what action a user should take under each category". Apple: translate confidence "into concepts that people already understand" and convey it "in terms of actionable suggestions". Devin shows 🟢 🟡 🔴 and reports 🟢 as twice as likely to end in a merged PR `[vendor]`. | RA2, RA4, RA22 | opinion (guidance); weak (vendor number) |
| A8 | **A citation is not proof.** In four generative search engines 51.5% of sentences were fully supported by their citations and 74.5% of citations supported their sentence. Deep-research products attach the URL, title and location per claim. A cited source must have been opened, and the reader needs the quote. | RA29, RA20, RA8 | moderate |
| A9 | **Explanations are contrastive and selected.** People ask why P *rather than* Q, expect one or two causes, and prefer a cause to a probability. Explanations cut overreliance only when they make checking cheaper than trusting. | RA5, RA32 | strong (review); moderate |
| A10 | **Over 10 s: show progress and when it ends.** 0.1 s / 1 s / 10 s limits; beyond 10 s give percent-done feedback and the expected finish. When step durations are unknown, show the number of steps instead of a percentage. Do not use a static indicator. | RA38, RA39, RA42 | moderate (classic; Myers primary unread) |
| A11 | **A bar that stalls near the end feels slow.** n = 22, 9 progress functions: bars with pauses were perceived as taking longer; the three with pauses near the end were all perceived as slower than linear; accelerating progress was favoured. A 2010 follow-up cut perceived duration by 11% with animation alone: these are effects on perception, not on speed. An honest step counter beats a percentage that the agent cannot keep moving `[INFERENCE]`. | RA40, RA41 | moderate (small n) |
| A12 | **Progress narration has a ceiling.** Anthropic: "Too little information leaves humans unable to assess whether the agent is on track… Too much can overwhelm them with irrelevant details". Opus 5 guidance: one sentence before the first tool call, then an update "only when you find something important or change direction". Codex: preambles of 1–2 sentences (8–12 words for quick updates), related actions grouped; a plan tool renders steps so the text need not repeat them. | RA7, RA12, RA15, RA17 | opinion (vendors agree) |
| A13 | **Interruptions cost stress, not time.** n = 48: interrupted tasks were finished faster with equal quality, at the price of more stress, frustration, time pressure and effort. Notifications delivered at task breakpoints cut frustration and reaction time (n = 16). | RA43, RA44 | moderate |
| A14 | **A page must be urgent, actionable, need a human and be new.** "Every page should be actionable"; "if a page merely merits a robotic response, it shouldn't be a page". Alert on symptoms; keep causes one link away. Acceptance of reminders fell 30% per extra reminder (RC F44, re-read). | RA45, RA50; RC43 | opinion (practice) + moderate (field data) |
| A15 | **An incident message names its state and the next update.** Four states: investigating, identified, monitoring, resolved. Never more than one hour without an update while customers are affected; "always indicate when to expect the next update". Updates are "short and factual": what is happening, what we are doing. | RA48, RA49, RA47 | opinion (practice) |
| A16 | **A structured handoff cuts errors.** I-PASS in 9 hospitals, 10,740 admissions: medical errors −23% (24.5 → 18.8 per 100), preventable adverse events −30%. SBAR orders any request: situation, background, assessment, recommendation or request. | RA52, RA51 | strong (I-PASS, before/after multi-site); opinion (SBAR) |
| A17 | **The receiver confirms.** Pilots read back the numbers of a clearance "as a means of mutual verification". An incident commander hands over with "You're now the incident commander, okay?" and waits for a firm acknowledgement. | RA53, RA46 | normative / opinion |
| A18 | **Agent-to-agent handoff: brief, artefacts, full trace.** A subagent brief needs "an objective, an output format, guidance on the tools and sources to use, and clear task boundaries". Results go to files, not through a paraphrase ("game of telephone"); a subagent returns 1,000–2,000 tokens. Across sessions: a progress file, the git history and a feature list. Decisions are implicit in actions, so hand over the trace, not only the message. | RA8, RA9, RA10, RA27 | opinion (vendors, partly conflicting on multi-agent) |
| A19 | **Ask rarely, ask closed, show the consequence, give a default.** Approval fatigue: users stop reading what they approve; sandboxing cut prompts by 84% `[vendor]`. A permission prompt "shows what Claude is about to do, followed by your options". Apple: few, diverse options, the most likely first. Codex: numbered options "so the user can quickly respond with a single number". Jules shows a plan and auto-approves on a timer; Replit shows an ordered task list with accept and revise. MCP elicitation offers accept, decline and cancel and shows who asks. HAI guideline G16: convey the consequences of user actions. | RA11, RA14, RA4, RA16, RA23, RA24, RA28, RA1 | opinion (convergent practice); weak (vendor number) |
| A20 | **A failure report gives the exact error, what was tried and a way forward.** PAIR: "provide paths forward from failure". NN/g: describe the issue "concisely and precisely", constructive, no blame. Bug-report practice: what you did, what you saw, what you expected, verbatim. OpenHands' finish message: summary of actions and results, next steps, "explanation if you're unable to complete the task", follow-up questions. Anthropic: agents "pause for human feedback at checkpoints or when encountering blockers". Manus keeps failed actions in the trace. | RA3, RA55, RA56, RA25, RA6, RA26 | opinion (convergent practice) |
| A21 | **A change description says what, then why, then how it was checked.** First line: a short imperative summary of what is done; body: the problem, why this approach, shortcomings. Codex: "where and why a change was made", then next steps. | RA57, RA16 | opinion (practice) |
| A22 | **Scope down when unsure.** HAI G10: "engage in disambiguation or gracefully degrade the AI system's services when uncertain". G2: make clear how well the system can do what it does. | RA1 | moderate (validated guideline set) |
| A23 | **The interventions that cut overreliance most are liked least.** Cognitive forcing reduced overreliance more than plain explanations and got the worst subjective ratings. A must-check list will feel like friction; that is the price. | RA33 | moderate |

No source measures any of this on agent *reports* read by developers with ADHD. The S1–S8 shapes below are
syntheses `[INFERENCE]`; each line of "Basis" says what they rest on.

## 3. Eight situations

Budgets are `[INFERENCE]` from the cited limits unless a source gives the number.

| # | Situation | The human's question | Shape, in order | Budget (default view) | Components |
|---|---|---|---|---|---|
| S1 | Final result | Is it done; can I merge; what do I do now; what did you not check? | outcome word + one reason → next action → what needs me (fixes, then checks) → evidence per item (folded) → the rest (folded) | decision in ≤ 3 lines; ≤ 7 items; ≤ 2 phone screens | verdict line, callout, evidence block, fold; table folded |
| S2 | Progress | Is it alive; how far; how long; must I act now? | one status line: stage k of n, counter, elapsed, typical range, age of last event → one line per finished stage with its result → early warning when a result is already lost | 1 line live; 1 line per stage; silence between changes | **addition:** status line + stage list |
| S3 | Decision / approval | What exactly do you need; what happens per choice; what do you recommend? | the question, closed → recommended option first → ≤ 4 options, each label + consequence → what happens with no reply → reply token | ≤ 6 lines; one question per message | callout holding **numbered options** (addition); verdict line |
| S4 | Blocked / failed / partial | What state is it in; why; what is still usable; what do you need? | state word that is not a success word → what failed, the cause, the exact error → what was tried → what still stands → what is not known → one needed action, as a command | ≤ 10 lines; error ≤ 3 lines verbatim | verdict line, evidence block, callout (the needed action), fold |
| S5 | Handoff | What is the goal; where are we; what is decided; what is next; what must I not redo? | state in one line → goal and acceptance → done, with artefact paths → decisions and why → next actions in order → open risks with "if X then Y" → pointers → acknowledgement | ≤ 25 lines to a human; 1–2 k tokens to an agent; the trace by path | verdict line, table, evidence block (paths, commands), fold |
| S6 | Research answer | What is the answer; how sure; on what grounds; what is missing? | answer in 1–2 sentences → claims, each with its source and strength beside it → confidence word from a defined scale with its basis → why this and not the alternative → not found, not verified → sources | answer ≤ 3 sentences; ≤ 7 claims before a fold | verdict line, table, evidence block (quote + URL), callout (unverified), fold |
| S7 | Change summary | What changed; why; how risky; where do I look first? | one imperative line: what → why → change map grouped by unit with a risk word → what to check first → how it was verified (command + result) → not covered | first line ≤ 72 characters; body ≤ 15 lines; map ≤ 10 rows | verdict line, table, evidence block, fold; one diagram on its trigger |
| S8 | Alert | Must I act now; on what; how? | severity word + symptom + where, in the title → impact in one line → the one action with its link → when the next update comes, or that none will | title ≤ 60 characters; body ≤ 3 lines; one alert per root cause | verdict line only (+ one evidence anchor) |

### S1 Final result

| | |
|---|---|
| Basis | A1, A2, A3, A4, A5, A9; RM55 (a focused instruction raised detection odds 8×); RC F44, F51 |
| Never | Open with what the agent did ("I first read…"). Give a success word when a part was skipped or produced no result. Write "tests pass" without the command and its output. Put the summary before the findings. Add length to look thorough (A4). |
| Why "needs me" is one list | Proven fixes and unverified checks are both the reader's to-dos. Two lists made the cal.com default view 7,366 px at 390 px. One ordered list, glyph and word per item (▲ fix, ○ check), keeps the difference visible. `[INFERENCE]` |

```text
▲ PASS with follow-ups · cal.com 30a92a4..5fd11f9
0 must fix · 1 should fix · 6 to check by hand · 7 optional
Next: fix #1 or reply `decision: <why>`, then do the 6 checks.
```

### S2 Progress during a long run

| | |
|---|---|
| Basis | A10, A11, A12, A13, A14; RA19 (a side panel lists steps taken and sources; a notification on completion); RA21 (session log, token use, session length); RA10 (progress file) |
| What to show | Stage k of n and its name; a real counter (agent runs done of scheduled); elapsed time; the typical range of past runs, not a point estimate; the age of the last event, so a hang is visible; proven blockers so far. |
| What to raise early | A result that is already lost: on cal.com the dependency install failed in minute 1 and the report said so in minute 28. Print it when it happens, with the consequence ("lint, types and tests will give no result"). |
| Never | A spinner alone for more than 10 s. A percent bar or a single ETA the agent cannot keep (A11). One line per tool call (A12). A notification for anything the human cannot act on (A14). |
| Two forms | TTY: the status line is rewritten in place, finished stages scroll above it. CI log: one line per stage transition, plus a heartbeat line when a stage runs long (interval `[INFERENCE]`: 5 min). |

Example: [mockups/progress-live.txt](mockups/progress-live.txt).

### S3 Asking for a decision or approval

| | |
|---|---|
| Basis | A19, A9, A16 (SBAR's R), A13, A14, A23; RC F44 |
| Never | An open "what do you think?". A question the tools can answer. One prompt per action (fatigue). A choice without its consequence or without a default. The question at the end of a long report. |
| Reply | One token: a number, `approve`, or arbiter's `decision: <why>`. The agent reads the reply back in its next message (A17). |

```text
○ DECISION NEEDED · e2e-judge Q1 · blocks 3 of 41 obligations          (sample data)
Is a retry after a gateway 503 required, or allowed?
  1. Required (recommended: the issue says "must retry")  → 3 tests must assert the second request
  2. Allowed                                               → the 3 obligations become must-not only
  3. Out of scope                                          → the 3 obligations are dropped and listed
No reply: the judge reports GAPS with Q1 open.
```

### S4 Blocked, failed or partial

| | |
|---|---|
| Basis | A20, A22, A15, A3, A17; arbiter's own rule that "a gate must not pass on silence" (`arbiter/pipeline.py` `_withhold`) |
| State words | INCOMPLETE (no verdict), BLOCKED (waits for a human answer), PARTIAL (a verdict with named holes). None of them is green or red by default. |
| Never | A PASS on silence. "An error occurred". Exit code 0. Dropping the results that did complete. Retrying without saying so. A needed action that is not a command or a concrete answer. |
| What still stands | List it under its own heading and mark it partial: a proven finding stays proven when later calls fail; "no finding" in a unit whose finder failed is not a result. |

Example: [mockups/report-incomplete.html](mockups/report-incomplete.html).

### S5 Handoff to another human or agent

| | |
|---|---|
| Basis | A16, A17, A18, A3 |
| Never | A narrative of the session. A paraphrase of data that exists as a file. "Done" without the artefact path. Decisions left implicit. A handoff nobody acknowledges. |
| To an agent | Objective, output format, boundaries, tools; the run directory and `report.json` by path; no prose summary of the findings. |

```text
▲ PASS with follow-ups · cal.com #22532 · arbiter run 20261123233602
Goal: merge when #1 is fixed or waived and the 6 checks are done.
Done: 16 candidates judged down to 8 findings; 6 of 7 proofs confirmed (report.json, proofs/).
Decided: 3 candidates rejected as false positives (f003, f008, f010; votes.json).
Next, in order: 1 fix #1 · 2 run lint, tsc and jest locally · 3 confirm R12–R14.
Risk: if `npm install` still fails with ERESOLVE, the three gates stay without a result.
```

### S6 Research or investigation answer

| | |
|---|---|
| Basis | A4, A5, A6, A7, A8, A9 |
| Confidence scale | A fixed list of words, each defined by the kind of evidence, as the IPCC and this file do (strong, moderate, weak, opinion). arbiter's rungs E1–E4 and "proven / verified / unproven" are already such a scale; print the word, define it once. |
| Never | A probability word without its scale (A6). A percentage that was not measured. A source that was not opened (A8). A sources list detached from the claims. Hedging every sentence: mark the uncertain claims only (A5). |

### S7 Diff or change summary

| | |
|---|---|
| Basis | A21, A3, A9; RC F51 (order steers attention); RP P16, P21; RM U25 (median largest call-graph cluster = 5 functions) |
| Never | Restating the diff line by line. A flat file list. "Various improvements". A risk word with no basis. A default diagram. |

### S8 Alert, incident, regression notice

| | |
|---|---|
| Basis | A14, A13, A15; RM56 (repeated warnings lose effect) |
| Never | An alert on PASS. One alert per finding. An alert for should-fix or optional items. The same alert twice for an unchanged state. Severity by colour alone. |

```text
✖ arbiter BLOCK · <repo> #<pr> · 1 proven blocker                      (sample data)
<path>:<line> <claim in ≤ 10 words> (repro test exits 1)
Fix it, then re-run. Report: <run>/report.html#f1
```

## 4. Which situations arbiter and e2e-judge hit

"Today" is the code on 2026-11-26 (`arbiter/pipeline.py`, `arbiter/cli.py`, `arbiter/report.py`, `skills/e2e-judge/SKILL.md`).

| Output | Situation | Today | Should emit |
|---|---|---|---|
| `report.md`, `report.html`, last stdout line | **S1** | title with verdict and counts, next action, requirement table, tiers, folds | verdict line with the unverified count; one "needs you" list; everything else folded (UX §3.1) |
| stdout during a run (27 min 46 s measured on cal.com; 13–47 min per the task brief `[unverified]`) | **S2** | one line: the run path. Then silence until `verdict …`. Retries go to stderr. | status line + stage list; early warning when a gate or the sandbox loses a result; `progress.jsonl` for tools |
| `decision: <why>` reply to a should-fix; `--decide` challenges; verify-tier items; e2e-judge "Open questions" | **S3** | "fix or reply `decision: <why>`" in the tier title; questions as a bullet list | each question closed, with numbered options, the consequence per option and what happens with no reply. arbiter itself never asks mid-run (README: "It never asks questions"); keep that. |
| INCOMPLETE (exit 5, "verdict withheld"); exit 2, 3, 4; a gate whose tool is missing; e2e-judge obligations "blocked on questions" | **S4** | `⚪ INCOMPLETE` + "rerun; too many agent calls failed to give a verdict." | state, cause with the exact error, what was tried, what still stands, what is unknown, the rerun command and its cost |
| PR comment; `report.json`, SARIF; e2e-judge "Owed" | **S5** | the report itself | comment = S1 shape + pointers; `report.json` is the agent handoff: no prose needed |
| evidence rungs, "proven / verified / unproven", research files in `research/` | **S6** | rung codes (E1–E4) with no legend | the word with the rung; one line that defines the scale |
| units and files in the coverage fold; e2e-judge freeze | **S7** | one long bullet | units table with churn and findings; DG5 on its trigger |
| exit 1 on BLOCK in CI; (later) a regression against the previous run | **S8** | `verdict BLOCK · report <absolute path>` | one line: severity, count, first blocker with `path:line`, link. No alert on PASS or follow-ups. |

## 5. Do the five components still hold

| Component | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 |
|---|---|---|---|---|---|---|---|---|
| Verdict line | ● | ● as the live status line | ● | ● | ● | ● | ● | ● |
| Table | folded | stage list | – | failed calls, folded | done / next | claims × source | change map | – |
| Evidence block | ● | – | – | the exact error | paths, commands | quote + URL | verify command | one anchor |
| Fold | ● | – | – | ● | ● | ● | ● | – |
| Callout | needs-you list | early warning | the question | the needed action | – | not verified | – | – |

| Result | Detail |
|---|---|
| The five hold for S1 and S4–S8. | No situation needs a sixth block type in a report. |
| The callout has one meaning everywhere: **what needs the human now.** | S1: fixes and checks. S3: the question. S4: the action. This replaces last pass's narrower "what a PASS does not cover". |
| Two additions, outside reports. | S2: a **status line** (stage, counter, elapsed, typical range, last-event age) and a **stage list**. S3: **numbered options** inside the callout. |
| One demotion. | The table is no longer in the default view of S1 at narrow widths: the requirement matrix repeats what the needs-you list says. It folds under a one-line count. |

## 6. Not verified

- Myers 1985 primary (RA42): PDF did not convert; the claim rests on Nielsen's citation (RA38).
- Vendor numbers: sandboxing −84% prompts (RA11), Devin 🟢 twice as likely merged (RA22). No independent test.
- Cursor background agents and Perplexity's citation UI: their pages returned no usable text. No claim rests on them; citation accuracy rests on RA29.
- PagerDuty's "CAN report" (conditions, actions, needs) was not found on the page read (RA47); not used.
- RA29, RA31–RA33, RA35, RA37, RA41, RA52: abstracts only. RA1: guideline list and abstract; RA5: §1.2 only.
- Felt et al. (2012) on Android permission prompts and Johnson & Goldstein (2003) on defaults: pages failed; not used.
- "13–47 min" run time comes from the task brief; the cal.com run records 1,666.1 s.
- Budgets in §3 (lines, items, characters, heartbeat interval) are inference. The reader test (UX plan U5) is the check.
