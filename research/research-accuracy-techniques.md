# Accuracy techniques beyond decomposition for cheap-model code review

Access date for every source: 2026-11-23. This report extends `research/research-ai-review-systems.md` §4 (cited as `[AI-§4 #n]`), `research/research-decompose-verify.md` §3 (cited as `[DV-Sx]`, `[DV-§3x]`) and `docs/methodology.md` §2–3 (cited as `[M-§x]`). Diff decomposition is out of scope; it is covered in `research/research-decompose-hierarchical.md`.

Tags: **V** = opened this session and the quoted number was read in the source (abstract, HTML full text or blog body). `[unverified]` = could not open. `[from memory]` = not checked this session. `[INFERENCE]` = my synthesis; no source states it.

"Cheap models" means Haiku, DeepSeek, GPT-mini and Gemini-Flash class, with Sonnet as the ceiling.

---

## 1. Short answer

- **Sampling plus aggregation is the best-measured lever for cheap models.** In SWR-Bench, 5 aggregated Gemini-2.5-Flash reviews beat one Gemini-2.5-Pro review on F1 at lower API cost (20.48% vs 19.38%; $3.68E-03 vs $5.86E-03), and recall rose 118.83% at n=10 (S4). Llama2-13B with 15 samples matches Llama2-70B on GSM8K (S3). Gains are not monotone in k: hard items get *worse* with more votes (S2).
- **Debate, intrinsic self-critique and confidence self-ratings do not pay at equal cost.** Majority voting "accounts for most of the performance gains typically attributed to" debate (S25). "No prior work demonstrates successful self-correction with feedback from prompted LLMs" except on special tasks (S22). Verbalized confidence is overconfident (S27). arbiter already avoids all three.
- **External oracles are what make cheap models good.** Self-correction works "in tasks that can use reliable external feedback" (S22). Generated tests lift pass@1 by 18.8 points (S17). Small models self-correct only with a strong verifier (S23). Repeated sampling scales "in domains where answers can be automatically verified", and voting plateaus where they can't (S41). arbiter's execution proofs and SAST-as-oracle are the right base.
- **LLM triage of SAST warnings is the most cost-effective oracle use arbiter does not yet make.** A hybrid of LLM and static analysis eliminated "94–98% of false positives with high recall" at "$0.0011–$0.12" per alarm in Tencent's industrial study (S31). CWE-specialized prompts beat generic ones (S32).
- **Cascades buy the same accuracy for less.** Examples: up to 98% cost reduction at GPT-4 accuracy (S37); 26% average cost reduction for code with self-tests (S39). Cheap-first verification with escalation on disagreement funds more sampling at fixed cost `[INFERENCE]`.
- **Cross-model ensembles are mixed.** Same-model aggregation beats mixed models in many settings (S5). A lightweight cross-model reviewer "scores no higher than same-model review" (S6). One pairing direction *lowers* pass rate from 91.4% to 82.8% (S7).

The top 8 gaps, ranked by expected accuracy gain per unit cost on cheap models, are in §6.

---

## 2. What arbiter already does (read from the methodology and code)

| Mechanism | Where | Evidence it rests on |
|---|---|---|
| 3-lens verifier panel, 2-of-3 TRUE_POSITIVE to verify, defaulting to FALSE_POSITIVE | `findings.tally`, `V.md` `[M-§3.3]` | `[AI-§4 #2]` |
| Execution proofs E1–E9 with fail-before/pass-after, exit codes re-read from `RUN/exec` records | proof agent P `[M-§3.4]` | `[DV-§3a]`, `[DV-S16]` |
| SAST as oracle: analyzer output is never shown to finders; it is attached afterwards as E2 support | `gates.py` `[M-§2]` | Hybrid-Review precision 2.8% `[DV-S5]` |
| Deep mode: K3 agents (A1a, A1b, A2, A3, A4) run 3 passes; a K3-only finding needs ≥2 passes | `plan.K3`, `findings.merge` | `[AI-§4 #2]`, SWR-Bench |
| Shuffled file order per deep pass | `plan._order` (`random.Random(k).shuffle`) | Bugbot randomized diff order (S35) |
| Task stated first and last in every prompt | `agents.build_prompt` `[M-§3.2]` | `[DV-S2]` |
| A0 intent extraction (claims, risk notes) and threat model | `pipeline.intent` | `[SEC-S36]` |
| Specialist agents by concern (A1a–A9), not one generalist | `[M-§3.2]` | `[AX-§3]` |
| No confidence scores; votes and proofs decide | `[M-§2]` | Greptile "nearly random" `[AI-§4 #10]` |
| Structured JSON output, with free reasoning allowed before the last fenced block | `agents.extract_json` | — |
| Cheap finders, stronger verifier and prover (`--model` vs `--verify-model`) | `[M-§3.7]` | `[AI-§4 #9]` |
| "If unsure, report nothing" in the preamble | `[M-§3.2]` | `[SEC-S35]` |

Today's measured baseline on the seeded corpus: Haiku finders with Sonnet-class verification reach precision 0.69 and recall 0.62. They miss the SQL injection in python-03 and every idiom/design finding in python-05 (`docs/benchmarks.md` §3.1–3.2). **For cheap models, recall is the binding constraint.**

---

## 3. Sources

| ID | Source | URL | Tag | Result direction |
|---|---|---|---|---|
| S1 | Wang et al., *Self-Consistency* (ICLR 2023) | https://arxiv.org/abs/2203.11171 | V | + |
| S2 | Chen et al., *Are More LLM Calls All You Need?* (2024) | https://arxiv.org/abs/2403.02419 | V | **null/negative** past an optimum |
| S3 | Li et al., *More Agents Is All You Need* (TMLR 2024) | https://arxiv.org/abs/2402.05120 · html | V | + |
| S4 | Zeng et al., SWR-Bench (re-opened, v2 HTML) | https://arxiv.org/html/2509.01494v2 | V | + |
| S5 | Li et al., *Rethinking Mixture-of-Agents* / Self-MoA (2025) | https://arxiv.org/abs/2502.00674 | V | **negative** for mixing models |
| S6 | Song, *When Does a Second Model Help?* (2026) | https://arxiv.org/abs/2610.01471 | V | mixed; **null** for a lightweight cross model |
| S7 | Xiang et al., *Cross-Model LLM Code Review* (2026) | https://arxiv.org/abs/2607.21656 | V | mixed; **negative** in one direction |
| S8 | Kumar et al., *Bigger Isn't Always Better* (re-opened, §4.7) | https://arxiv.org/html/2606.15689 | V | **negative** for union ensembles (F1) |
| S9 | Xia et al., *Agentless* (2024) | https://arxiv.org/abs/2407.01489 | V | + for fixed pipelines |
| S10 | Charoenwet et al., *Agentic Code Review in the Terminal* (2026) | https://arxiv.org/abs/2607.16740 · html | V | + precision, high cost |
| S11 | Meng et al., RARe, *When More Retrieval Hurts* (2025) | https://arxiv.org/abs/2511.05302 | V | + top-1; **negative** beyond top-1 |
| S12 | Zhang et al., LAURA (ASE 2025) | https://arxiv.org/abs/2512.01356 | V | + |
| S13 | Sun et al., Go issue-list review and context augmentation (2026) | https://arxiv.org/abs/2606.01859 | V | + |
| S14 | Haider et al., call graph and summary in review prompts (2024) | https://arxiv.org/abs/2411.10129 | V | + (BLEU only) |
| S15 | Maddila et al., ARCTIC: intent, drift, spotlight (Meta, 2026) | https://arxiv.org/abs/2607.29516 | V | + |
| S16 | Li et al., RevAgent: category-specific commentators (2025) | https://arxiv.org/abs/2511.00517 | V | + (BLEU only) |
| S17 | Chen et al., CodeT (2022) | https://arxiv.org/abs/2207.10397 | V | + |
| S18 | Maaz et al., *Agentic Property-Based Testing* (2025) | https://arxiv.org/abs/2510.09907 | V | + |
| S19 | Chen et al., *Self-Debugging* (ICLR 2024) | https://arxiv.org/abs/2304.05128 | V | + with execution |
| S20 | Dhuliawala et al., Chain-of-Verification (2023) | https://arxiv.org/abs/2309.11495 | V | + (no numbers in abstract) |
| S21 | Shinn et al., Reflexion (NeurIPS 2023) | https://arxiv.org/abs/2303.11366 | V | + with external signal |
| S22 | Kamoi et al., *When Can LLMs Actually Correct Their Own Mistakes?* (TACL 2024) | https://arxiv.org/abs/2406.01297 | V | **negative** for intrinsic |
| S23 | Zhang et al., *Small LMs Need Strong Verifiers to Self-Correct* (ACL Findings 2024) | https://arxiv.org/abs/2404.17140 | V | **negative** with weak self-verifier |
| S24 | Smit et al., *Should we be going MAD?* (2023) | https://arxiv.org/abs/2311.17371 | V | **null** vs self-consistency |
| S25 | Choi et al., *Debate or Vote* (NeurIPS 2025) | https://arxiv.org/abs/2508.17536 | V | **null**: voting explains the gains |
| S26 | Kadavath et al., *LMs (Mostly) Know What They Know* (2022) | https://arxiv.org/abs/2207.05221 | V | + for P(True), big models |
| S27 | Xiong et al., *Can LLMs Express Their Uncertainty?* (ICLR 2024) | https://arxiv.org/abs/2306.13063 | V | **negative**: overconfident |
| S28 | Spiess et al., *Calibration and Correctness of LMs for Code* (ICSE 2025) | https://arxiv.org/abs/2402.02047 | V | **negative** out of the box; + with Platt scaling |
| S29 | Tam et al., *Let Me Speak Freely?* (2024) | https://arxiv.org/abs/2408.02442 · html | V | **negative** for format restriction |
| S30 | dottxt, *Say What You Mean* (rebuttal of S29) | https://blog.dottxt.ai/say-what-you-mean.html | V | + (contradicts S29) |
| S31 | Du et al., LLM false-alarm reduction at Tencent (2026) | https://arxiv.org/abs/2601.18844 | V | + |
| S32 | ZeroFalse (2025) | https://arxiv.org/abs/2510.02534 · html | V | + |
| S33 | Datadog, *Using LLMs to filter out false positives from SAST* (2025) | https://www.datadoghq.com/blog/using-llms-to-filter-out-false-positives | V | + (no numbers published) |
| S34 | Chen et al., *Premise Order Matters* (ICML 2024) | https://arxiv.org/abs/2402.08939 | V | order effect up to 30% |
| S35 | Cursor, *Building Bugbot* | https://cursor.com/blog/building-bugbot | V | + |
| S36 | Anthropic docs, long-context prompting tips | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips | V | + |
| S37 | Chen et al., FrugalGPT (2023) | https://arxiv.org/abs/2305.05176 | V | + |
| S38 | Ong et al., RouteLLM (ICLR 2025) | https://arxiv.org/abs/2406.18665 | V | + |
| S39 | Chen et al., *Model Cascading for Code* (2024) | https://arxiv.org/abs/2405.15842 | V | + |
| S40 | Snell et al., *Scaling Test-Time Compute Optimally* (2024) | https://arxiv.org/abs/2408.03314 | V | + (difficulty-dependent) |
| S41 | Brown et al., *Large Language Monkeys* (2024) | https://arxiv.org/abs/2407.21787 | V | + with verifier; **plateau** without |
| S42 | Liu et al., *Can 1B LLM Surpass 405B?* (2025) | https://arxiv.org/abs/2502.06703 | V | + (math only) |
| S43 | Pornprasit & Tantithamthavorn, fine-tuning vs prompting for review (IST 2024) | https://arxiv.org/abs/2402.00905 | V | + fine-tune; − persona |
| S44 | Greptile, *How to make LLMs shut up* | https://www.greptile.com/blog/make-llms-shut-up | V | **negative** for few-shot and self-rating; + for embedding filter |
| S45 | Jang et al., negated prompts (2022) | https://arxiv.org/abs/2209.12711 | V | **negative**: inverse scaling |

45 sources opened; at least 13 report null or negative results (S2, S5, S6, S7, S8, S11, S22, S23, S24, S25, S27, S29, S44, S45).

---

## 4. Technique families

Each family lists: **Evidence**, **Cheap models**, **Cost**, **arbiter today**, **Gap**.

### 4.1 Self-consistency, multi-sample voting, cross-model ensembles

**Evidence.**
- Self-consistency: GSM8K +17.9%, SVAMP +11.0%, AQuA +12.2%, StrategyQA +6.4%, ARC-challenge +3.9% (S1).
- Sampling-and-voting "scales with the number of agents"; the gain is "correlated to the task difficulty". Llama2-13B on GSM8K goes from 0.35 to 0.59 at ensemble size 40. At size 15 it "achieves comparable accuracy with Llama2-70B" (S3).
- Code review specifically (S4): Multi-Review runs the reviewer n times and has an LLM synthesize one report.
  - Gemini-2.5-Flash Self-Agg n=10: F1 21.91% (+43.67%), recall 30.44% (+118.83%).
  - Flash n=5 (F1 20.48%) beats single-pass Pro (19.38%) at lower cost ($3.68E-03 vs $5.86E-03).
  - Qwen-Chat-7B n=10: F1 +26.13% (to 14.67%); Qwen-Chat-32B: +19.25% (to 16.41%).
- Bugbot v1: "eight parallel passes with randomized diff order", bucket similar bugs, majority vote, then a validator model (S35).
- **Null/negative.**
  - Vote and Filter-Vote "can first increase but then decrease" with more calls. More calls help "easy" queries and hurt "hard" ones (S2).
  - Self-MoA, one model sampled many times, beats mixing different LLMs by 6.6% on AlpacaEval 2.0 and 3.8% on average; "mixing different LLMs often lowers the average quality" (S5).
  - Cross-model at two calls: one same-model fresh session plus one cross-model review matched 56.7% of planted errors vs 42.7% for two same-model reviews (p=.006). But "a lightweight cross-model reviewer scores no higher than same-model review" (S6).
  - Direction matters: Claude reviewing Codex drafts 71.6% → 89.7%. Codex reviewing Claude drafts 91.4% → 82.8% (S7).
  - Union of Haiku with a second model on review lowered F1: Haiku alone 0.365 (P 0.486, R 0.293); Haiku ∪ Sonnet 0.333 (P 0.627, R 0.226) (S8 Table 9). A true union cannot lower recall, so the paper's merge rule must differ from "union" as described; treat this with caution.

**Cheap models.** Yes, specifically. S3 and S4 show the largest relative gains on the smallest models, and S4 shows the cheap-many-samples configuration beating the expensive single sample on cost-adjusted F1.

**Cost.** k× finder calls (k=3–10); one extra aggregation call in S4's form. arbiter aggregates in code, so it pays no aggregation call.

**arbiter today.** k=3 for five K3 agents in deep mode only, with a 2-of-3 rule (a precision filter), plus shuffled file order.

**Gap.**
1. At standard effort a cheap finder gets k=1, the regime where S4 shows recall is worst.
2. The 2-of-3 rule spends samples on precision, which the verifier panel already buys. S4's gain was mostly recall.
3. There is no difficulty-adaptive k (S2, S40).

### 4.2 Agentic exploration vs static context

**Evidence.**
- Agentic terminal reviewers (Claude Code, Gemini CLI, Rovo Dev, CodeRabbit) "achieve higher review precision but incur substantial exploration and validation overhead". Rovo Dev spends $0.75 on validation and $0.44 on exploration per task; Claude Code $0.10; Gemini CLI ≤$0.007 per phase. "Successful reviews are associated with stronger planning", yet planning stays under 10% of effort (S10).
- Vendors: agentic context is the top production precision gain `[AI-§4 #1]`.
- Counterpoint for *repair*: the fixed three-phase Agentless pipeline reached 32.00% on SWE-bench Lite at $0.70, beating every open-source agent then (S9). A fixed pipeline with a little tool use can beat free-form agents at lower cost.

**Cheap models.** Partly. Cheap models pay the exploration cost with weaker navigation [INFERENCE from S10's cost spread]. S9 suggests deterministic context assembly helps weaker models more than open-ended loops do.

**Cost.** S10 shows a 10–100× per-task cost spread between agent harnesses.

**arbiter today.** Finders have read, grep and glob in the HEAD worktree: a bounded agent inside a deterministic pipeline, which is the Agentless shape.

**Gap.** Small. Deterministic context (callers, co-change, see 4.3) handed to the finder is cheaper than letting a Haiku finder discover it.

### 4.3 Retrieval-augmented review (code graph, similar past reviews, docs)

**Evidence.**
- RARe: retrieving historical reviews as in-context examples gives BLEU-4 12.32 / 12.96. **"Using only the top-1 retrieved example works best, while adding more retrieved items can degrade performance"** (S11).
- LAURA: exemplar retrieval, context augmentation and guidance make GPT-4o and DeepSeek-V3 comments "completely correct or at least helpful" in 42.2% and 40.4% of cases, and every component helps in ablation (S12).
- Go review (1,438 instances) (S13):
  - Issue-list review plus neighboring context plus **similar co-change context** plus candidate integration reaches 28.00% refinement exact match.
  - Primary-issue review without context: 17.15% (+10.85 pp). CodeReviewer: 15.02%. Human ceiling: 36.09%.
  - Pruning cut candidates from 7.2 to 3.1 "while retaining nearly the full benefit".
- Function call graph in few-shot prompts: GPT-3.5 beats the pretrained baseline by "around 90% BLEU-4" (S14). BLEU says little about bug detection.
- `[DV-S5]`: 48% of SWR-Bench false positives come from "Lack of Contextual Understanding" (re-confirmed in S4 Table 7).

**Cheap models.** Yes, in the sense that S12 and S13 used mid-tier models (DeepSeek-V3, GPT-4o class). None of these papers isolates a Haiku-class model.

**Cost.** Retrieval is zero model calls. Exemplars add prompt tokens. S11 says one exemplar is optimal.

**arbiter today.** No past-review retrieval. No co-change context. Caller and callee maps are proposed in `research-decompose-hierarchical.md` §4.2 but not built.

**Gap.**
- Git co-change mining (files that historically change together with the diff's files) costs zero model calls and is the component S13 found useful.
- Past-review exemplars need a corpus arbiter does not have.

### 4.4 Plan-then-review and change summarization

**Evidence.**
- ARCTIC (Meta): intent prediction 0.86 F1. Its "spotlight" ranking of risky diff regions "outperforms the baseline AI reviewer by 2.4x on quality estimation at 5x fewer tokens". In rollout, drift scores reduce misalignment "by an additional 5.76 points (p = 0.026)" (S15).
- S10: successful agentic reviews "are associated with stronger planning and less downstream validation" (association, not causation).
- Caution `[AX-S9]`: CRBugBench agents "trust misleading PR descriptions".

**Cheap models.** Plausible but untested. A plan written once by a stronger model and read by many cheap finders is the cascade shape of 4.14 `[INFERENCE]`.

**Cost.** One call per PR (A0 already exists).

**arbiter today.** A0 produces claims and per-unit risk notes. Finders receive only `unit_notes`. The claims go to SPEC, not to the finders (`pipeline.py`, around line 183 vs 206).

**Gap.** Finders lack the PR-level "what this change is supposed to do" frame. Pass the claims to them as hypotheses to falsify, never as facts. Also missing: a spotlight ordering, telling the finder which hunks A0 rates riskiest.

### 4.5 Checklist and specialist-agent decomposition by concern

**Evidence.**
- RevAgent: five category-specific commentators plus a critic beat single-model baselines by 12.90% BLEU and 8.57% SBERT (S16).
- ZeroFalse: "CWE-specialized prompting consistently outperforms generic prompts" (S32).
- Issue-list prompting (enumerate all issues) beats primary-issue prompting (S13).
- Persona prompting hurt: "few-shot learning without a persona should be used" (S43).

**Cheap models.** Yes. Narrow prompts reduce what a weak model must hold at once `[INFERENCE]`. No source isolates it.

**Cost.** Linear in specialists. arbiter runs 8 per unit at standard effort and 18 at deep `[research-decompose-hierarchical §4.0]`.

**arbiter today.** Done: A1a–A9, CWE-oriented A3, lens-specific verifiers.

**Gap.** None structural. Per-agent precision and recall measurement (roadmap P0.2) would show which specialists earn their calls.

### 4.6 Generate-then-verify with tests (repro, property, mutation)

**Evidence.**
- CodeT: dual execution agreement against generated tests gives HumanEval pass@1 65.8%, +18.8 points over code-davinci-002 (S17).
- Agentic PBT across 100 Python packages: 56% of reports were valid bugs. With a ranking rubric, 86% of the top 21 were valid and 81% reportable; 3 patches merged (S18).
- Repro tests doubled SWE-Agent precision `[DV-S16]`, but only 28% of real bugs got plausible repros `[DV-S17]`. Buggy code steers tests `[DV-S20]`.
- Repeated sampling with an automatic verifier scales coverage: DeepSeek-Coder-V2 on SWE-bench Lite goes from 15.9% at 1 sample to 56% at 250 (S41).

**Cheap models.** Yes. The oracle does the judging, so the generator can be cheap (S41). S39 used self-generated tests as the cascade signal.

**Cost.** Sandbox minutes plus 1–3 model calls per finding.

**arbiter today.** Done for E3/E4/E5/E7 with up to 3 attempts. E6 (property or fuzz) is accepted for logic and edge findings but has no cookbook recipe that a cheap prover reliably follows `[INFERENCE from benchmarks: python-04 stays unproven]`.

**Gap.** PBT is used only to *prove* findings, never to *find* them. S18 shows PBT finds bugs on its own on pure functions with documented contracts.

### 4.7 Chain-of-verification, self-critique, Reflexion; failure of intrinsic self-correction

**Evidence.**
- CoVe: plan verification questions, "answer those questions independently so the answers are not biased", then revise. It decreases hallucination on list QA and long-form text (S20; the abstract gives no numbers).
- Reflexion: 91% HumanEval pass@1 vs GPT-4's 80%, using test feedback (S21).
- Self-Debugging: up to +12% where unit tests exist, 2–3% without; it matches baselines that sample 10× more (S19).
- **Negative:**
  - "No prior work demonstrates successful self-correction with feedback from prompted LLMs"; it works with "reliable external feedback" or "large-scale fine-tuning" (S22).
  - Small models gain "when paired with a strong GPT-4-based verifier", with "limitations … when using a weak self-verifier" (S23).
  - LLMs cannot self-correct reasoning without feedback `[DV-S19]`.

**Cheap models.** Intrinsic self-critique is worst for them (S23). Execution-fed self-repair helps them (S19).

**Cost.** 1–3 extra calls.

**arbiter today.** Done right: the writer never grades itself, verifier lenses are independent (CoVe's "answer independently"), and the prover retries on sandbox output.

**Gap.** None. Do not add a "finder reviews its own findings" step.

### 4.8 Multi-agent debate

**Evidence.**
- MAD protocols "do not reliably outperform … self-consistency and ensembling"; they are "more sensitive to different hyperparameter settings" (S24).
- "Majority Voting alone accounts for most of the performance gains typically attributed to MAD". Debate "induces a martingale over agents' belief trajectories", so it "does not improve expected correctness" (S25).
- In S4, the aggregator sees all n reports at once: aggregation, not debate.

**Cheap models.** No evidence that they gain. Debate multiplies calls by rounds × agents.

**Cost.** Rounds × agents (typically 6–9× a single call).

**arbiter today.** Independent votes, no debate. Correct.

**Gap.** None. Rejected.

### 4.9 Confidence calibration and abstention

**Evidence.**
- Verbalized confidence: LLMs "tend to be overconfident". Consistency across samples helps. White-box beats black-box only narrowly (AUROC 0.522 to 0.605) (S27).
- Code models "are not well-calibrated out of the box". Platt scaling helps when correctness data exists (S28).
- P(True) self-evaluation is well calibrated for large models and improves when models "consider many of their own samples" (S26). That needs logprobs, which arbiter's harness does not expose.
- Greptile 1–10 self-rating "nearly random" (S44).

**Cheap models.** Calibration improves with scale (S27), so cheap models' self-reports are worse. Agreement-based confidence (votes, pass counts) is the model-agnostic substitute.

**Cost.** Zero calls when fitted on existing eval runs.

**arbiter today.** No self-reported confidence. Votes, pass counts and proof rung decide, with fixed thresholds.

**Gap.** Small. The thresholds (2-of-3, rung per axis) are hand-set. A Platt or logistic fit of (TRUE votes, finder passes, rung, agent) to correctness on the dev split would tune abstention. It needs roadmap P0.2/P0.3 data first.

### 4.10 Structured output and evidence requirements

**Evidence.**
- "Significant decline in LLMs reasoning abilities under format restrictions"; JSON mode performs worst on GSM8K-type tasks (S29).
- **Contested:** dottxt re-ran the same evals and found structured output ≥ unstructured: GSM8K 0.77→0.78, Last Letter 0.73→0.77, Shuffle Object 0.41→0.44. It attributes S29's result to weaker prompts for the structured arm (S30).
- Evidence fields: file:line per claim `[AI-§4 #5]`, rated medium.

**Cheap models.** S29 and S30 both used small open models (Llama-3-8B in S30). The practical rule both support: let the model reason in free text, then emit structure `[INFERENCE]`.

**Cost.** Zero.

**arbiter today.** Done. Free text is allowed before the last fenced JSON block (`extract_json`), and a schema with evidence lines and `path:line` is required.

**Gap.** None.

### 4.11 Static-analysis fusion (LLM triage of SAST)

**Evidence.**
- Tencent industrial study, 433 alarms (328 FP, 105 TP): hybrid LLM+SA techniques "eliminate 94–98% of false positives with high recall" at "2.1–109.5 seconds and $0.0011–$0.12" per alarm, vs 10–20 minutes of manual inspection (S31).
- ZeroFalse: F1 0.912 on the OWASP Java Benchmark and 0.955 on OpenVuln, "maintaining recall and precision above 90%"; CWE-specialized prompts win; gpt-oss-20b had the highest OWASP recall (0.900) (S32).
- Datadog ships the same pattern (TP/FP classification over CWE-mapped findings) but publishes no numbers (S33).
- **Contrast:** SAST output pasted into the *finder* prompt dropped precision to 2.8% `[DV-S5]`. Triage (LLM judges a SAST hit) works; injection (SAST hits as finder hints) does not.
- IRIS: LLM-inferred taint specs plus CodeQL found 55 vs 27 of 120 CVEs `[SEC-S44]`.

**Cheap models.** Yes. Triage is a narrow binary task with the location given. gpt-oss-20b and the $0.0011 per-alarm configurations are cheap-class.

**Cost.** One call per alarm, or 3 calls with a panel. Zero finder calls.

**arbiter today.** Analyzers run (semgrep, bandit, gosec) and their hits attach as E2 *support* to findings an agent already made. A hit that no agent raised is never adjudicated.

**Gap.** Large for cheap models. Haiku missed the python-03 f-string SQL injection that bandit `B608` / ruff `S608` flag deterministically [INFERENCE: hit not checked in that run's gate output]. The analyzer's own hits on added lines should become *candidates* for the verifier panel.

### 4.12 Diff ordering and shuffling

**Evidence.**
- Permuting premise order drops accuracy "over 30%"; accuracy is best when order matches the reasoning order (S34).
- Bugbot: "Each pass received a different ordering of the diff, which nudged the model toward different lines of reasoning" (S35).

**Cheap models.** The order effect holds across models (S34). No cheap-model split.

**Cost.** Zero (it comes with sampling).

**arbiter today.** Deep passes shuffle *file* order within a unit (`plan._order`). Pass 0 keeps the natural order.

**Gap.** Minor. Hunk order within a file is never permuted, and standard effort has one pass, so there is nothing to shuffle. It closes for free if 4.1's gap is closed.

### 4.13 Prompt position effects

**Evidence.**
- Lost in the middle `[DV-S2]`.
- Anthropic: put long documents at the top; "queries at the end can improve response quality by up to 30 percent in tests, especially with complex, multidocument inputs" (S36).
- Negated instructions show inverse scaling. "All LM types perform worse on negated prompts as they scale" (S45). This bears on 4.17.

**Cheap models.** Yes, as a general effect.

**Cost.** Zero.

**arbiter today.** Done: the task line comes first and last, with inputs in between.

**Gap.** None measured. Optionally move the output schema after the inputs as well (already the order, per `[M-§3.2]`).

### 4.14 Model routing and cascades

**Evidence.**
- FrugalGPT matches GPT-4 "with up to 98% cost reduction or improve[s] the accuracy over GPT-4 by 4% with the same cost" (S37).
- RouteLLM cuts cost "by over 2 times in certain cases-without compromising" quality (S38).
- Code cascades with self-generated tests as the escalation signal: −26% cost on average, −70% at best, "while maintaining or improving accuracy" (S39).
- Compute-optimal allocation per prompt is ">4x" more efficient than best-of-N (S40).
- S2: hard queries get worse with more cheap votes, so escalation is the right response to disagreement `[INFERENCE]`.
- S8: Haiku 4.5 beat Sonnet 4.6 on review F1 (0.365 vs 0.343) at 3.2× lower cost. The strong model is not uniformly better.

**Cheap models.** This is the technique *for* cheap models.

**Cost.** Below baseline: escalation runs only on the uncertain fraction.

**arbiter today.** Static role routing: cheap finders, a Sonnet-class verifier for *every* candidate × 3 lenses, and a Sonnet-class prover.

**Gap.** No uncertainty-driven escalation. Every candidate pays 3 strong-model verifier calls, including the obviously true and the obviously false.

### 4.15 Test-time compute scaling for cheap models

**Evidence.**
- With compute-optimal allocation, "test-time compute can be used to outperform a 14x larger model" on problems where the small model "attains somewhat non-trivial success rates" (S40).
- A 1B model exceeds a 405B model and a 3B model surpasses 405B on MATH-500 (S42); this uses PRMs, math only.
- Coverage scales log-linearly with samples where outputs are verifiable; voting and reward models "plateau beyond several hundred samples" (S41).
- In SWR-Bench, reasoning LLMs top the single-pass table (Gemini-2.5-Pro F1 19.38%, DeepSeek-R1 18.58%) (S4 Table 8).

**Cheap models.** Yes, conditionally. They must have non-trivial base success (S40), and the gain needs a verifier (S41). arbiter has one: the panel plus execution.

**Cost.** Thinking tokens: roughly 2–5× output tokens per call `[INFERENCE]`. Sampling: k×.

**arbiter today.** The `:thinking` suffix is dropped when resolving omp roles `[M-§3.7]`. No thinking budget is set per role.

**Gap.** Unmeasured. A thinking-budget A/B on the Haiku verifier and prover is cheap to run. For finders, sampling (4.1) has better review-specific evidence than thinking.

### 4.16 Fine-tuning and distillation on review data

**Evidence.**
- Fine-tuned GPT-3.5 zero-shot scores 73.17–74.23% higher exact match than Guo et al.'s approach. Without fine-tuning, few-shot beats zero-shot by 46.38–659.09% EM; persona hurts (S43).
- QLoRA-tuned Code Llama and Llama 3.1 are "competitive" (25–83% improvement) (S14).
- RevAgent fine-tunes all agents (S16).
- All these metrics are lexical (EM, BLEU); none measures bug-detection precision.

**Cheap models.** Fine-tuning targets small models, but arbiter is model-agnostic and runs through harness CLIs `[M-§3.7]`, and Greptile rejected fine-tuning for "cost, speed, and lack of portability" (S44).

**Cost.** A training pipeline plus hosted weights; out of scope for a stdlib-only CLI.

**arbiter today.** None.

**Gap.** Out of scope. Not ranked.

### 4.17 Negative-example suppression

**Evidence.**
- Greptile: good/bad examples in the prompt "made the bot even worse … inferred superficial characteristics". A downvote-embedding filter (cosine similarity to ≥3 downvoted comments → block) took address rate from 19% to 55+% "within two weeks"; "far and away the most impactful technique" (S44).
- Bugbot resolution rate rose from 52% to over 70% across 40 experiments (S35); learned rules in `[AI-§4 #3]`.
- Negated instructions scale inversely (S45). A growing list of "do not report X" lines in briefs is the weak form.
- RARe's top-1 result (S11) suggests one close exemplar beats many.

**Cheap models.** The filter runs in code, after the model, so model strength does not matter. Negated prompt lists hurt *more* as instruction-following weakens `[INFERENCE from S45]`.

**Cost.** Zero model calls at review time. It needs labelled history.

**arbiter today.** Not built (roadmap I5). Briefs carry "do not report X" rules added after r0/r1/r2 (`docs/benchmarks.md` §3.1), the prompt-negation form.

**Gap.** A post-hoc filter against dismissed findings, keyed per repo.

---

## 5. Null and negative results to respect

| Claim tested | Result | Source |
|---|---|---|
| More votes always help | Non-monotone: hard items degrade | S2 |
| Mixing different models beats one model sampled many times | Self-MoA wins by 3.8% on average | S5 |
| A cheap cross-model reviewer adds signal | "No higher than same-model review" | S6 |
| Any cross-model pairing helps | One direction drops 91.4% → 82.8% | S7 |
| Union of two models' findings raises review F1 | F1 0.365 → 0.304–0.333 | S8 |
| More retrieved examples help | Top-1 is best; more degrades | S11 |
| Prompted self-correction works | No successful case without external feedback | S22, S23 |
| Debate beats voting | Voting explains most of the gain; debate is a martingale | S24, S25 |
| Verbalized confidence is usable | Overconfident; calibration poor out of the box | S27, S28, S44 |
| Few-shot good/bad examples cut noise | "Made the bot even worse" | S44 |
| Negated instructions scale with model size | Inverse scaling | S45 |
| JSON output hurts reasoning | Contested (S29 vs S30) | S29, S30 |

---

## 6. Ranking: top 8 techniques arbiter does not yet do

Ranking key: expected accuracy gain (mainly recall, since Haiku recall 0.62 is the binding constraint) divided by added cost, on cheap models. Gains are `[INFERENCE]` extrapolations from the cited sources to arbiter, not measurements. Each must pass the roadmap rule: rerun the narrowest benchmark and revert if held-out recall drops by more than 0.05.

| Rank | Technique | Key evidence | Expected effect on cheap-model arbiter `[INFERENCE]` | Added cost per review |
|---|---|---|---|---|
| 1 | **SAST hits as verifier-panel candidates** (CWE lens) | S31 94–98% FP removed, $0.0011–0.12/alarm; S32 F1 0.91–0.96, CWE prompts win; `[DV-S5]` injection fails, triage works | + security/edge recall where a deterministic rule fires (python-03 class); precision held by panel | 3 verifier calls per new hit on added lines; capped; 0 finder calls |
| 2 | **Cascade verification: cheap panel, escalate split votes** | S37 −98% cost at parity; S39 −26% avg; S40 >4× efficiency; S2 hard items need more than votes; S23 small models need strong verifiers | Same precision at ~40–60% of verifier cost; the saving funds rank 3 | Negative (saves calls) |
| 3 | **Adaptive k=3 cheap finders at standard effort, union into the panel** | S4 Flash ×5 > Pro at lower cost, recall +118.83% at n=10; S3 13B×15 ≈ 70B; S35 Bugbot 8 passes; S2 cap k | Largest recall lever for Haiku (0.62 → target ≥ 0.70, roadmap P2.4) | ~3× calls for K3 agents on flagged units only |
| 4 | **Co-change and neighbor context map** | S13 +10.85 pp from issue-list + neighbor + co-change + integration; `[DV-S5]` 48% of FPs from missing context | + precision and recall on real PRs (Martian/SWR), little on seeded | 0 model calls; one `git log` |
| 5 | **A0 claims and spotlight passed to finders as hypotheses** | S15 intent F1 0.86, spotlight 2.4× at 5× fewer tokens; S10 planning ↔ success; `[AX-S9]` caveat | + recall on intent-violating bugs (logic, spec drift) | 0 new calls; ~200 prompt tokens per finder |
| 6 | **Feedback-learned suppression filter** | S44 address rate 19% → 55+%; S35 52% → 70%+; S45 against prompt negation | + precision on real repos once labels exist; nothing at cold start | 0 model calls |
| 7 | **One cross-family lens in the verifier panel** | S6 56.7% vs 42.7% at 2 calls (strong cross model only); S7 asymmetric; S5 mixing can hurt | Small, uncertain; decorrelates lens errors | ~0 (replaces a lens) |
| 8 | **Property-based-test finder and prover recipe** | S18 56% valid → 86% after ranking; S17 +18.8 pp with generated tests; S41 verifier-backed scaling | + edge/logic recall on pure functions with contracts; E6 proofs for findings now stuck in "Suspected" | 1–2 calls plus ≤2 min sandbox per eligible function |

### 6.1 Sketches

**1. SAST hits as verifier-panel candidates.** In `gates.py`, keep each analyzer hit that falls on an added line and is new against the base worktree. Most analyzers support a baseline mode; otherwise diff the two worktrees' hit sets. Map the rule id to an axis and CWE with the lint-code map that roadmap P1.4 already plans (for example `S608`/`B608` → security, CWE-89). Emit each unmatched hit as a candidate `Finding` with `agent="SAST:<tool>"`, the rule message as the claim and the hit line as evidence. `findings.merge` then dedups it against agent findings by location. Hits that duplicate an agent finding only add support, as today. Survivors go to the existing panel with the security lenses (REACHABILITY, IMPACT, DEFENSES). Add one line of CWE-specific guidance per lens from a small `{cwe: question}` table, following S32. Never show hits to finders (`[DV-S5]` stays honored). Cap candidates per run (say 10, sorted by analyzer severity) so a noisy legacy file cannot flood the panel. Acceptance: python-03 found with Haiku finders, and zero new clean-case findings.

**2. Cascade verification.** Add a `cascade` setting to `Settings`: run the three lenses on the finder-tier model first. In `findings.tally`, a 3/3 TRUE_POSITIVE or 0/3 TRUE_POSITIVE result from the cheap panel is final, except on the never-auto-dismiss list, which always escalates. A split (1 or 2 TRUE) re-runs the three lenses on `--verify-model`, and only that second panel's votes count. Record which tier decided in `coverage.json` so the eval can report agreement between tiers. Before enabling it, replay existing runs: re-run the cheap panel on the stored candidates and compare with the stored Sonnet votes. The disagreement rate on unanimous cheap votes is the risk number, and it must be under 5% on the dev split. Escalation preserves S23's "strong verifier" condition where it matters, and the saving pays for rank 3.

**3. Adaptive cheap-finder sampling.** In `plan.schedule`, set k=3 at standard effort for K3 agents on a unit when (a) the finder model is not the verify model and (b) the unit is risky: `plan_required`, a trigger fired, or an A0 risk note exists. That gives difficulty-adaptive allocation (S40) and avoids S2's degradation on easy units. Use `_order(u, k)` for distinct file orders. Unlike deep mode, do not require ≥2 passes. Union the passes in `merge`, because the panel already filters for precision and S4's gain was recall. Record the pass count on each finding, since agreement is a free confidence signal for rank 2's escalation. Keep the `max_agents` budget: when over budget, k drops to 1 first. Acceptance: Haiku-finder held-out recall ≥ 0.70 with precision drop ≤ 0.03.

**4. Co-change and neighbor context map.** In `plan`, for each changed file run `git log --name-only --format=%H -n 500 -- <file>` on the base. Count the files that co-occur in those commits and keep the top 5 by count with a support of at least 3 commits, excluding files already in the unit. Add a "Files that usually change with these" block to the finder input, listing path, co-change count, and whether the file is in this PR. Put it after the diff, before the closing task line. A co-changed file *absent* from the PR is the cue S13's co-change context provides (a missed companion edit). Neighbor context is the ±20 lines arbiter already sends. List paths only, never bodies: finders can read them, and pasting bodies is the noise failure in `[research-decompose-hierarchical §4.2]`. Stdlib only (`subprocess` git).

**5. A0 claims and spotlight to finders.** In `pipeline._finder_jobs`, add the A0 `claims` relevant to the unit (claims whose cited paths intersect the unit's files, else all, capped at 5) under the heading "Author's stated intent: hypotheses to check, never facts". The preamble already says repo text is untrusted. Extend A0's schema with a per-unit `spotlight` list of up to 3 line ranges it judges riskiest, and send it as "look here first". This costs no new call. It turns A0 into ARCTIC's intent-plus-spotlight (S15) and gives finders S10's planning step for free. Guard: a finding whose only support is "contradicts the claim" still needs code evidence, and the verifier's CLAIM lens already checks that.

**6. Feedback-learned suppression.** Store dismissals in `~/.cache/arbiter/feedback/<repo-hash>.jsonl`: one record per finding a user marks wrong via `arbiter feedback <run> <finding-id> --dismiss`, holding axis, rule, normalized title, file path and the 3 surrounding added lines. At merge time compute a stdlib similarity: token-set Jaccard on title plus rule, with a same-axis requirement. Suppress a candidate with ≥0.6 similarity to at least 3 distinct dismissals, and pass one with similar matches to 3 accepted ones (Greptile's rule, S44, without embeddings). Suppressed findings appear in a report section "Suppressed by feedback (n)" and never vanish silently. The never-auto-dismiss list overrides. This is roadmap I5 and overlaps any learned-rules work in flight; coordinate before building. Do *not* turn dismissals into "do not report" prompt lines (S44, S45).

**7. Cross-family verifier lens.** Add an optional `--lens-model` naming a model from a different family at the same tier as the verifier (for example a GPT-class model when the verifier is Sonnet). It runs one fixed lens, ATTRIBUTION for functional findings and DEFENSES for security. The vote arithmetic is unchanged. S6 shows the gain only for a top-tier cross model, and S7 shows direction matters, so never use a weaker model here. Make it opt-in, evaluate on the Martian sample, and keep it only if verified precision rises at equal recall.

**8. Property-based-test finder and prover recipe.** In the cookbook (`review-python.md` and the Go, Rust and TS equivalents), add an E6 recipe per language: hypothesis, `testing/quick` or rapid, proptest, fast-check. Each recipe runs time-boxed in the sandbox with the seed and the shrunk input recorded. For proving: the P brief tries E6 before E4 for edge and logic findings on pure functions, with properties derived from the docstring, type or callers (`oracle_source`, `[DV-S20]`). For finding: a new triggered agent fires when a changed top-level function is pure (no I/O imports in its body, by an `ast` check) and has a docstring or type contract. It writes 1–3 properties and runs them. A failing property with a shrunk counterexample enters merge as a candidate with E6 already attached, then goes through the panel. Use S18's ranking rubric (validity, reportability) as the verifier's CLAIM-lens checklist.

### 6.2 Considered and not ranked

| Technique | Why not in the top 8 |
|---|---|
| Top-1 retrieved past-review exemplar (S11, S12) | Needs a labelled review corpus per repo; revisit after rank 6 collects one |
| Platt-calibrated abstention on votes, passes and rung (S28) | Needs P0.2/P0.3 per-agent data first; zero call cost once that exists |
| Thinking budget on cheap verifier and prover (S40, S41) | Plausible; no review-specific evidence; quick A/B after P0.1 token accounting |
| Hunk-order shuffling (S34) | Comes free with rank 3 |
| Fine-tuning or distillation (S43, S14) | Breaks model-agnostic, stdlib-only design; lexical metrics only |
| Debate, intrinsic self-critique, confidence self-ratings | Null or negative at equal cost (§5) |

---

## Gaps

- Most sources measure math, QA or code *generation*; review-specific evidence for 4.1, 4.3, 4.4 and 4.11 is limited to S4, S8, S10–S16 and S31–S33.
- No source isolates Haiku-class models for sampling or cascades in code review. S4's cheapest commercial model is Gemini-2.5-Flash.
- S3, S20, S24 and S38 give no per-task numbers in the parts read (abstract plus partial HTML for S3).
- S8's ensemble table reports lower recall for a union than for its parts; the merge rule behind "union" was not found in the parts read.
- S10's precision deltas between agentic and static reviewers were not found in the HTML sections read; only costs and phase shares were extracted.
- S33 (Datadog) publishes no accuracy numbers.
- The expected effects in §6 are extrapolations. None was measured on arbiter.
