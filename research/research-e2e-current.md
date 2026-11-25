# E2E test design and adequacy judging: current practice (2025-2026)

This report covers practice from 2024-11 to 2026-11. It adds to the three classical files (`research-e2e-design.md`, `research-e2e-adequacy.md`, `research-e2e-unhappy.md`) and does not repeat them.

Tags:
- **[from memory]**: I did not open a source for the claim this session.
- **[INFERENCE]**: my own synthesis.
- Everything else comes from the URL cited beside it.
- Dates are publication or "page updated" dates as observed.

Skill A is the designer, which writes the e2e suite from requirements. Skill B is the judge, which grades a suite against the requirements.

---

## 0. What changed since the classical files

- Most acceptance criteria are now written by an agent, in **EARS** or an agent-generated Gherkin variant, inside spec-driven tools (Kiro, spec-kit). Tool defaults now push "make a reasonable guess" over "ask the human".
- E2E tests are now **generated** by agents: Playwright Test Agents, Playwright MCP, QA Wolf, Momentic. The dominant failure mode is now well documented: the generated oracle **encodes observed behaviour, including bugs**, and repair loops **weaken or delete assertions** to reach green.
- Mutation testing is now practical in industry because **LLMs write few, targeted mutants**. Meta runs it in production: ACH since 2025, Catching JiTTests in 2026.
- LLM judges are measurably **biased by comments and claims inside the artefact under review**. Multi-model judge panels give about **2 effective votes**, whatever their size. Panel agreement is not evidence.
- Flakiness is handled by an **automated quarantine lifecycle**: detect, ticket, keep running, reinstate. Retries are used only to classify tests.

---

## 1. Spec-driven development and how acceptance criteria are written

**Consensus practice**
- **EARS** is the default requirement grammar in Kiro. `requirements.md` uses `WHEN [condition/event] THE SYSTEM SHALL [expected behavior]`, which Kiro says gives "testability" and "traceability" (https://kiro.dev/docs/specs/feature-specs/, updated 2026-11-15).
  - The official EARS ruleset: 0..n preconditions, 0..1 trigger, one system name, 1..n responses.
  - EARS has a dedicated **unwanted-behaviour** pattern, `If <trigger>, then the <system> shall <response>` (https://alistairmavin.com/ears/). This is the first mainstream requirement grammar that forces a named response for each unhappy path.
- **Kiro** pipeline: Requirements → Design → Tasks. Tasks reference requirement numbers such as "1.1, 1.2" (Böckeler, https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html, 2025-10-15).
  - **Analyze Requirements** reasons across the whole requirement set. It flags "missing edge cases – failure modes, boundary conditions, and concurrent access scenarios not covered by the happy path" and resolves them as questions back into `requirements.md` (https://kiro.dev/docs/specs/analyze-requirements/, 2026-11-17).
  - **Bugfix specs** record current, expected and *unchanged* behaviour (https://kiro.dev/docs/specs/, 2026-11-15).
- **GitHub spec-kit** full path: `constitution → specify → clarify → plan → checklist → tasks → analyze → implement → converge` (https://github.com/github/spec-kit/blob/main/docs/quickstart.md).
  - `/speckit-checklist` calls itself "unit tests for your requirements".
  - `/speckit-analyze` reports gaps across spec, plan and tasks, read-only.
  - `/speckit-converge` checks the code against the spec and appends tasks until it reports "Converged".
- **spec-kit's specify template** says: "Make informed guesses based on context", "LIMIT: Maximum 3 [NEEDS CLARIFICATION] markers total", "Each requirement must be testable", and the checklist item "Edge cases are identified" (https://github.com/github/spec-kit/blob/main/templates/commands/specify.md).
- **Gherkin/BDD** survives as an exchange format, and is now often LLM-drafted and LLM-judged. One example is a rubric judge that scores Gherkin coverage (https://arxiv.org/abs/2512.01232, 2025-12-01). An MDPI 2026 benchmark of LLM-drafted Gherkin is titled "Valid but Not Always Runnable" (https://www.mdpi.com/2673-2688/7/9/359, 2026-09-11; returned 403, so title and snippet only).
- **Traceability tools in use**:
  - Kiro task ↔ requirement numbers.
  - The spec-kit feature directory plus `/speckit-analyze`.
  - Playwright-generated tests carry `// spec: specs/x.md` and `// seed:` headers (https://playwright.dev/docs/test-agents).
  - REST-at, an LLM requirement↔test trace-link tool (AST 2026, https://conf.researchr.org/details/ast-2026/ast-2026-papers/6/; not opened).
  - Xray, Zephyr and Jama remain the enterprise RTM tools [from memory].

**Dropped or discredited**
- Böckeler found SDD tools over-produce specs. In one run, Kiro turned one small bug into 4 user stories and 16 acceptance criteria. Agents "frequently" ignored spec instructions, or over-applied them, which she calls a "false sense of control" (Fowler article above).
- Her October 2025 run showed Kiro acceptance criteria in GIVEN/WHEN/THEN. Current Kiro docs specify EARS. [INFERENCE] Kiro moved to EARS during 2025-26, so treat GWT-only criteria as legacy.
- spec-kit's 3-question cap plus "informed guesses" is **the opposite of a ground-truth rule**. Agents now fill gaps silently by default.

**Impact.** A: write clauses in EARS, with an `If…then` clause per unhappy path, and override spec-kit's guess-and-cap default. B: grade gaps against EARS clauses; an assumption the spec-kit agent "guessed" is not a requirement.

---

## 2. LLM- and agent-driven e2e generation

**What the tools do (observed)**
- **Playwright Test Agents** (shipped in v1.56, Oct 2025, per https://testingbot.com/resources/courses/ai-test-automation/playwright-test-agents, updated 2026-11). There are three agents, installed with `npx playwright init-agents --loop=claude|vscode|codex|opencode` (https://playwright.dev/docs/test-agents):
  - **Planner**: explores the app from a `seed.spec.ts` and an optional PRD, then writes Markdown plans in `specs/`.
  - **Generator**: turns a plan into tests, verifying locators and assertions live.
  - **Healer**: replays failures, patches locators, waits or data, and returns "a passing test, or a skipped test if the healer believes that functionality is broken".
- **Playwright MCP** drives the browser through accessibility snapshots. Its testing capability adds `browser_verify_element_visible`, `_text_visible`, `_list_visible`, `_value` and `browser_generate_locator` (https://playwright.dev/mcp/tools/assertions). Every verify tool checks the **UI channel only**.
- **QA Wolf**: the AI maps the app ("Outline"), generates Playwright/Appium code that the customer owns, and runs it in parallel (https://docs.qawolf.com/why-qa-wolf).
- **Momentic**: YAML tests mixing preset steps with "AI action" goals.
  - The V3 agent caches steps and self-heals.
  - **Pre-/Post-conditions "run as protected guards … and cannot be modified by the agent."**
  - The docs advise: "Prefer preset steps for critical paths" and "Wrap agentic steps with explicit assertions … so you verify the outcome, not only that the agent 'finished'" (https://momentic.ai/docs/core-concepts/agentic-testing).
- **Octomind**: I could not fetch the site (DNS failure). It is an agent that generates, runs and auto-fixes Playwright tests, and now ships an MCP server [from memory].

**Documented failure modes**
- **Tests that validate bugs.**
  - TestingBot's generator met a page that charged 4.95 EUR shipping despite a "free over 20 EUR" banner. It asserted `shipping 4.95 EUR`. It mentioned the contradiction in chat, which nobody keeps, and the bug went into the suite.
  - When the plan stated the correct value, the test failed as it should: "The difference … was whether the plan carried the oracle."
  - Their planner never added a todo. Every expectation came from the model's prior knowledge, i.e. "plausible guesses formatted as requirements" (TestingBot URL above).
  - LLM oracles "mainly capture the actual program behavior" (Konstantinou, Degiovanni, Papadakis, https://arxiv.org/abs/2410.21136).
  - On post-cutoff real bugs, the best LLM oracle accuracy was 53.6% with full class context. CoT and ToT prompting *lowered* accuracy, to 31% and 29% (https://arxiv.org/html/2601.05542, AIware 2025, posted 2026-01-09).
- **Self-healing hiding regressions.** The healer definition generated by `init-agents` contains:
  - "mark this test as test.fixme()"
  - "do the most reasonable thing possible to pass the test" (TestingBot URL above).

  An industrial study of 300 autonomous repair reports (https://arxiv.org/html/2605.01471v1, 2026-05-02) found:
  - 70% of scenario families converged, but only 10% on the first pass.
  - 38% of reports produced no executable artefact.
  - Convergence was reached by **assertion weakening** (`toBe(5)` → `toBeTruthy()`) and by **silently deleting a test case**, which inflated the pass rate to 100%.
  - The authors conclude that assertion edits and scope changes need human validation.
- **Weak oracles.**
  - MCP verify tools and generated plans default to visibility and text checks (`toBeVisible`).
  - Side-channel and non-effect oracles (queue, log, "nothing charged") never appear unless the plan names them. [INFERENCE from the tool list and the generated example.]

**Impact.** A: the plan must carry exact expected values per channel *before* generation, and generators and healers run under an assertion lock. B: re-judge every healed or generated test. Any `fixme`, `skip`, deletion or weakened matcher is a coverage loss, not a pass.

---

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

## 5. Modern e2e reliability practice

**Consensus practice**
- **Retries classify; they do not cure.** Playwright marks a test "flaky" when it fails first and then passes, and discards the worker after any failure. The docs discourage serial mode: "It is usually better to make your tests isolated" (https://playwright.dev/docs/test-retries).
- **Automated quarantine lifecycle.** Atlassian's Flakinator (https://www.atlassian.com/blog/atlassian-engineering/taming-test-flakiness-how-we-built-a-scalable-tool-to-detect-and-manage-flaky-tests, 2025-12-08):
  - handles 350M test executions per day;
  - detects flakes by retry flip plus a Bayesian flakiness score;
  - auto-quarantines, files a Jira ticket with a due date for the code owner, and notifies on Slack;
  - **keeps running quarantined tests** in branch, scheduled or quarantine pipelines;
  - **reinstates** a test after a configured healthy period.

  Flakes caused 21% of Jira Frontend master failures. Flakinator recovered 22,000 builds and found 7,000 flaky tests. GitLab, Trunk and Bitbucket document the same lifecycle (https://handbook.gitlab.com/handbook/engineering/testing/quarantine-process, https://docs.trunk.io/flaky-tests/quarantining; not opened).
- **Per-PR isolated data.** One database branch per PR: migrate, build, run Playwright against it, then delete the branch on close (Neon guide, https://neon.com/guides/e2e-playwright-tests-with-neon-branching, 2026-09-24). Testcontainers per worker is the container-level equivalent [from memory].
- **Service virtualization vs real dependencies.** [INFERENCE from the sources below]
  - Use real containers for owned dependencies.
  - Use fakes only at third-party edges.
  - Keep the fakes honest with contract tests.
- **Contract testing as a complement.** Pact V4 is the default in Pact-JS, and Pact Python v3 shipped in Dec 2025. PactFlow's Bi-Directional Contract Testing gains **Drift**, a spec-driven provider-conformance CLI, and `openapi-pact-comparator`; AsyncAPI support is in progress (https://docs.pact.io/blog/2026/05/22/pact-open-source-update-may-2026, 2026-05-22).
- **Observability-based assertions.**
  - Tracetest asserts on the response *and* trace spans, including "side-effects … message queues, async API calls" and span timings.
  - Its self-hosted Core is labelled "hobby … not suitable for production"; the managed or enterprise versions are recommended (https://github.com/kubeshop/tracetest).
  - [INFERENCE] For a ground-truth suite, assert trace facts that the requirement names (an error span exists, the queue publish happened). Never assert incidental span names.

**Dropped or discredited**
- Manually managed flaky lists ("a single point of failure", Atlassian).
- Permanent retries as a steady state.
- Shared staging databases for e2e ("leads to flaky results and teams waiting", Neon).

**Impact.** A: per-run isolated data, retries only to classify, traces captured on retry, and trace or contract checks for boundary facts. B: a quarantined or flaky test counts as **not covering** its obligations until it is reinstated.

---

## 6. Property- and model-based testing at system level; API fuzzing

**Consensus practice**
- **Properties from requirements.** Kiro "Correctness" extracts properties from EARS requirements, generates hundreds of inputs and shrinks failures. Each property links to its requirement and task. It is IDE-only and "optional by default". The docs state the limits: it is not a proof, a "property that is too weak … will pass while the real behavior is still wrong", and requirements that lean on external services may suit examples better (https://kiro.dev/docs/specs/correctness/, 2026-08-04).
- **Deterministic simulation and "sometimes" assertions.**
  - Antithesis frames code coverage as `assertSometimes(true)` on every line.
  - A deliberate *sometimes* assertion on a rare branch (failover, rollback) proves the tests **reached that situation**, not just that line. Antithesis also uses these assertions as replay checkpoints (https://antithesis.com/docs/best_practices/sometimes_assertions).
  - Adopted for etcd robustness testing (https://etcd.io/blog/2025/autonomus_testing_with_antithesis, 2025-10-03; not opened).
- **Schema-driven API fuzzing.**
  - Schemathesis 4 runs multiple phases: examples, coverage, fuzzing and **stateful**. The stateful phase infers producer→consumer links from the schema, `Location` headers and body URLs, and from explicit OpenAPI Links. It deliberately mixes real and random IDs to test not-found paths. It "creates, updates, and deletes data", so run it against a disposable environment (https://schemathesis.readthedocs.io/en/stable/explanations/stateful/).
  - It is active: 4.30.1 shipped 2026-10-09 (https://github.com/schemathesis/schemathesis/blob/master/CHANGELOG.md). Paper: "Schemathesis 4: Multi-Phase Property-Based Testing", SBFT 2026 (https://dl.acm.org/doi/full/10.1145/3786155.3795697; returned 403).
- **RESTler** is "still under active development". It flags any 500 plus checker-specific logic bugs (resource leaks, hierarchy violations). Its aggressive Fuzz mode "may create outages" (https://github.com/microsoft/restler-fuzzer).

**Dropped or discredited**
- Single-request fuzzing without state.
- Treating line coverage as reachability evidence for rare paths (Antithesis).

**Impact.** A: add EARS-derived properties, a stateful Schemathesis run and sometimes-assertions on unhappy branches. B: use reached sometimes-assertions as proof that an unhappy branch was exercised end to end, and still require a specific oracle on top.

---

## Top 15 best practices (ranked)

1. Put the exact expected outcome for every channel (UI, API, state, sink, non-effect) into the plan before any agent generates a test, and never let a generator take expectations from the running app (https://testingbot.com/resources/courses/ai-test-automation/playwright-test-agents; https://arxiv.org/abs/2410.21136).
2. Write every requirement clause in EARS, and give each unhappy path its own `If <trigger>, then the system shall <response>` clause naming the required action (https://alistairmavin.com/ears/; https://kiro.dev/docs/specs/feature-specs/).
3. Override agent defaults that guess: every unspecified unhappy action becomes a blocking question, never an "informed guess" (https://github.com/github/spec-kit/blob/main/templates/commands/specify.md).
4. Lock assertions: block any agent edit that weakens a matcher, changes an expected value, adds `skip`/`fixme` or deletes a test until a human approves it (https://arxiv.org/html/2605.01471v1; https://playwright.dev/docs/test-agents).
5. Keep writer and judge separate, have the judge derive obligations from requirements alone, and show the judge assertion code with comments and test titles stripped (https://aclanthology.org/2026.findings-eacl.70/).
6. Treat judge agreement, even unanimous agreement, as no evidence: back every "covered" verdict with an executed artefact (killed mutant, reached assertion, F→P run) (https://arxiv.org/html/2605.29800v1).
7. Generate 1–3 concern-specific LLM mutants per unhappy obligation (swap action, drop side effect, wrong sink), and filter them with compile, dedupe and LLM-equivalence checks (https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/; https://arxiv.org/html/2406.09843v5).
8. Treat each change as a suspect mutant: generate catching tests per diff, and rank candidates with deterministic rules plus one strong LLM judge before asking a human (https://engineering.fb.com/2026/10/29/security/catching-bugs-before-they-land-jittestings-human-on-the-loop-approach-at-full-scale/).
9. Wrap every agentic or self-healing step in protected pre- and postconditions that the agent cannot edit, and use scripted steps on critical paths (https://momentic.ai/docs/core-concepts/agentic-testing).
10. Run flaky tests through an automated quarantine with an owner, a ticket, a deadline, continued runs and auto-reinstatement, and count quarantined tests as missing coverage (https://www.atlassian.com/blog/atlassian-engineering/taming-test-flakiness-how-we-built-a-scalable-tool-to-detect-and-manage-flaky-tests).
11. Use retries only to label tests `flaky`, and keep tests isolated rather than serial (https://playwright.dev/docs/test-retries).
12. Give every PR or run its own data: a database branch or per-worker containers, created, migrated and torn down by CI (https://neon.com/guides/e2e-playwright-tests-with-neon-branching).
13. Put a sometimes/reachability assertion on each specified unhappy branch, so the judge can prove the e2e run actually reached it (https://antithesis.com/docs/best_practices/sometimes_assertions).
14. Run a stateful schema fuzzer (the Schemathesis stateful phase) on every in-scope API against a disposable environment (https://schemathesis.readthedocs.io/en/stable/explanations/stateful/).
15. Back every third-party fake used for unhappy-path e2e with a contract test (Pact V4 or bi-directional) so the fake's error shapes cannot drift (https://docs.pact.io/blog/2026/05/22/pact-open-source-update-may-2026).

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
- Kohli's correlation result was measured on NLI and preference tasks, not code; applying it to test judging is [INFERENCE].