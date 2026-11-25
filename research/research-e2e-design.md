# Research: deriving a systematic e2e test suite from requirements

Scope: techniques that turn a requirements document into an e2e suite. Every test must trace to a clause, a coverage item and an oracle. This makes the set systematic, not ad hoc. The audience is a future DESIGNER skill and JUDGE skill.

Tags: **[from memory]** means I did not open a source for the claim this session. **[INFERENCE]** means my own synthesis. Everything else comes from the URL cited beside it.

---

## 0. Core vocabulary (ISTQB / 29119)

- **Test basis → test condition → coverage item → test case.** "Test analysis answers the question 'what to test?' in terms of measurable coverage criteria." Test design "includes the identification of coverage items, which serve as a guide to specify test case inputs" (ISTQB CTFL v4.0.1, §1.4) — https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf
- **Traceability** between the test basis and the testware is what lets you evaluate coverage and the impact of a change (same source, §1.4.4).
- ISO/IEC/IEEE 29119-4:2021 lists these specification-based techniques, each with a matching coverage measure in §6.2:
  - 5.2.1 equivalence partitioning
  - 5.2.2 classification tree
  - 5.2.3 boundary value analysis (BVA)
  - 5.2.4 syntax testing
  - 5.2.5 combinatorial
  - 5.2.6 decision table
  - 5.2.7 cause-effect graphing
  - 5.2.8 state transition
  - 5.2.9 scenario testing
  - 5.2.10 random testing
  - 5.2.11 metamorphic testing
  - 5.2.12 requirements-based testing

  It also lists error guessing (5.4.1). Sources: table of contents of the iTeh preview, https://cdn.standards.iteh.ai/samples/iso/iso-iec-ieee-29119-4-2021/959083ba1c9445ff9f8b4e6783c4cc24/iso-iec-ieee-29119-4-2021.pdf ; https://www.iso.org/standard/79430.html
- **Consequence for an agent [INFERENCE]:** each technique has a defined coverage-item type and a % coverage formula. So "is the suite systematic?" becomes a question you can compute: per technique, the number of coverage items covered divided by the number identified.

---

## 1. Requirement decomposition into atomic, testable clauses

### 1.1 Atomic clauses
- **What:** split each requirement sentence into clauses. Each clause has one trigger, one condition set and one observable outcome. "If X and Y then Z, otherwise W" gives at least two clauses: (X∧Y→Z) and ¬(X∧Y)→W. [INFERENCE]
- **E2E application:** every clause becomes a row in the traceability matrix. Unhappy outcomes count as clauses too: early return with a default value, an error, delegation to another helper or service, a failure shown to the user, or a failure sent to a log, queue or alert.
- **Example:** "Users can export ≤ 10 000 rows as CSV; larger exports are queued and emailed; anonymous users get 401."
  - C1: authenticated, rows ≤ 10 000 → file downloads.
  - C2: authenticated, rows > 10 000 → job enqueued, toast shown, email sent.
  - C3: anonymous → 401 and redirect to login.
  - C4 (implicit): queue down → user sees the error and an alert is emitted. Raise this as a question if the spec is silent.
- **Limits:** implicit clauses (C4) are not in the text. Error guessing (§2.9) and red "question" cards (§1.2) must surface them.

### 1.2 Example Mapping
- **What:** story card (yellow) → rules or acceptance criteria (blue) → examples (green) → open questions (red). "We keep going until the group is satisfied that the scope of the story is clear" — https://cucumber.io/docs/bdd/example-mapping/ ; origin: https://cucumber.io/blog/bdd/example-mapping-introduction
- **E2E application:** blue card = clause, green card = test case. A red card is an explicit gap. The JUDGE should report it as "unspecified behaviour", never silently pick an answer. [INFERENCE]
- **Limits:** the method was designed for a human conversation. An agent has to play every role, so the red cards must be escalated to the requirement owner. [INFERENCE]

### 1.3 Given-When-Then (Gherkin)
- **What:** Given puts "the system in a known state", When is an event, Then is an outcome that "should be on an observable output … not a behaviour deeply buried inside the system (like a record in a database)". 3–5 steps per example. The `Rule:` keyword groups the examples for one business rule. Source: https://cucumber.io/docs/gherkin/reference/
- **E2E application:** Given maps to seeding (API or DB fixture, never UI clicks; see §5.1). When is the single user action. Then is the oracle.
- **Mini example:**
  ```gherkin
  Rule: exports over 10 000 rows are queued
    Example: 10 001 rows
      Given org "acme" has 10001 invoices
      When Ann exports invoices
      Then she sees "We'll email your export"
      And an export job for "acme" is queued
  ```
- **Limits / tension:** Cucumber discourages database checks in Then. For ground-truth e2e, some unhappy outcomes are only visible through a side channel: queue, log, metric, email. [INFERENCE] Treat those channels as the "external system" observer that the Gherkin guidance allows. Read them through their public interface (mail sink, queue consumer, log query), not through private tables.

### 1.4 Specification by Example: key examples
- **What:** illustrate each rule with a few key examples and summarise the important boundaries. Splitting validation from processing exposes hidden concepts such as "valid transaction". In Adzic's routing example, 5⁷ ≈ 80 000 combined examples collapse to about 40 grouped ones — https://gojko.net/2014/05/05/focus-on-key-examples/ ; book: https://gojko.net/books/specification-by-example
- **E2E application:** if a clause needs dozens of examples, decompose further. Each sub-rule gets its own partitions. Combine the rules in a separate small group of examples.
- **Example (from the source):** the risk threshold is 25 USD for high-risk countries and 50 USD for low-risk countries. Key examples: 24.99 high, 25 high, 25 low, 49.99 low, 50 low.
- **Limits:** key examples help shared understanding. They are not a coverage criterion; layer BVA and decision tables on top.

---

## 2. Black-box test design techniques (ISTQB CTFL v4.0.1 §4.2, 29119-4 §5.2)

### 2.1 Equivalence partitioning (EP)
- **What:** divide the data so that every element of a partition is "processed in the same way". Partitions apply to inputs, outputs, configuration, internal values, time-related values and interface parameters. Partitions "must not overlap and must be non-empty". To reach 100%, cover every valid and every invalid partition at least once. With several parameters the minimum criterion is **Each Choice**. Source: ISTQB §4.2.1 (URL above).
- **E2E:** partition the user-visible state as well as the field values: role, plan tier, feature flag, locale, empty, one or many records, and online or offline.
- **Example:** export size {0, 1..10 000, >10 000}; role {anon, viewer, admin}. Each Choice coverage needs 3 tests.
- **Limits:** a partition is a hypothesis about the implementation. Wrong partitions mean missed bugs. Each Choice ignores interactions; see §2.7.

### 2.2 Boundary value analysis, 2-value and 3-value
- **What:** only for ordered partitions.
  - **2-value BVA:** the boundary value plus its closest neighbour in the adjacent partition.
  - **3-value BVA:** the boundary value plus both neighbours.

  3-value finds defects that 2-value misses. Example: `x ≤ 10` wrongly coded as `x = 10`. 2-value tests {10, 11} pass, but the 3-value test with 9 fails. Source: ISTQB §4.2.2; white paper https://istqb.org/wp-content/uploads/2025/10/Boundary-Value-Analysis-white-paper.pdf
- **E2E:** row counts, string lengths, amounts, dates (end of month, DST, leap day), pagination edges, rate limits, upload sizes.
- **Example:** limit 10 000 rows. 2-value: {10 000, 10 001}. 3-value: {9 999, 10 000, 10 001}. Also the 0/1 boundary: {0, 1}.
- **Limits:** needs ordered domains, and the spec must state whether the boundary is inclusive. If it does not, raise a red-card question.

### 2.3 Decision table testing
- **What:** conditions and actions are the rows, rules are the columns. "–" marks a condition that does not matter; "N/A" marks an infeasible combination. The coverage items are the **feasible columns**. Writing the table "helps to find any gaps or contradictions in the requirements" (ISTQB §4.2.3).
- **E2E:** this is the main tool for unhappy-path completeness. Every column's action row names the required action: return a default, raise an error, delegate, show to the user, emit to a log or queue.
- **Example:**

  | | R1 | R2 | R3 | R4 |
  |---|---|---|---|---|
  | authenticated | F | T | T | T |
  | rows > 10 000 | – | F | T | T |
  | queue reachable | – | – | T | F |
  | → 401 + redirect | X | | | |
  | → CSV download | | X | | |
  | → enqueue + toast + email | | | X | |
  | → error toast + alert emitted, nothing enqueued | | | | X |
- **Limits:** the number of rules grows as 2ⁿ. Minimise the table, or use risk-based selection or pairwise testing for the irrelevant interactions.

### 2.4 Cause-effect graphing
- **What:** a Boolean graph from causes (input conditions) to effects (outputs). Constraints between causes (exclusive, inclusive, one-only, requires) prune infeasible combinations. The graph is converted into a decision table. Listed in 29119-4 §5.2.7. Origin: Myers, *The Art of Software Testing* [from memory].
- **E2E:** use it when the spec has mutual exclusions, for example "exactly one payment method" or "coupon requires login", before you build the table.
- **Limits:** heavy to build by hand. In practice an agent can encode the constraints directly as PICT constraints (§2.7). [INFERENCE]

### 2.5 State transition testing (0-switch, 1-switch)
- **What:** states, plus transitions labelled `event [guard] / action`. A state table shows the invalid transitions explicitly as empty cells. Coverage levels:
  - **All states** coverage.
  - **Valid transitions** coverage, also called 0-switch. This is the most widely used criterion.
  - **All transitions** coverage: valid transitions plus attempted invalid ones, with one invalid transition per test to avoid defect masking. This "should be a minimum requirement for mission and safety-critical software" (ISTQB §4.2.4).

  **1-switch** (N-switch) coverage covers every valid *pair* of consecutive transitions. Origin: Chow 1978; also in the ISTQB Advanced Test Analyst syllabus [from memory].
- **E2E:** model the entity lifecycle as the user sees it (draft → submitted → approved/rejected → archived), plus session or auth states. An invalid transition is a UI or API attempt such as "approve an archived doc". Its oracle is the required rejection: disabled control, 409 response, or message.
- **Example:** 1-switch pairs catch bugs like "reject then resubmit keeps the stale approver". 0-switch never forces those two transitions in sequence.
- **Limits:** the hidden states (cache, pending async job) must appear in the model, or the coverage is illusory. 1-switch grows quickly; see the generators in §3.

### 2.6 Classification tree method
- **What:** a tree of classifications (aspects) and classes (partitions), with a combination table under it. Each row picks one class per classification. Listed in 29119-4 §5.2.2 with a coverage measure in §6.2.2. Origin: Grochtmann & Grimm 1993; tool: TESTONA/CTE [from memory].
- **E2E:** a visual EP across many aspects: browser × role × data shape × locale. Rows are then generated by a minimal-coverage rule or by pairwise selection.
- **Limits:** this is EP made visible; it adds no new fault model.

### 2.7 Combinatorial / pairwise (t-way) testing with PICT
- **What:** cover every t-tuple of parameter values (default t = 2, `/o:N` sets the order). Constraints (`IF … THEN …`) remove infeasible tuples during generation; deleting rows afterwards would lose valid pairs. Seeding is available (`/e:file`). **Negative values** are prefixed `~`, and PICT puts only one invalid value per test to avoid "input masking". Output is deterministic for the same model and seed. Source: https://github.com/microsoft/pict/blob/main/doc/pict.md
- **E2E:** configuration and environment matrices: browser, viewport, locale, role, flag and data size. Run PICT for the cross-product and use BVA/EP for the values inside each parameter.
- **Mini example:**
  ```
  Role:    anon, viewer, admin
  Rows:    0, 1, 10000, 10001
  Browser: chromium, firefox, webkit
  Locale:  en-US, de-DE
  IF [Role] = "anon" THEN [Rows] = 0;
  ```
- **Limits:** pairwise testing misses 3+-way interactions. NIST data shows most failures are triggered by ≤ 6 interacting parameters (Kuhn et al.) [from memory]. Raise t for high-risk subsets using sub-models (`{A,B,C} @ 3`).

### 2.8 Use-case / scenario testing (main, alternate, exception flows)
- **What:** derive tests from use-case flows: one for the main success scenario, one per alternate flow, one per exception flow. Coverage = flows exercised / flows identified. Listed in 29119-4 §5.2.9 / §6.2.9; dropped from CTFL v4 core [from memory].
- **E2E:** this is the natural e2e unit. Each exception flow must name its handler: user message, retry, compensation, alert.
- **Limits:** coverage depends on the quality of the use case. Pair it with a state model so flows hit every transition.

### 2.9 Error guessing and fault attacks
- **What:** anticipate errors from experience. A **fault attack** builds a list of likely failures and designs tests to trigger each one (ISTQB §4.4.1; Whittaker).
- **E2E fault list [INFERENCE]:**
  - double submit or double click
  - back button after submit
  - refresh mid-flow
  - two tabs or users editing the same entity
  - session expiry mid-form
  - slow, 500 or timeout from a dependency
  - partial network failure
  - Unicode, RTL or emoji input
  - very long strings
  - timezone and DST edges
  - clock skew
  - offline mode
  - quota exceeded
  - stale cache after deploy
- **Limits:** depends on experience, so there is no coverage measure. Keep a reusable checklist so it becomes a repeatable list.

### 2.10 Exploratory charters
- **What:** design, execution and evaluation happen at the same time, time-boxed in sessions and guided by a **test charter** (ISTQB §4.4.2). Hendrickson's template: "Explore ‹target› with ‹resources› to discover ‹information›" [from memory].
- **E2E:** an agent with Playwright can run charters and turn findings into scripted tests. Charters are the residual-risk sweep after the systematic techniques. They do not replace them.
- **Limits:** results are not reproducible unless every finding is converted into a scripted test.

---

## 3. Model-based testing (MBT)

### 3.1 Graph models and GraphWalker
- **What:** vertices are states or assertions, edges are actions. Generators walk the graph until a stop condition is met:
  - `random(edge_coverage(100))`
  - `quick_random` steers toward unvisited elements
  - `a_star(reached_vertex(X))` drives the test to a target state
  - `shortest_all_paths` is an Eulerian path
  - `new_york_street_sweeper()` is the optimal Chinese-postman route that covers every edge; it ignores guards
  - generators can be chained

  Source: https://graphwalker.github.io/graphwalker-rs/generators
- **E2E:** each vertex is implemented as Playwright assertions on the page, each edge as a Playwright action. Edge coverage 100% = 0-switch coverage of §2.5. [INFERENCE] Use `a_star` to reach deep states cheaply.
- **Limits:** the model can be wrong. A model derived from the implementation tests nothing; derive it from the requirements only. [INFERENCE]

### 3.2 XState / @xstate/test
- **What:** a statechart drives the generation of event sequences, which are replayed against the real UI — https://stately.ai/docs/xstate/v6/model-based-testing
- **Limits:** same model-fidelity risk as §3.1.

---

## 4. Property-based and stateful testing at system level

### 4.1 Hypothesis `RuleBasedStateMachine`
- **What:** Hypothesis generates whole programs: sequences of `@rule` steps with `@precondition`, plus `@invariant` checks that run after **every** step. `Bundle`s let generated IDs flow between rules. Failures shrink to a minimal, copy-pasteable sequence. Source: https://hypothesis.readthedocs.io/en/latest/stateful.html
- **E2E:** rules call the app through `playwright.sync_api` or the HTTP API. The model is a dict of the expected entities. Invariants hold the cross-cutting requirements, for example "a list count badge equals the number of rows", or "no error toast without a matching log entry". [INFERENCE]
- **Example:**
  ```python
  class Todos(RuleBasedStateMachine):
      ids = Bundle("ids")
      @initialize()
      def start(self):
          self.page = new_isolated_page()
          self.model = {}
      @rule(target=ids, title=st.text(min_size=1, max_size=200))
      def add(self, title):
          tid = ui_add(self.page, title)
          self.model[tid] = title
          return tid
      @rule(tid=consumes(ids))
      def delete(self, tid):
          ui_delete(self.page, tid)
          del self.model[tid]
      @invariant()
      def list_matches(self):
          assert ui_titles(self.page) == sorted(self.model.values())
  ```
- **Limits:** slow per step in a browser, so cap `stateful_step_count` and `max_examples`. You need a reset per example (fresh context plus tenant). Nondeterminism breaks shrinking; control it (§5.2).

### 4.2 fast-check model-based testing with Playwright
- **What:** commands implement `check(model)` and `run(model, real)`; `fc.commands` generates them and shrinks smartly. Runners: `modelRun`, `asyncModelRun`, and `scheduledModelRun` "for a better detection of race conditions". Replay uses `seed`, `path` and `replayPath`. The docs warn that the model must be *simpler* than the system: "avoid testing the code by comparing it to itself." Source: https://fast-check.dev/docs/advanced/model-based-testing/
- **E2E:** `real` = `{ page }`. `run` performs a Playwright action, then a web-first `expect` against the model.
  ```ts
  class Add implements fc.AsyncCommand<M, R> {
    constructor(readonly t: string) {}
    check = () => true;
    async run(m: M, r: R) {
      await r.page.getByRole('textbox').fill(this.t);
      await r.page.keyboard.press('Enter');
      m.items.push(this.t);
      await expect(r.page.getByRole('listitem')).toHaveCount(m.items.length);
    }
    toString = () => `add(${JSON.stringify(this.t)})`;
  }
  ```
- **Limits:** same cost and determinism limits as §4.1. A property only says what the model says. Specified examples (§1–2) still anchor the semantics.

### 4.3 Metamorphic testing (MT) for the oracle problem
- **What:** when the correct output of a single input is unknown, use **metamorphic relations (MRs)** between source and follow-up executions. Example: shortest path (G,a,b) has the same length as (G,b,a). MT "alleviates" but cannot completely solve the oracle problem. A small set of diverse MRs is recommended. MT is also useful when an oracle exists. Source: Chen et al., ACM CSUR 51(1) 2018, https://research.nottingham.edu.cn/ws/portalfiles/portal/31448151/51607.pdf ; listed in 29119-4 §5.2.11.
- **E2E MRs [INFERENCE]:**
  - Search: adding a filter never increases the result count.
  - Sort: reversing the sort reverses the order.
  - Export: exported CSV rows equal the on-screen total.
  - Pagination: the union of pages equals the unpaged list.
  - Locale: switching locale does not change amounts.
  - Idempotency: repeating a PUT leaves the state unchanged.
  - Commutativity: applying two discounts in either order gives the same total, when the spec says so.
- **Limits:** an MR is a necessary property, not a sufficient one. A program can satisfy every MR and still be wrong.

---

## 5. E2E-specific engineering concerns

### 5.1 Isolation and data seeding
- Playwright: each test should be "completely isolated … with its own local storage, session storage, data, cookies"; browser contexts give a clean slate. Reuse the auth state through a setup project. "If working with a database then make sure you control the data" — https://playwright.dev/docs/best-practices ; https://playwright.dev/docs/browser-contexts
- **Rules [INFERENCE]:**
  - Seed in Given through the API or factories, never through UI steps of another feature.
  - Use a per-test tenant or unique prefix so parallel runs never collide.
  - Every test must be runnable alone and in any order.
  - Fixtures (https://playwright.dev/docs/test-fixtures) own setup and teardown.

### 5.2 Determinism: clock and network
- **Clock:** `page.clock.setFixedTime`, `install` + `pauseAt` / `fastForward` / `runFor`. These override `Date`, timers, `requestAnimationFrame` and `performance`. Example from the docs: test a 5-minute inactivity logout with `fastForward('05:00')` — https://playwright.dev/docs/clock . Server-side time needs its own injectable clock. [INFERENCE]
- **Network:**
  - `page.route` + `fulfill` stubs a response.
  - `route.fetch` + patch modifies a real one.
  - `routeFromHAR` replays a recording, with strict URL, method and POST-body match.
  - `routeWebSocket` handles WebSockets.

  Source: https://playwright.dev/docs/mock . "Avoid testing third-party dependencies … use the Playwright Network API" — https://playwright.dev/docs/best-practices
- **Stub vs real [INFERENCE]:**
  - Never stub the system under test's own backend in a ground-truth suite.
  - Stub only third parties you do not control.
  - Fault-inject your own dependencies at the network or proxy level (Toxiproxy, container stop) [from memory].
  - Every unhappy branch that depends on a dependency failing needs a test that *forces* that failure deterministically.

### 5.3 Flakiness avoidance
- Use web-first assertions: `await expect(locator).toBeVisible()` retries; `expect(await locator.isVisible()).toBe(true)` does not. Prefer role or label locators over CSS or XPath. Collect a trace on the first retry — https://playwright.dev/docs/best-practices ; https://playwright.dev/docs/test-assertions
- No `waitForTimeout` or sleeps. Wait on a condition: an element state, `waitForResponse`, or `expect.poll` for side channels like a queue or log. [INFERENCE, consistent with the docs]
- Larger tests are more flaky. When a stable test turned flaky, the cause was a real production bug in about 1/6 of tracked cases, so treating flakes as noise eventually hides real bugs — https://testing.googleblog.com/2017/04/where-do-our-flaky-tests-come-from.html ; Google re-run and quarantine policy: https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html
- Retries (https://playwright.dev/docs/test-retries) only *detect* flakiness. A test that passes only on retry is "flaky" and must be fixed. It is never an acceptable steady state for a suite meant as ground truth. [INFERENCE]

### 5.4 Pyramid vs trophy: when e2e is the ground truth
- Pyramid (Vocke / Fowler): "push your tests as far down the test pyramid as you can". If a higher-level test finds a bug no lower test catches, add a lower-level test. Avoid duplication, but "if a higher-level test gives you more confidence … you should have it" — https://martinfowler.com/articles/practical-test-pyramid.html
- Trophy (Dodds): mostly integration tests; "the more your tests resemble the way your software is used, the more confidence they can give you" — https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications
- **Synthesis for this task [INFERENCE]:** with unlimited resources, the e2e suite is the *acceptance oracle for the requirement*. It must cover every clause and every decision-table column at the system boundary. Lower-level tests may add combinatorial depth, but the e2e suite must not delegate any clause to them. The pyramid argument is about cost, and cost is waived here. Keep Fowler's first rule as a separate improvement: when e2e catches a bug, add a lower test too.

---

## 6. Test oracle design: what to assert

- **Taxonomy (Barr et al., IEEE TSE 41(5) 2015):** oracles can be **specified** (specs, contracts, state models), **derived** (from metamorphic relations, regression or prior versions, docs, mined specs), or **implicit** (crash, exception, deadlock: "blatant faults", but context-dependent). The fourth case is a **human** oracle with reduced cost. Source: https://coinse.github.io/publications/pdfs/Barr2015qd.pdf
- **E2E oracle layers [INFERENCE].** Each test declares which layers its clause requires:
  1. **UI:** visible text, role state (enabled, disabled, checked), URL or route, focus, absence of forbidden elements.
  2. **API response:** status, error code or body schema (`page.waitForResponse`), headers such as Retry-After.
  3. **Persisted state:** read back through the public read API or a reload, not private tables. A raw DB read is allowed only when no public read path exists. Assert both the presence of what should exist and the absence of what should not, for example "no order row on payment failure".
  4. **Side effects:**
     - email received in a mail sink
     - message on the queue or topic
     - outbound webhook captured by a stub server
     - log record with level and correlation id
     - metric or alert fired
     - audit trail entry
  5. **Non-effects:** what must NOT happen. No charge, no email, no enqueue, no partial write. This is where "early return with default" bugs hide.
  6. **Implicit:** no uncaught console errors (`page.on('pageerror')`), no 5xx responses outside the forced fault, no unhandled promise rejections. Run as a global after-each check.
- **Unhappy-action oracle map [INFERENCE]:**

  | Required action | Minimum oracle |
  |---|---|
  | early return / default value | UI shows the default; API returns the default; no downstream call (stub records 0 calls); state unchanged |
  | raised / returned error | exact status and error code; user-facing message; no partial persistence |
  | delegation to helper/service | stub or real collaborator received the call with the expected payload, exactly once; result reflected in UI |
  | failure shown to user | role=alert or toast text; form state preserved; retry affordance if specified |
  | failure sent to log/queue/telemetry/alert | record found with severity, correlation id and payload fields; assert through a sink, polled with `expect.poll` |
- **Oracle strength [INFERENCE]:** an assertion that would also pass on the wrong branch is a weak oracle. Example: "toast visible" passes for both the success and the error toast. Every unhappy test needs at least one assertion that *distinguishes* its branch from its siblings.

---

## 7. Risk-based prioritisation

- Risk level = likelihood × impact. Risk-based testing selects and prioritises test activities from risk analysis. Product risks include missing or wrong functionality, incorrect calculations, security, performance, etc. (ISTQB §5.2) — https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf
- **E2E use [INFERENCE]:** with unlimited resources, risk does not decide *whether* a clause is covered; every clause is covered. Risk decides the *depth*:
  - pairwise vs 3-way
  - 2-value vs 3-value BVA
  - 0-switch vs 1-switch
  - all-transitions (invalid attempts)
  - the number of stateful-PBT examples
  - the run order: high risk first, fail fast

  High risk covers money, auth, data loss, irreversible actions, privacy and external notifications.

---

## 8. DESIGN PROCEDURE (agent-runnable)

**Input:** a requirements doc or issue. **Output:** an e2e suite and a traceability matrix.

1. **Extract clauses.** Split every sentence into atomic clauses `C<n>`: trigger, conditions, outcome. Mark each clause *explicit* or *derived* (implied by negation or an else-branch). For every conditional clause, write the complement clause too.
2. **Example-map.** Group the clauses under rules (`R<n>`). Write 1–3 key examples per rule. Log every ambiguity as a question `Q<n>`, for example inclusive boundaries, the error message text, or a silent failure mode. Do not invent the answer. Mark the dependent tests `blocked-on Q<n>`.
3. **Inventory the unhappy actions.** For each clause, list each failure mode: invalid input, unauthorised, not found, conflict, dependency down or slow, quota, timeout. For each one, record the *required action*: default, error, delegate, show user, emit to a sink. A missing action becomes a `Q`.
4. **Model the inputs.** Per clause, list the parameters (fields, role, flags, data shape, time, environment). Apply EP: valid and invalid partitions `P<n>`. Apply BVA to ordered partitions: 3-value for high risk, 2-value otherwise, `B<n>`.
5. **Model the logic.** Where ≥ 2 conditions interact, build a decision table. Use cause-effect constraints to drop infeasible columns. Every feasible column `D<n>` is a coverage item, and its action rows come from step 3.
6. **Model the states.** If the feature has a lifecycle, session or async job, build a state table: states `S`, valid transitions `T`, invalid cells `I`. Target valid-transitions (0-switch) coverage. Add all-transitions coverage (one invalid attempt per test) for high risk. Add 1-switch pairs for flows with re-entry: retry, resubmit, undo.
7. **Model the flows.** Write the main, alternate and exception flows `F<n>`. Each exception flow must reference a decision column or an invalid transition.
8. **Combine the environment.** Write a PICT model for the environment and configuration parameters, with constraints and `~` negative values. Use t = 2, or t = 3 on high-risk sub-models. Each row is `E<n>`.
9. **Add generative layers.**
   - (a) A stateful model-based test (Hypothesis or fast-check) over the commands from step 6, with invariants taken from the cross-cutting clauses.
   - (b) MRs for clauses whose exact output is hard to specify: search, sort, aggregates, pagination, export.
10. **Error-guess and charter.** Run the e2e fault checklist from §2.9 against every clause. Add tests `G<n>` for the faults that apply. Write 1–3 exploratory charters for the residual risk.
11. **Assemble test cases.** Pack the coverage items into tests. Each test has exactly one When action, or one command sequence. A test may cover several *valid* items but **at most one invalid item**, to avoid masking (ISTQB, PICT). Assign IDs `TC-<clause>-<n>`.
12. **Design oracles.** For each test, pick the oracle layers from §6 that the clause requires. Every unhappy test needs a branch-distinguishing assertion, a non-effect assertion, and a side-channel assertion when the action is "sent somewhere".
13. **Engineer determinism.** Per test, define:
    - the seed fixture: API or factory, unique tenant
    - the clock: `setFixedTime` / `install`, plus a server clock
    - the network policy: real for the system under test; stubbed only for third parties
    - the fault-injection hook for each forced failure
    - waits that use only web-first or `expect.poll` assertions
14. **Emit the matrix and coverage.** Compute coverage per technique, as in §6.2 of 29119-4: covered items / identified items. Every row ≥ 1 test, every test ≥ 1 row, all percentages 100% or explicitly waived with a `Q` or risk justification.

**Traceability matrix template:**

| Clause | Kind | Coverage items (P/B/D/S/T/I/F/E/G) | Test id | Oracle (UI · API · state · side-effect · non-effect) | Determinism (seed · clock · net/fault) | Risk |
|---|---|---|---|---|---|---|
| C2 rows>10 000 → queue | explicit | B: 10 000/10 001/10 002 (3-val); D: R3 | TC-C2-1 | UI toast "We'll email…" · 202 · job row via `/jobs` · mail sink has email · no download event | tenant t42 seeded 10 001 rows · fixed clock · real queue | H |
| C4 queue down | derived (Q1 answered) | D: R4; G: dependency down | TC-C4-1 | role=alert text · 503 code `EXPORT_UNAVAILABLE` · no job · alert sink has `export.enqueue_failed` with tenant id | toxiproxy cut queue · fixed clock | H |

---

## Actionable rules

1. Every requirement sentence is split into atomic clauses. Each clause has exactly one trigger, condition set and expected outcome.
2. Every conditional clause has its complement clause (else-branch) written explicitly, even when the spec is silent.
3. Every clause maps to ≥ 1 test id, and every test id maps to ≥ 1 clause. Orphans on either side fail the suite.
4. Every unhappy outcome names its required action: default, error, delegate, show user, or emit to a sink. If the action is unspecified, record a question; never guess it.
5. Every input parameter has documented valid and invalid partitions. Each partition is exercised by ≥ 1 test (Each Choice = 100%).
6. Every ordered partition has BVA. Use 3-value BVA for high-risk clauses and ≥ 2-value elsewhere. Boundary inclusivity must be cited from the spec or logged as a question.
7. Any clause with ≥ 2 interacting conditions has a decision table. Every feasible column has a test (100% column coverage).
8. Any feature with a lifecycle has a state table. Valid-transition (0-switch) coverage is 100%. High-risk features also have every invalid transition attempted, one per test.
9. Flows with re-entry (retry, resubmit, undo, back) have 1-switch coverage of the re-entry pairs.
10. A test contains at most one invalid input or invalid transition (no defect masking).
11. Environment and configuration interactions are covered by a constrained PICT model at t ≥ 2, and t = 3 for high-risk sub-models. Infeasible combinations are removed by constraints, not by deleting rows.
12. Every dependency the feature calls has ≥ 1 test that deterministically forces its failure (error, timeout, slow). That test asserts the required unhappy action.
13. Every unhappy-path test has an assertion that would fail if a sibling branch had run (branch-distinguishing oracle).
14. Every unhappy-path test asserts the non-effects: no charge, no write, no enqueue, no email, as applicable.
15. Every "failure sent somewhere" clause is asserted at its sink (log, queue, metric, alert, webhook) with severity and correlation id, using a polled assertion.
16. Persisted state is verified by reload or the public read API. A raw DB read is allowed only when no public read path exists, and the matrix states why.
17. A global after-each check fails on uncaught page errors and on unexpected 5xx responses (implicit oracle).
18. Tests never use fixed sleeps. Waiting uses only web-first `expect` or `expect.poll`.
19. Locators are role, label or test-id based, never CSS or XPath structure.
20. Each test runs alone, in any order and in parallel. It seeds its own data via API or fixture in an isolated tenant or context.
21. Time-dependent clauses control both the browser clock (`page.clock`) and the server clock.
22. The system under test's own backend is never stubbed in the ground-truth suite. Only third parties outside the team's control may be stubbed or HAR-replayed.
23. Stateful features have a model-based or stateful property test. Its model is simpler than the implementation, and its invariants come from cross-cutting clauses.
24. Clauses whose exact output is impractical to specify have ≥ 2 diverse metamorphic relations.
25. The e2e fault checklist (double submit, refresh, back, two tabs, session expiry, offline, Unicode or long input, DST or timezone) is applied to every clause. Applicable items get tests.
26. Each risk is scored as likelihood × impact. Risk raises depth (BVA arity, t-way, switch level, property-test examples) and run order, never omission.
27. A test that passes only on retry is classed as failing until its root cause is fixed.
28. The matrix reports per-technique coverage %, computed as identified vs covered items. Anything below 100% carries a named question or a risk waiver.

## Research agent notes (unverified sources)

I did not check Example Mapping's origin post, 1-switch / Chow 1978, the classification-tree origin, the cause-effect origin, the NIST ≤6-way claim, Toxiproxy or Hendrickson's charter template; those are tagged [from memory]. The 29119-4 standard text is paywalled, so I only had its table of contents and the technique details come from ISTQB.

Risk: the main agent must save this file itself, because I could not write it.

### Critical Files for Implementation
- `local://research-e2e-design.md` — the target artifact; paste the block above.
- https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf — coverage definitions for EP, BVA, decision table, state transition and risk.
- https://github.com/microsoft/pict/blob/main/doc/pict.md — combinatorial rules: constraints, negative values, no input masking.
- https://playwright.dev/docs/best-practices — isolation, web-first assertions, locators, third-party stubbing.
- https://fast-check.dev/docs/advanced/model-based-testing/ — the stateful model-based pattern for Playwright.
