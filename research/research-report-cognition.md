# Cognition & comprehension evidence for arbiter's report (prefix RC)

Scope: what measurably cuts reading time and errors when humans (including people with ADHD) absorb dense technical reports. This feeds the arbiter `report.md` / `report.json` redesign.
Tags: `[unverified]` = source not fetched or the number comes from a secondary summary. `[INFERENCE]` = my extrapolation to arbiter.

Caveat that applies to everything below: most effect sizes come from learning experiments (students, transfer tests, short lessons). None of them measured reading a code-review report. Carrying them over to arbiter is `[INFERENCE]`. The direction is robust. The sizes are not.

---

## 1. Sources

| Key | Source | URL |
|---|---|---|
| RC1 | Sweller, van Merriënboer, Paas (2019). Cognitive Architecture and Instructional Design: 20 Years Later. *Educ Psych Rev* 31 | https://link.springer.com/article/10.1007/s10648-019-09465-5 |
| RC2 | Mayer (2023). Research-Based Principles for Designing Multimedia Instruction (APA Div 2), median d per principle | https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-research-based-principles-for-designing-multimedia-instruction-mayer.pdf |
| RC3 | Mayer & Fiorella. Principles for Reducing Extraneous Processing (Cambridge Handbook ch.), quotes Ginns 2006 meta-analysis | https://edtechuvic.ca/edci337/wp-content/uploads/sites/11/2022/09/principles-for-reducing-extraneous-processing-in-multimedia-learning-coherence-signaling-redundancy-spatial-contiguity-and-temporal-contiguity-principles.pdf |
| RC4 | Schroeder & Cenkci (2018). Spatial Contiguity and Split-Attention meta-analysis. *Educ Psych Rev* 30 | https://link.springer.com/article/10.1007/s10648-018-9435-9 |
| RC5 | Cromley & Chen (2025). Meta-analysis of Mayer's multimedia research (181 studies, 591 effects). *Educ Res Rev* 49 | https://par.nsf.gov/biblio/10637927 |
| RC6 | Schneider, Beege, Nebel, Rey (2018). Meta-analysis of signaling (103 studies, N=12,201). Read via the QIC-WD umbrella summary | https://www.qic-wd.org/umbrella-summary/signaling-in-training |
| RC7 | Kalyuga, Ayres, Chandler, Sweller (2003). The Expertise Reversal Effect. *Educ Psychologist* 38 `[unverified: abstract not fetched]` | https://www.tandfonline.com/doi/abs/10.1207/S15326985EP3801_4 |
| RC8 | Cowan (2001). The magical number 4 in short-term memory. *BBS* 24 | https://pubmed.ncbi.nlm.nih.gov/11515286 |
| RC9 | Heer & Bostock (2010). Crowdsourcing Graphical Perception (replicates Cleveland & McGill 1984). CHI | https://vis.stanford.edu/files/2010-MTurk-CHI.pdf |
| RC10 | Cleveland & McGill (1984). Graphical Perception. *JASA* 79 `[unverified: read only via RC9]` | https://www.jstor.org/stable/2288400 |
| RC11 | Munzner. Visualization Analysis & Design: channel effectiveness rankings (slides) | https://www.cs.ubc.ca/~tmm/talks/minicourse14/vad15seattle.pdf |
| RC12 | Mackinlay (1986). Automating the Design of Graphical Presentations. ACM TOG `[unverified: paywalled; cited via RC9]` | https://dl.acm.org/doi/10.1145/22949.22950 |
| RC13 | Shneiderman (1996). The Eyes Have It: Task by Data Type Taxonomy | https://hci.stanford.edu/courses/cs448b/papers/shneiderman96eyes.pdf |
| RC14 | Healey & Enns (2012). Attention and Visual Memory in Visualization. IEEE TVCG `[unverified: not fetched]` | https://ieeexplore.ieee.org/document/5963660 |
| RC15 | Few (2006). Common Pitfalls in Dashboard Design | https://www.perceptualedge.com/articles/Whitepapers/Common_Pitfalls.pdf |
| RC16 | Few (2008). Practical Rules for Using Color in Charts | https://www.perceptualedge.com/articles/visual_business_intelligence/rules_for_using_color.pdf |
| RC17 | Tufte (2004). Sparkline theory and practice | https://www.edwardtufte.com/notebook/sparkline-theory-and-practice-edward-tufte/ |
| RC18 | Borkin et al. (2016). Beyond Memorability: Visualization Recognition and Recall. IEEE TVCG | https://pubmed.ncbi.nlm.nih.gov/26390488 |
| RC19 | Matthews et al. (2006). Evaluating Glanceable Visuals for Multitasking (UCB tech report) | https://www2.eecs.berkeley.edu/Pubs/TechRpts/2006/Archive/EECS-2006-173.pdf |
| RC20 | Morkes & Nielsen (1997). Concise, SCANNABLE, and Objective: How to Write for the Web (NN/g) | https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/ |
| RC21 | Pernice (2019). The Layer-Cake Pattern of Scanning (NN/g) | https://www.nngroup.com/articles/layer-cake-pattern-scanning/ |
| RC22 | Pernice (2017). F-Shaped Pattern of Reading (NN/g) | https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/ |
| RC23 | Nielsen. Progressive Disclosure (NN/g) | https://www.nngroup.com/articles/progressive-disclosure/ |
| RC24 | NN/g. Inverted Pyramid: Writing for Comprehension | https://www.nngroup.com/articles/inverted-pyramid/ |
| RC25 | Forrin et al. (2021). TL;DR: Longer Sections of Text Increase Unintentional Mind-Wandering. *J Exp Educ* 89 | https://experts.umn.edu/en/publications/tldr-longer-sections-of-text-increase-rates-of-unintentional-mind/ |
| RC26 | Forrin, Risko, Smilek (2019). Reading difficulty and mind-wandering: a section-length account. *Psych Res* 83 | https://pubmed.ncbi.nlm.nih.gov/29094259 |
| RC27 | W3C COGA (2021). Making Content Usable for People with Cognitive and Learning Disabilities + supplemental design patterns | https://www.w3.org/TR/coga-usable/ ; https://www.w3.org/WAI/WCAG2/supplemental/ |
| RC28 | W3C COGA pattern: Avoid Too Much Content | https://www.w3.org/WAI/WCAG2/supplemental/patterns/o5p03-manageable-quantity/ |
| RC29 | W3C COGA pattern: Provide Summary of Long Documents | https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p08-summary-provided/ |
| RC30 | WCAG 2.2 Understanding SC 1.4.1 Use of Color | https://www.w3.org/WAI/WCAG22/Understanding/use-of-color |
| RC31 | W3C: What's New in WCAG 2.2 | https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/ |
| RC32 | British Dyslexia Association. Dyslexia Style Guide 2023 (archived PDF) | https://web.archive.org/web/20230510230226if_/https://cdn.bdadyslexia.org.uk/uploads/documents/Advice/style-guide/BDA-Style-Guide-2023.pdf |
| RC33 | Okabe & Ito. Color Universal Design | https://jfly.uni-koeln.de/color/ |
| RC34 | Alderson et al. (2013). ADHD and working memory in adults: meta-analysis (38 studies). *Neuropsychology* 27 | https://pubmed.ncbi.nlm.nih.gov/23688211 |
| RC35 | Ben-Yehudah & Brann (2019). Pay attention to digital text: ADHD comprehension and self-monitoring. *Res Dev Disabil* 89 | https://pubmed.ncbi.nlm.nih.gov/30981195 |
| RC36 | Llana et al. (2026). Reading with Diversity in Mind: Pupillometry and Typography for ADHD Readers. CHI EA `[numbers read via secondary review]` | https://dl.acm.org/doi/10.1145/3772363.3799383 ; summary: https://a11y-paradise.onrender.com/reviews/69ed2c3f083d4508fd230b16 |
| RC37 | Newman et al. (2025). "Get Me In The Groove": Supporting ADHD Professional Programmers. ICSE | https://andrewbegel.com/papers/newman-icse25.pdf |
| RC38 | Liebel, Langlois, Gama (2024). Challenges, Strengths, and Strategies of Software Engineers with ADHD. ICSE-SEIS | https://arxiv.org/abs/2312.05029 |
| RC39 | Johnson et al. (2013). Why Don't Software Developers Use Static Analysis Tools to Find Bugs? ICSE | http://people.cs.gmu.edu/~johnsonb/docs/icse2013.pdf |
| RC40 | Sadowski et al. (2018). Lessons from Building Static Analysis Tools at Google. CACM 61(4) | https://cacm.acm.org/magazines/2018/4/226371-lessons-from-building-static-analysis-tools-at-google/fulltext |
| RC41 | Sadowski et al. (2015). Tricorder: Building a Program Analysis Ecosystem. ICSE | https://research.google.com/pubs/archive/43322.pdf |
| RC42 | Imtiaz et al. (2019). Challenges with Responding to Static Analysis Tool Alerts. MSR | https://akondrahman.github.io/files/papers/msr19_sat.pdf |
| RC43 | Ancker et al. (2017). Workload, complexity and repeated alerts on alert fatigue in CDSS. *BMC Med Inform* 17 | https://pubmed.ncbi.nlm.nih.gov/28395667 |
| RC44 | Parnin & Orso (2011). Are Automated Debugging Techniques Actually Helping Programmers? ISSTA | https://eecs481.org/readings/debugging-helping.pdf |
| RC45 | Lawrance, Clarke, Burnett, Rothermel (2005). How Well Do Professional Developers Test with Code Coverage Visualizations? VL/HCC | https://web.engr.oregonstate.edu/~burnett/Reprints/vlhcc05-professionalsTesting.pdf |
| RC46 | Cornelissen et al. (2011). A Controlled Experiment for Program Comprehension through Trace Visualization. IEEE TSE | https://azaidman.github.io/publications/cornelissenTSE2010.pdf |
| RC47 | Li & Maalej (2012). Which Traceability Visualization Is Suitable in This Context? REFSQ | https://link.springer.com/chapter/10.1007/978-3-642-28714-5_17 |
| RC48 | (2024). Deep Learning-based Code Reviews: A Paradigm Shift or a Double-Edged Sword? (controlled exp., 29 experts) | https://arxiv.org/abs/2411.11401 |
| RC49 | (2025). Automated Code Review in Practice. ICSE-SEIP (Qodo PR-Agent, 4,335 PRs) | https://arxiv.org/abs/2412.18531 |
| RC50 | (2026). RovoDev Code Reviewer: Large-Scale Online Evaluation at Atlassian | https://arxiv.org/abs/2601.01129 |
| RC51 | (2025). Does AI Code Review Lead to Code Changes? 16 GitHub Actions, 22k comments | https://arxiv.org/abs/2508.18771 |
| RC52 | (2025). What Types of Code Review Comments Do Developers Most Frequently Resolve? | https://arxiv.org/abs/2510.05450 |
| RC53 | (2024). AI-Assisted Assessment of Coding Practices in Modern Code Review (Google AutoCommenter) | https://arxiv.org/abs/2405.13565 |
| RC54 | Arisholm et al. (2006). The Impact of UML Documentation on Software Maintenance. IEEE TSE `[unverified: abstract not fetched]` | https://www.computer.org/csdl/journal/ts/2006/06/e0365/13rRUygT7oV |
| RC55 | Bacchelli & Bird (2013). Expectations, Outcomes, and Challenges of Modern Code Review. ICSE | https://research.tudelft.nl/en/publications/expectations-outcomes-and-challenges-of-modern-code-review/ |
| RC56 | US Army AR 25-50, Preparing and Managing Correspondence (Army writing standard, "bottom line" first) `[unverified: PDF not fetched]` | https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN42124-AR_25-50-007-WEB-13.pdf |

---

## 2. Findings

### 2.1 Cognitive load and multimedia learning

| # | Finding | What was measured / size | Keys |
|---|---|---|---|
| F1 | Cognitive load theory: all new information passes through a working memory with limited capacity and duration. Design must cut extraneous load. | Theory backed by decades of experiments. | RC1 |
| F2 | Working memory holds about 3–5 chunks, not 7. | Review of capacity data across paradigms. | RC8 |
| F3 | **Coherence:** removing extraneous material improves transfer. | 18/19 tests, median **d = 0.86**. Effects are strongest for low working-memory learners. | RC2 |
| F4 | **Signaling:** headings, outlines, highlighting and pointer words help. | 26/28 tests, median **d = 0.70**. Verbal signals d = 0.69, visual d = 0.71. Strongest for novices, complex material, and *sparing* use. | RC2 |
| F5 | Signaling also has a strong effect on retention and a moderate effect on transfer. Learners report lower effort and look longer at the relevant material. | Meta-analysis of 103 studies, N = 12,201. Exact g not read `[unverified]`. | RC6 |
| F6 | **Spatial contiguity / split-attention:** put the words next to the graphic part they explain. | Mayer: 9/9 tests, d = 0.82. Ginns 2006: **d = 0.72** over 37 experiments. Schroeder & Cenkci: **g = 0.63** over 58 comparisons (n = 2,426). | RC2, RC3, RC4 |
| F7 | **Segmenting** (learner-paced chunks) and **pre-training** (define key terms first) help. | d = 0.67 (7/7) and d = 0.78 (10/10). | RC2 |
| F8 | **Redundancy:** the effect is small and conditional. Duplicate text helps or hurts depending on pacing and length. | Median d = 0.10. The effect reverses when the reader controls the pace or the text is short. | RC2 |
| F9 | **Counterweight:** an independent meta-analysis of Mayer's own corpus finds smaller effects that are shrinking over time. Removing seductive detail stays among the largest. Text + diagrams is large and consistent. | 181 studies, 591 effects, overall **g = 0.37**, falling slightly per year. | RC5 |
| F10 | **Expertise reversal:** guidance that helps novices can slow experts. | Boundary condition reported in RC2 (signaling and pre-training weaker for high-knowledge learners). RC7 not fetched. | RC2, RC7 |

### 2.2 Visual encoding and dashboards

| # | Finding | Keys |
|---|---|---|
| F11 | Accuracy ranking for quantitative judgement: position on a common scale > length > angle / area. The crowdsourced replication gave the same ranking as Cleveland & McGill. Position "significantly outperformed" length. | RC9, RC10 |
| F12 | Munzner's channel rankings. Magnitude (ordered data): position common > position unaligned > length > angle > area > depth > luminance > saturation > curvature > volume. Identity (categories): spatial region > hue > motion > shape. Use magnitude channels for ordered data and identity channels for categories. | RC11 |
| F13 | Visual information-seeking mantra: "Overview first, zoom and filter, then details-on-demand". This is a design heuristic, not an experimental result. | RC13 |
| F14 | Dashboard definition: "most important information … consolidated and arranged on a single screen so the information can be monitored at a glance". Pitfall #1 is exceeding a single screen. Expert opinion. | RC15 |
| F15 | Sparkline: "small intense, simple, word-sized graphic". It can be embedded in a sentence or a table. Opinion and practice. | RC17 |
| F16 | Eye tracking (33 participants, 393 visualizations): titles and supporting text should state the message. Redundancy (text + visual) helps the message get through. At-a-glance memorable visualizations also convey their message. | RC18 |
| F17 | Glanceable visuals: renditions should match viewer expectations, abstract to essentials, stay distinct and stay consistent. Recognition was studied with set sizes 3 vs 7. | RC19 |
| F18 | Preattentive features (hue, size, orientation, motion, etc.) pop out before focused attention. Specifics `[unverified]`: RC14 not fetched. | RC14 |

### 2.3 Scanning, BLUF and progressive disclosure

| # | Finding | Measured | Keys |
|---|---|---|---|
| F19 | Rewriting the same content made it far more usable. Concise: +58%. Scannable (bullets, bold keywords, more headings): +47%. Objective: +27%. Combined: **+124%**. | n = 51, between-subjects. Task time 359 s → 149 s (combined). Task errors 0.82 → 0.10. Memory 0.41 → 0.67. 1997 web study. | RC20 |
| F20 | In that study, 15/19 participants scanned before reading. Users liked summaries and the inverted pyramid ("Boom. It gets to the point"). | Qualitative. | RC20 |
| F21 | Layer-cake scanning (eyes jump between descriptive headings) is "by far the most effective" scanning pattern. The F-pattern appears when text has no signals, and readers "miss meaningful information and have no knowledge they did so". | Eyetracking; NN/g. | RC21, RC22 |
| F22 | Progressive disclosure improves learnability, efficiency and error rate. "Designs that go beyond 2 disclosure levels typically have low usability". | NN/g expert guidance. | RC23 |
| F23 | Inverted pyramid: the conclusion comes first, so readers get the point however much they read. | NN/g guidance. | RC24 |
| F24 | Longer sections of text (2–6 sentences per screen vs 1) raised *unintentional* mind-wandering. | n = 80, controlled. | RC25 |
| F25 | Part of the "hard text → more mind-wandering" effect comes from section length. | 3 experiments. | RC26 |
| F26 | BLUF: the Army writing standard puts the bottom line in the opening. `[unverified: AR 25-50 text not fetched]` | Doctrine. | RC56 |

### 2.4 Accessibility and neurodivergence

| # | Finding | Evidence strength | Keys |
|---|---|---|---|
| F27 | COGA objectives: help users find what they need, use clear content, help users focus, and do not rely on memory. Patterns include "Provide Summary of Long Documents", "Avoid Too Much Content", "Use White Spacing", "Use a Consistent Visual Design", "Make it easy to find the most important actions and information", "Support Simplification". | W3C guidance (supplemental, non-normative). | RC27 |
| F28 | "Avoid Too Much Content": give users "five or less main choices on each screen". Important information should be "the first thing I read". Hide extras under a clear "more". | Guidance / opinion. | RC28 |
| F29 | Summaries should be short bullets stating the main points. Headings can act as the summary for content under 300 words. | Guidance. | RC29 |
| F30 | WCAG SC 1.4.1 (Level A): colour must not be the only visual means of conveying information. | Normative standard. | RC30 |
| F31 | WCAG 2.2 added cognitive-adjacent criteria, e.g. 2.4.11 Focus Not Obscured. | Normative. | RC31 |
| F32 | BDA style guide: sans-serif at 16–19 px, 1.5 line spacing, bold for emphasis (no italics or underline), no all-caps, left-aligned, 60–70 characters per line, headings at least 20% larger, bullets over prose, flow charts for procedures, avoid red/green. | Practitioner guidance; partly research-derived. | RC32 |
| F33 | About 8% of Caucasian males, 5% of Asian males and 4% of African males are red-green colour-blind. | Epidemiology summary. | RC33 |
| F34 | Adults with ADHD show **moderate** working-memory deficits, both phonological and visuospatial. | Meta-analysis, 38 studies. | RC34 |
| F35 | On *digital* text, ADHD students had lower comprehension and were **overconfident** about their performance. On print they matched controls but took longer. | n = 45 ADHD + 61 controls. One study. | RC35 |
| F36 | Typography: ADHD readers read faster with fewer saccades (IRR 0.78). They preferred chunked text, consistent formatting, no clutter and no AI summaries injected unasked, and 80% wanted user control of font and size. | **Weak**: 6 ADHD participants. Numbers from a secondary review. | RC36 |
| F37 | ADHD programmers (survey n = 493 + 99 Reddit threads) report more memory and time-management difficulty in code review and documentation reading. Top strategies: task chunking (72%), notes (40%), task visualization (38%). Pull-request notifications were named as distractions. | Moderate (self-report, survey). | RC37 |
| F38 | Software engineers with ADHD struggle with attention and task organisation. Strengths: creativity, puzzles. | Qualitative case study. | RC38 |
| F39 | **Honest gap:** no controlled study found tests report or code-review formats on developers with ADHD. ADHD-specific guidance is extrapolated from working-memory and attention findings (F2, F3, F24, F34) plus COGA. | — | `[INFERENCE]` |

### 2.5 Software engineering: review output, diagrams, coverage, alerts, AI comments

| # | Finding | Measured | Keys |
|---|---|---|---|
| F40 | 14/20 developers cited poorly presented output as a barrier. False positives and warning volume ("sifting through them is so arduous … forget this") drive abandonment. Developers want lists prioritised by what matters to them, and quick fixes. | Interviews, n = 20. | RC39 |
| F41 | Reasons warnings get ignored: not integrated, not actionable, not trustworthy, not manifest in practice, too expensive to fix, not understood. | Industrial experience report. | RC40 |
| F42 | Tricorder code-review criteria: understandable, actionable with fix guidance, **< 10% effective false positives** ("developers should feel the check is pointing out an actual issue at least 90% of the time"). Results show on *changed lines* only by default. A "Not useful" button exists: above 10% puts an analyzer on probation, above 25% may switch it off. Scale: ~5,000 "Please fix" clicks per day. | Industrial, large scale. | RC40, RC41 |
| F43 | The most common Stack Overflow question about SA alerts is how to ignore or filter them. 44.6% of questions show communication problems. | 280 SO questions. | RC42 |
| F44 | Alert fatigue (clinical): acceptance of reminders dropped **30% per additional reminder** per encounter, and 10% per 5-point rise in repeated reminders. | Field data. | RC43 |
| F45 | Automated fault localisation rank lists did not match how developers debug. Developers want "values, overviews, and explanations". Clustering results and explanations with data values and test-case info would help. Percentage-rank metrics "will not cut it". | Preliminary user study. | RC44 |
| F46 | **Coverage visualisation (block coverage) did not increase faults found or tests written. It made developers overestimate their test effectiveness** more than controls did. | Controlled experiment, professionals. | RC45 |
| F47 | Trace visualisation added to the IDE: **−22% time, +43% correctness** on comprehension tasks. | Controlled experiment. | RC46 |
| F48 | Traceability: matrices suit overview and management, graphs suit navigation, hyperlinks suit fine-grained implementation and testing work. Lists were the least liked. Users "are not always able to choose the most suitable visualization". | Experiment + interviews, n = 24. | RC47 |
| F49 | UML documentation helps correctness on complex maintenance changes, with time costs. `[unverified: abstract not fetched]` | Controlled experiment. | RC54 |
| F50 | Code review is less about defects than expected. It also serves knowledge transfer and awareness. The claim that understanding the change is the key challenge is `[unverified]`. | Microsoft field study. | RC55 |
| F51 | **Anchoring:** with an LLM review as the starting point, reviewers focused on the flagged locations. They found more low-severity issues but **no more high-severity ones**. No time was saved and confidence did not rise. | Controlled, 29 experts, 50+ h. | RC48 |
| F52 | 73.8% of automated comments were resolved, yet PR closure time *rose* (5 h 52 → 8 h 20). Drawbacks: faulty reviews and irrelevant comments. | Industry, 4,335 PRs. | RC49 |
| F53 | 38.7% of comments led to code changes. PR cycle time −30.8%. Human comments −35.6%. | Atlassian, 1 year. | RC50 |
| F54 | Comments that are **concise, contain code snippets**, are manually triggered and hunk-level are more likely to cause changes. | 22k comments, 178 repos. | RC51 |
| F55 | Readability, bug and maintainability comments were resolved more often than design comments. | LLM-judged taxonomy. | RC52 |
| F56 | An LLM best-practice commenter ran as an A/B test at Google with a positive workflow impact. | Industrial. | RC53 |

### 2.6 Colour

| # | Finding | Keys |
|---|---|---|
| F57 | Never use colour alone (WCAG 1.4.1, Level A). Pair it with text, shape or position. | RC30 |
| F58 | Red/green is the worst pair, given 8% prevalence in some male populations. The BDA guide also says avoid red/green. The CUD palette (Okabe-Ito) is built for protan/deutan viewers. | RC33, RC32 |
| F59 | Few: use colour sparingly. Most of the display should be neutral so that saturated colour flags the exceptions. `[unverified: rule text skimmed only]` | RC16 |

---

## 3. Implications for arbiter: ranked design rules

Strength scale. **strong**: meta-analyses or replicated controlled experiments. **moderate**: single controlled studies, large field data, or replicated eyetracking. **weak**: small or one-off studies. **opinion**: expert or standards guidance with no direct experiment. A **normative** item is a standards requirement.

| Rank | Rule (concrete, for report.md / HTML view) | Evidence | Strength |
|---|---|---|---|
| 1 | **Verdict + one-line next action first.** Line 1: verdict badge (icon + word, e.g. `✖ BLOCK`), one sentence on why, one imperative next step. Everything else comes after. | F19, F20, F23, F26, F29 | moderate |
| 2 | **Cut, don't fold, the noise.** Remove whatever does not change the reader's decision: restated inputs, method narration, praise, passing checks. Concise alone cut task time 42% and nearly halved errors. Coherence d = 0.86. Removing seductive detail is among the largest effects even in the conservative re-analysis. | F3, F9, F19 | strong |
| 3 | **≤ 5 items above the fold, ≤ 4 per group.** At most 5 top-level blocks: verdict, requirements status, blocking findings, coverage gaps, details link. Blocking findings capped at 3–5 with "+N more". | F2, F28, F44 | moderate (WM limit strong; exact cap is opinion) |
| 4 | **Evidence sits next to its claim.** Each finding card holds the claim, `file:line`, a ≤ 6-line code snippet, the failing/missing test name and the fix, all in one block. No "see Appendix B" and no separate proof sections. | F6 (d ≈ 0.63–0.82), F54 | strong |
| 5 | **Every finding is actionable or it is not shown.** Required fields: severity, one-line problem, concrete fix (patch when possible). Suppress or fold low-confidence findings. Aim for < 10% "not useful". Add a per-finding "not useful" signal to `report.json` for tuning. | F40, F41, F42, F43 | moderate (industrial) |
| 6 | **Severity-gated display; low severity collapsed by default.** Show blocking/high first and collapse the rest under a count. LLM review anchors humans on what it lists and inflates low-severity attention, so ordering decides where humans look. | F51, F52, F55, F44 | moderate |
| 7 | **Requirements × status matrix as the overview.** One row per requirement. Columns: implemented / branches exercised / tests (oracle strength) / open findings. Cells are glyph + short word. Each row links to detail (hyperlinks for fine-grained work). | F48, F13, F14 | moderate |
| 8 | **Never colour-only; colour-blind-safe palette.** Status = shape glyph (✔ ▲ ✖ ○) + word + colour. Use the Okabe-Ito blue/orange/vermillion family, not red/green. Keep most of the page neutral and reserve saturated colour for exceptions. | F30, F57, F58, F59, F33 | strong (normative + prevalence) |
| 9 | **Quantities as position or length, never area, angle or hue intensity.** Coverage and branch counts as aligned horizontal bars (bullet bars) or dot rows. No pies, donuts or heat-intensity alone. | F11, F12 | strong |
| 10 | **Coverage must not read as "tested".** Show *exercised* vs *asserted* separately (branch hit vs oracle checks it). Label 100% green coverage with the oracle grade beside it. Coverage visualisation alone made professionals overconfident. | F46, F45 | moderate (one controlled study) |
| 11 | **Overview → filter → details, max 2 disclosure levels.** Level 0: verdict + matrix. Level 1: expandable cards per requirement or finding. Level 2: raw JSON or log link. No third nested fold in markdown. | F13, F22, F7 (segmenting d = 0.67) | moderate |
| 12 | **Descriptive, message-bearing headings.** Each heading states the conclusion ("3 requirements lack an oracle"), not the topic ("Coverage"). Use the same in chart titles. This enables layer-cake scanning. | F4, F16, F21 | strong (signaling) / moderate (eyetracking) |
| 13 | **Short blocks: one idea, ≤ 3 sentences of prose per block.** Use bullets and tables over paragraphs. Long sections raise unintentional mind-wandering. | F24, F25, F19, F32 | moderate |
| 14 | **Explain with values, not scores.** Findings and judge rubric items show concrete inputs, observed vs expected values and the triggering test, not only R-codes or percentages. Cluster related findings into one card. | F45, F47 | moderate |
| 15 | **Inline word-sized graphics in tables.** Put a tiny bar or branch-dot strip inside the requirement row instead of a separate chart section (same idea as rule 4). | F15, F6 | opinion (Tufte) + strong (contiguity) |
| 16 | **Define terms once, up front, in plain words.** A 3–5 entry legend (verdict values, glyphs, STRONG/GAPS/WEAK, oracle O0–O3) before the matrix. Pre-training is d = 0.78. | F7, F27, F32 | strong (novices) |
| 17 | **Stable layout across runs.** Same section order, glyphs, words and positions every time, so returning readers skip by position. | F17, F27 | opinion |
| 18 | **Explicit "what you still must check" box.** List the items the agent could not verify. ADHD readers are overconfident on digital text, and coverage UIs breed overconfidence. Make the unknowns visible rather than implied. | F35, F46, F51 | weak–moderate |
| 19 | **Density toggle for experts.** The default view is the scaffolded one. A "compact" view hides the legend and explanations for repeat readers (expertise reversal). | F10 | moderate (theory) / weak (direct evidence) |
| 20 | **Typography and calm chrome (HTML view).** Left-aligned, 16–19 px, 1.5 line height, 60–70 ch measure, bold not italics, no all-caps body, no motion or auto-expanding content, no unrequested AI summaries. | F32, F36, F27 | opinion / weak |

### Cross-cutting notes for the design decision

- **Biggest measured wins are subtractive** (F3, F19, F9). A prettier wall of text is still a wall. The report generator needs a hard budget per section, e.g. max cards and max words per card, enforced in code. `[INFERENCE]`
- **Interactive JSON views are for level 2, not level 0.** Evidence supports overview + details on demand (F13, F22, F48). No source supports raw tree explorers as the primary view. `[INFERENCE]`
- **ADHD:** the evidence is thin and indirect (F36 has n = 6; F35 is one study; F37 is self-report). The defensible claim: design for low working memory and short attention bursts (rules 1–4, 11, 13). This is universal design that also helps neurotypical readers (BDA and COGA both say so). Do not claim "ADHD-validated".
- **AI-review trust:** resolution rates vary widely (38.7%–73.8%, F52, F53), and LLM output anchors reviewers (F51). Because arbiter is an agent, showing confidence and source (machine-checked vs model-judged) per finding is a likely trust lever `[INFERENCE]`. I found no direct experiment on it.

What I skipped: I did not fetch the full texts of Arisholm 2006, Healey & Enns 2012, Mackinlay 1986, Kalyuga 2003 or AR 25-50 (paywalled or blocked). Those rows are tagged `[unverified]`. The exact effect sizes for Schneider 2018 signaling come from a secondary summary.
