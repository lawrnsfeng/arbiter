# Current practice (2025-2026): mutation in industry and LLM judges

Verbatim from `research/research-e2e-current.md` §3–§4 and "Where the classical research files are outdated or wrong". These override `adequacy.md` where they conflict.

## 3. Mutation testing in industry

**Consensus practice**
- **Targeted LLM mutants over exhaustive rule-based mutants.**
  - Meta's ACH builds mutants from a plain-text description of a concern, generates tests that kill them, and runs an LLM equivalence detector. The detector scores precision 0.79 and recall 0.47, or 0.95 and 0.96 with simple preprocessing.
  - In an Oct–Dec 2024 privacy trial, engineers accepted 73% of generated tests, and 36% were privacy-relevant (https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/, 2025-09-30; paper https://arxiv.org/abs/2501.12862, FSE 2025).
- **Diff-as-mutant ("Catching JiTTests")**, Meta production, 2026. Two workflows:
  - "Dodgy diff" treats each risky diff *as* a mutant.
  - "Intent-aware" infers the diff's intent, lists risks, builds a mutant per risk, then generates killing tests.

  Weak catches are ranked by an **ensemble LLM-as-judge plus a deterministic rule-based filter (RubFake)** before any human sees them. Results:
  - 589 engineers engaged (64% of outreach).
  - 60% true positives.
  - 74 SEV privacy bugs caught in H1 2026, and privacy SEVs fell 20% (https://engineering.fb.com/2026/10/29/security/catching-bugs-before-they-land-jittestings-human-on-the-loop-approach-at-full-scale/, 2026-10-29; paper https://arxiv.org/pdf/2601.22832).
- **Evidence that LLM mutants are better faults.** A TOSEM study used 851 real Java bugs and more than 701k mutants (https://arxiv.org/html/2406.09843v5, v5 2026-01-22):
  - LLM mutants detect real bugs at 76.47% vs 44.15% for rule-based, a 1.75× gain.
  - They are worse on non-compilability (+32.73 pp), duplication (+9.38 pp) and equivalents (+3.64 pp).
  - Rule-based Major had 2.0% equivalents; GPT-4o had 3.1%.
- **LLM equivalent-mutant detection** beats prior techniques by 35.69% F1 on average. Fine-tuned code embeddings work best (Tian et al., ISSTA 2024, https://arxiv.org/abs/2408.01760).
- **Google diff-based mutation**, which mutates only changed, covered, non-arid lines, remains the reference design (Petrović et al., TSE 2022, https://ieeexplore.ieee.org/document/9524503). No newer Google paper was found this session.

**Tool maturity**
- **cargo-mutants**: v27.1.0, active, new `#[mutants::exclude_re]` (https://crates.io/crates/cargo-mutants, http://mutants.rs/changelog.html).
- **mutmut**: 3.8.1, active in Oct 2026 (https://pypi.org/project/mutmut).
- **gremlins**: still 0.x with no backward-compatibility guarantee. It targets "smallish" modules and can take hours on big ones (https://github.com/go-gremlins/gremlins).
- **StrykerJS**: active, with mutation switching [from memory for its current major version].

**Dropped or discredited**
- "Mutation score as a single gate over all code" is out. Both Meta and Google scope mutants to a diff or a concern.
- "Equivalent mutants make LLM mutation impractical" is out: LLM equivalence filters plus compile and dedupe filters are now standard.

**Impact.** A: for each unhappy obligation, generate 1–3 concern-specific mutants (swap action, drop side effect, wrong sink) and require a killing e2e test. B: use diff-as-mutant runs and LLM mutants as executed evidence, filtered by compile, dedupe and equivalence checks.

---

## 4. LLM-as-judge for test suites and requirement coverage

**Benchmarks and measured accuracy**
- **TestGenEval**: 1,210 code↔test file pairs from 11 repos. It is the first benchmark to report a **mutation score** for generated suites (https://arxiv.org/html/2410.00752, ICLR 2025).
- **TestForge**, an agentic loop with coverage feedback, on TestGenEval: pass@1 84.3%, line coverage 44.4%, mutation score 33.8%, at $0.63 per file (https://arxiv.org/abs/2503.14713, 2025-03-18). Even the best agentic suites kill about a third of mutants.
- **SWT-Bench**: issue-reproduction tests scored fail-to-pass (F→P). LogicStar reported 84% on SWT-Bench Verified with multi-agent iteration (https://logicstar.ai/blog/logicstar-on-test-generation-benchmark-swt; blog undated, about 2025). ICSE 2026 adds AssertFlip, which inverts passing tests into bug-reproducing ones (https://dl.acm.org/doi/full/10.1145/3744916.3773127; not opened).
- **Requirement-coverage judge**: Gherkin rubric scoring across 20 model configurations. GPT-4o-mini was best, at 6.07 MAAE, with 96.6% first-attempt completion and a 175× cost spread (https://arxiv.org/abs/2512.01232). [INFERENCE] MAAE appears to be the mean absolute error on a coverage score, so expect about ±6 points of noise per script.

**Independence evidence (new in 2026)**
- **Correlated judges.** A panel of 9 frontier judges from 7 model families gives n_eff ≈ 2.0–2.5 independent votes:
  - The best single judge matched or beat the panel on every dataset.
  - Unanimous verdicts were wrong 9.1% of the time.
  - Chain-of-thought *raised* correlation.
  - Smarter aggregation closed at most 11% of the gap.
  - The authors recommend reporting n_eff and treating n_eff/k < 0.5 with caution (https://arxiv.org/html/2605.29800v1, 2026-05-28; tested on NLI and RewardBench, not on code).
- **Artefact-borne bias.** Code judges flip on comments:
  - "self-declared correctness" pushes verdicts toward correct;
  - "misleading task" comments cut GPT-4o accuracy by up to 26.7 pp;
  - asking the judge to generate test cases first only partly mitigates this (https://aclanthology.org/2026.findings-eacl.70/, EACL 2026 Findings).
- **Meta's 2026 design** pairs a non-deterministic LLM-judge ensemble with deterministic RubFake rules, and reaches humans "on the loop" through aggregate criteria (JiTTest URL above).

**Dropped or discredited**
- "Ensemble of LLM judges ≈ independent review" is out (Kohli).
- "Judge reads the test and its description" is out: descriptions bias the verdict (Moon et al.).
- "Coverage-feedback loops produce adequate suites" is out: about 34% mutation score (TestForge).

**Impact.** A: the writer never self-certifies, and test names and comments are not evidence. B: derive obligations blind from requirements, judge **stripped assertion code**, use one strong judge plus deterministic checks, and accept only executed artefacts as evidence.

---

## Where the classical research files are outdated or wrong

1. **`research-e2e-adequacy.md` §8 (mitigations) and §9 Step 1 ("use 2 independent derivations and union them"); rule 23 ("where two judges disagree, require executed evidence").** The rule implies that *agreement* lets a verdict skip executed evidence. LLM judges are about 2 effective votes, unanimous verdicts are wrong about 9% of the time, and CoT raises correlation (https://arxiv.org/html/2605.29800v1). Fix: executed evidence for every "covered" claim, whether or not judges agree. A union of two derivations is still useful for *recall* of obligations, not for verdicts. [INFERENCE]

2. **`research-e2e-adequacy.md` §9 Step 2 ("Read S now. Map each test …").** It omits artefact bias. Comments, test titles and `// spec:` headers shift judge verdicts by up to 26.7 pp (https://aclanthology.org/2026.findings-eacl.70/). Add: strip comments and titles, and map tests by stimulus and assertion only.

3. **`research-e2e-adequacy.md` §4 (cost control 4) and the §9 Step 8 rationale ("85% leaves headroom for 10–15% equivalents").**
   - A 701k-mutant study measured equivalents at 2.0% (Major) to 3.1% (GPT-4o).
   - The real cost of LLM mutants is **non-compilability** (+32.73 pp) and duplication (https://arxiv.org/html/2406.09843v5).
   - So the headroom argument is weak. Add an explicit compile and dedupe filter step. [INFERENCE]

4. **`research-e2e-adequacy.md` §4 and `research-e2e-unhappy.md` §12 step 4 (mutation thought-experiment).** Both predate production diff-as-mutant practice. Meta now treats *every risky diff* as a mutant and ranks catches with RubFake plus a judge ensemble (JiTTest 2026 URL). This is a stronger, executed form of the "swap the unhappy action" thought-experiment and should replace purely static grading where it can run.

5. **`research-e2e-design.md` §1.3 (Given-When-Then as the clause format) and §8 step 1.**
   - These are outdated as the *default*. Current spec tools use EARS, whose `If…then` pattern names the unhappy response directly (https://alistairmavin.com/ears/; Kiro docs).
   - GWT remains fine for examples. Clause extraction should start from EARS.

6. **`research-e2e-design.md` §1.2 / §8 step 2 ("log every ambiguity as Q<n>; do not invent the answer").** The rule is correct but now **contested by tool defaults**: spec-kit tells agents to guess and caps questions at 3 (specify template). The skills must enforce the rule explicitly against such tool output. The classical file does not mention that agent-produced specs embed guesses.

7. **`research-e2e-design.md` §5.3 ("Retries only *detect* flakiness … never acceptable") and rule 27; `research-e2e-adequacy.md` §9 Step 0.**
   - The ground-truth stance stands.
   - The cited evidence (Google 2016/2017) is dated. Current practice is an automated quarantine lifecycle with reinstatement (Atlassian, 2025-12-08).
   - The judge rule should say: quarantined means uncovered.

8. **`research-e2e-design.md` §5.1 (isolation via "unique tenant/prefix").** This is incomplete. Per-PR database branching and isolated stacks are now documented practice (Neon guide, 2026-09-24). Prefix-only isolation does not survive migration-changing PRs. [INFERENCE]

9. **`research-e2e-unhappy.md` §5 (OTel InMemorySpanExporter, collector file exporter).** This is a valid DIY approach but misses trace-based testing tools. Tracetest asserts on spans and side effects directly, though its Core is "not suitable for production" (https://github.com/kubeshop/tracetest). The classical API names remain [from memory].

10. **`research-e2e-unhappy.md` §9 (Schemathesis `--mode=negative`, from a search snippet).** It ignores Schemathesis 4's multi-phase design and its **stateful** phase, which reaches use-after-delete and not-found paths through inferred links (Schemathesis docs). The `--mode` flag is still unverified for v4.

11. **`research-e2e-design.md` §4 (PBT) and §8 step 9.** It treats properties as hand-written only. Kiro now derives properties from EARS automatically, with explicit warnings about weak properties (https://kiro.dev/docs/specs/correctness/). Sometimes-assertions add reachability proof for rare branches (Antithesis), which none of the three files cover.

12. **All three files: no section on agent-generated suites.** None covers Playwright planner, generator and healer, or MCP verify tools. Gaps:
    - The healer's "do the most reasonable thing possible to pass the test" and `test.fixme()` behaviour.
    - Generator assertions that encode observed bugs (TestingBot).
    - Assertion weakening and test deletion during repair (arXiv 2605.01471).

    The judge procedure needs a step that diffs assertions against the last human-approved version. [INFERENCE]

13. **`research-e2e-adequacy.md` §8 ("Prompt Coverage Adequacy … 30+% more faults").** It is still research-grade. No 2025-26 industrial adoption was found this session. Keep it out of gates.

---

**Gaps and risks.**
- Not opened: Octomind (DNS failure), the MDPI Gherkin benchmark and the Schemathesis 4 paper (both 403), REST-at, the AssertFlip body, and the GitLab and Trunk quarantine pages. The Google 2025-26 mutation updates were not found.
