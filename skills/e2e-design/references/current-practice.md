# Current practice (2025-2026): specs, agent-generated suites, reliability, properties

Verbatim from `research/research-e2e-current.md` §0–§2, §5, §6. These override the classical files where they conflict.

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

