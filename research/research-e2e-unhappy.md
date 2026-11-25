# E2E verification of unhappy paths — techniques, oracles, taxonomy

Scope: how a black-box or grey-box e2e test **proves the system took the correct action** when something goes wrong. Audience: a DESIGNER skill (writes the suite) and a JUDGE skill (grades the suite).

Terms used below:
- **Trigger**: how the test causes the failure.
- **Oracle**: what the test observes to decide pass or fail.
- **Channel**: where an effect lands: UI, HTTP response, DB, queue, mail, telemetry, or a third party.

---

## 0. Core model [INFERENCE]

Every unhappy-path test is a triple **(trigger, expected action, oracle set)**. The action has exactly one *primary* outcome type (§1–§5). A full oracle set has four parts:

1. **User-visible** — what the caller sees: UI text and role, HTTP status, error body.
2. **Persisted state** — DB rows, files and cache after the step settles.
3. **Side-effect channel** — log, span, metric, error-tracker event, queue or DLQ message, email, webhook, or a third-party call.
4. **Negative** — what must *not* have happened: no write, no second charge, no email, no leaked data.

A test that checks only (1) can pass when the code takes the wrong action behind a correct-looking screen. Example: the UI shows "Payment failed" but the charge still went through.

---

## 1. Outcome: early return with default / fallback value

**What it is.** The code catches a failure or a missing value and continues with a defined default (empty list, cached value, feature off).

**E2E observation.**
- Trigger the cause at the dependency boundary, not in the app:
  - Browser-side: Playwright `page.route(pattern, r => r.abort('connectionrefused'))` or `r.fulfill({status: 503})`.
  - Server-side: take the dependency down with Toxiproxy `down`, or stub it to fail with WireMock or Mountebank.
- Oracle:
  - The page or response shows the **specified default**: the exact empty-state copy, or `[]`.
  - The status code stays success (200, not 500) when the spec says "degrade, don't fail".
- Grey-box check: a log line or span event records that the degradation happened. Otherwise the fallback is invisible to operators.

**Mini example** (from the Toxiproxy README, opened): the spec says "if the tag store is down, show the post with no tags".
```ruby
Toxiproxy[/redis/].down do
  assert_equal [], @post.tags   # fallback value, not an exception
end
```
E2E version:
```ts
// tag service unreachable
await toxiproxy.proxy('redis_tags').disable();
await page.goto('/posts/1');
await expect(page.getByRole('article')).toContainText('Post body');
await expect(page.getByTestId('tags')).toHaveText('');            // default
await expect(page.getByRole('alert')).toHaveCount(0);             // no error shown
```

**Limits.**
- A default that equals a legal real value (an empty list) cannot be told apart from "no data". Seed data so the real answer is non-empty.
- A fallback served from cache needs a primed cache, then the dependency killed, then a stale-but-correct value asserted.

**Sources.** https://github.com/Shopify/toxiproxy (opened); https://playwright.dev/docs/api/class-route (opened).

---

## 2. Outcome: error mapped to status code / error body

**What it is.** The failure surfaces as a defined protocol error, for example a status code plus an RFC 9457 `application/problem+json` body with `type`, `title`, `status`, `detail` and `instance`.

**E2E observation.**
- Call the real HTTP endpoint (Playwright `request` fixture, or any HTTP client).
- Assert:
  - exact status;
  - `Content-Type`;
  - stable `type` URI or error code;
  - no stack trace or internal details in `detail` (a security requirement).
- For browser flows: `page.waitForResponse(predicate)`, then assert on the response the UI consumed and the UI's rendering of it.

**Mini example**
```ts
const r = await request.post('/api/orders', { data: { qty: 0 } });
expect(r.status()).toBe(422);
expect(r.headers()['content-type']).toContain('application/problem+json');
const body = await r.json();
expect(body.type).toBe('https://example.com/probs/invalid-quantity');
expect(JSON.stringify(body)).not.toMatch(/at \w+\.\w+ \(|SQLSTATE|stack/i);
```

**Limits.**
- The status code alone is weak: many branches share 400 or 500. Assert the machine-readable code too.
- Schema-driven fuzzers can check "invalid input → 4xx" in bulk (§9). They cannot tell which 4xx the spec requires.

**Sources.** RFC 9457 https://www.rfc-editor.org/rfc/rfc9457.html (via search snippet); Playwright network docs https://playwright.dev/docs/network.

---

## 3. Outcome: delegation (retry, fallback provider, compensation, circuit breaker)

**What it is.** On failure, the code hands off to something else:
- retries the same dependency;
- switches to provider B;
- runs a compensating action (refund, release a hold);
- opens a circuit breaker.

**E2E observation.** Put a **recording fake** at each dependency, then assert **who was called, in what order, how many times**.
- WireMock records every request in a journal. `verify(exactly(n), postRequestedFor(...))` checks counts, including `exactly(0)` (https://wiremock.org/docs/verifying/).
- WireMock **Scenarios** (a state machine) script a sequence such as "fail, fail, succeed" to test retry-then-succeed (https://wiremock.org/docs/stateful-behaviour).
- WireMock faults: `EMPTY_RESPONSE`, `MALFORMED_RESPONSE_CHUNK`, `RANDOM_DATA_THEN_CLOSE`, `CONNECTION_RESET_BY_PEER`, plus fixed, lognormal and chunked-dribble delays (opened).
- Mountebank faults: `CONNECTION_RESET_BY_PEER`, `RANDOM_DATA_THEN_CLOSE`. Injection needs `--allowInjection` (https://www.mbtest.dev/docs/api/faults).
- MSW (browser or Node): `HttpResponse.error()` for a network error, or any error `Response` (https://mswjs.io/docs/http/mocking-responses/network-errors).
- Playwright `route.fetch()` + `fulfill({response, json})` mutates a *real* response, for example to inject a bad field (opened).

**Mini example** — the spec says "if provider A times out (>2 s), charge via provider B; never charge both":
```ts
await wiremockA.stub({ request:{method:'POST',url:'/charge'},
  response:{ status:200, fixedDelayMilliseconds: 5000 }});
await placeOrder(page);
await expect(page.getByRole('status')).toHaveText(/payment confirmed/i);
expect(await wiremockB.count({method:'POST',url:'/charge'})).toBe(1);
// late success of A must not double-charge:
await wiremockA.waitForJournal(1);
expect(await db.one('select count(*) from charges where order_id=$1',[id])).toBe(1);
```
**Retry assertions:**
- exact attempt count;
- backoff spacing measured from journal timestamps (or controlled with a fake clock);
- the same idempotency key on every attempt;
- stop after N attempts, then the terminal action (§5 DLQ, §2 error).

**Compensation assertions:**
- after step k fails, every committed step < k shows its compensating call;
- persisted state equals the pre-saga state, or the specified terminal state such as `CANCELLED`.

**Limits.**
- Fakes encode *your belief* about the dependency's error shape. Pair them with contract tests, or with recorded real error responses (HAR) when you can capture them.
- Timing assertions are flaky unless time is controlled.

---

## 4. Outcome: failure shown to the user

**What it is.** A toast, an error page, inline field validation, or a live-region announcement.

**E2E observation (Playwright).**
- Query by role, not CSS:
  - `getByRole('alert')` for urgent errors;
  - `getByRole('status')` for advisory messages.
- `expect(field).toHaveAccessibleErrorMessage('…')` (added v1.50) checks the `aria-errormessage` / `aria-invalid` wiring, not only that the text is visible (https://playwright.dev/docs/api/class-locatorassertions).
- WCAG technique ARIA19: errors are injected into `role=alert` or `aria-live` regions so assistive technology announces them (https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA19).
- Error page: assert the HTTP status of the navigation response *and* the rendered page.
- Assert **focus** moves to the error summary or first invalid field: `expect(locator).toBeFocused()`.
- Assert **preserved input**: the form keeps the user's values after a failed submit.
- Toasts: control time with the **Playwright Clock API**. `page.clock.install()` and then `runFor` / `fastForward` show the toast and then its auto-dismiss without real waiting (https://playwright.dev/docs/clock).

**Mini example**
```ts
await page.clock.install();
await page.route('**/api/profile', r => r.fulfill({ status: 409, json:{code:'STALE'} }));
await page.getByRole('button', {name:'Save'}).click();
await expect(page.getByRole('alert')).toHaveText(/changed by someone else/i);
await expect(page.getByLabel('Display name')).toHaveValue('my edit'); // input kept
await page.clock.runFor(10_000);
await expect(page.getByRole('alert')).toBeHidden();                 // spec: auto-dismiss 8s
```

**Limits.**
- Role queries do not prove that a screen reader actually announced anything [INFERENCE]. Add axe scans if a11y is in scope.
- Stubbing at `page.route` skips the real server's error mapping. Run at least one test per error class against the real backend.

---

## 5. Outcome: failure sent somewhere (log, metric, span, error tracker, DLQ, outbox, email, webhook)

The **side-effect channel** is often the *only* proof of the required action ("alert ops", "dead-letter the message"). Capture each channel in the test environment and query it after the step.

| Channel | Capture in test env | Assertion |
|---|---|---|
| Structured logs | App writes JSON to stdout; harness tails the container log (Testcontainers log consumer [from memory]) or sends logs via OTLP to a collector with `file`/`debug` exporter | exactly one record with `level=error`, `event=payment_declined`, `order_id=…`; **no PII fields** |
| Traces | OTel SDK `InMemorySpanExporter` (in-process) or Collector `fileexporter` (out-of-process; OTLP JSON lines, https://opentelemetry.io/docs/specs/otel/protocol/file-exporter) | span `charge` has status `ERROR`, an `exception` event, the right parent; retry spans counted |
| Metrics | Scrape `/metrics` before and after, or collector file export | `payments_failed_total{reason="declined"}` delta == 1 |
| Error tracker | Sentry **Spotlight** sidecar receives SDK envelopes locally (https://spotlightjs.com/docs/sidecar; `SPOTLIGHT_CAPTURE=1` writes them to a file, https://spotlightjs.com/docs/contribute/development/); or a custom SDK transport/`beforeSend` hook [from memory] | one event, correct fingerprint/tags; **zero** events for *expected* errors like validation |
| DLQ | Real broker via Testcontainers / LocalStack; SQS redrive `maxReceiveCount` (https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) | after N poison deliveries: message in DLQ with the original body, absent from the source queue, side effect applied 0 times |
| Outbox | Query the outbox table in the same DB (pattern: https://microservices.io/patterns/data/transactional-outbox.html) | business row and outbox row both committed, or both absent (atomicity); relay publishes exactly once |
| Email | Mailpit SMTP catcher plus REST API `/api/v1/messages` (https://mailpit.axllent.org/docs/api-v1); **Mailpit Chaos** returns SMTP 4xx/5xx at Sender, Recipient or Auth stage, e.g. `--chaos-triggers Sender:451:100` (opened) | right recipient and template; on SMTP failure, retried or queued per spec; no duplicate after a retry |
| Webhook | WireMock or Mountebank receiver plus journal | payload, signature header, retry on 5xx, stop after N, DLQ or disable |

**Mini example (OTel, Python in-process)** [from memory API names]:
```python
exporter = InMemorySpanExporter()
provider.add_span_processor(SimpleSpanProcessor(exporter))
client.post("/orders", json=bad_card)
span = next(s for s in exporter.get_finished_spans() if s.name == "charge")
assert span.status.status_code == StatusCode.ERROR
assert any(e.name == "exception" for e in span.events)
```

**Limits.**
- Asserting exact span or log names couples tests to instrumentation that changes when libraries update (noted at https://python-testing-debugging.com/…/tracing-a-request-through-a-test-with-opentelemetry). Assert only fields the **requirement** names, such as "alert ops" → error event exists.
- Async channels need a bounded poll (`expect.poll` or retry-until-deadline), never a fixed sleep.

---

## 6. Fault injection — choose the layer

| Layer | Tool | Good for | Limit |
|---|---|---|---|
| Browser↔server | Playwright `route.abort(code)` (codes include `connectionrefused`, `connectionreset`, `timedout`, `namenotresolved`, `internetdisconnected`), `fulfill`, `fetch`+modify (opened); `routeFromHAR` replays recorded traffic (https://playwright.dev/docs/mock) | client error handling, offline, garbage JSON | server logic is not exercised |
| Server↔HTTP dep | WireMock, Mountebank, MSW (Node) | status codes, slow bodies, malformed responses, sequences | fake ≠ real contract |
| Server↔any TCP dep | **Toxiproxy** toxics: `latency`, `down`, `bandwidth`, `slow_close`, `timeout`, `reset_peer`, `slicer`, `limit_data`, `packet_loss` (opened) | DB, Redis, broker under slow, partial, reset conditions; works with real deps in Testcontainers | TCP only; no semantic errors (e.g. a specific SQL error) |
| Inside the process | **Failpoints**: Go `etcd-io/gofail` (`GOFAIL_FAILPOINTS='name=return("x")'`, or HTTP `GOFAIL_HTTP` + `curl -XPUT`) https://github.com/etcd-io/gofail; `pingcap/failpoint` (`failpoint-ctl enable`, `GO_FAILPOINTS`) https://github.com/pingcap/failpoint; Rust `fail` crate `fail_point!("name")` + `FAILPOINTS=name=return` with feature `fail/failpoints` (https://docs.rs/fail) | "crash after DB commit, before publish" — the partial-failure points nothing outside can reach | needs a test build; grey-box |
| Cluster / k8s | **Chaos Mesh**: NetworkChaos (delay, loss, partition…), HTTPChaos, IOChaos, PodChaos, StressChaos (https://chaos-mesh.org/docs/basic-features) | pod kill mid-request, disk full, partitions in a full env | coarse; slower; needs k8s |
| Time | Playwright Clock (browser); injectable server clock or libfaketime [from memory] | expiry, timeouts, backoff, TTL | server and browser clocks are separate; control both |
| Real deps | Testcontainers (https://testcontainers.com) | real constraint violations, real isolation behaviour, real broker redelivery | slower startup |

Rule of thumb [INFERENCE]: pick the **outermost** layer that can produce the condition. Use failpoints only for crash windows *between* two internal steps.

---

## 7. Negative assertions ("nothing else happened")

**Technique.** Snapshot every side-effect channel **before** the action, then diff **after** it settles.

**Channels to cover:**
- DB tables the feature touches: row counts and `updated_at`;
- outbox and queue depth;
- Mailpit message count;
- WireMock journal for every third party, using `verify(exactly(0), …)`;
- error-tracker event count;
- audit log.

**"After it settles"** must be bounded. Use one of:
- wait for a positive completion signal, such as the response or a span end;
- drain the queue;
- advance a fake clock past every scheduled retry;

then assert the count did not change.

**Mini example** — the spec says "a declined card writes no order, sends no email, charges at most once":
```ts
const before = await snapshot(['orders','outbox'], mailpit, psp);
await submitWithCard(page, '4000000000000002'); // decline
await expect(page.getByRole('alert')).toHaveText(/declined/i);
await drainWorkers(); await page.clock.runFor(RETRY_HORIZON_MS);
expect(await diff(before)).toEqual({ orders:0, outbox:0, mail:0, pspCharges:1 });
```

**Limits.**
- "Nothing happened" can only be proved for the channels you watch. The JUDGE must list unwatched channels as gaps.
- A wait that is too short gives false passes.

---

## 8. Partial failure, rollback, idempotency, concurrency

**Partial failure / rollback.**
- Use a failpoint at each step boundary of a multi-step write: after step 1, after the DB commit, before the publish.
- Assert the system ends in a **specified** state: fully rolled back, compensated, or resumable. Then re-run the operation and assert it completes exactly once.
- Outbox pattern: a crash between commit and publish must still publish later, exactly once.

**Idempotency.**
- Send the same request twice with the same `Idempotency-Key`, sequentially and then concurrently.
- Stripe semantics, useful as a reference oracle:
  - the first result is stored and replayed, *including errors*;
  - the same key with different params is rejected;
  - validation failures and concurrent-conflict outcomes are not stored.
- Source: https://docs.stripe.com/api/idempotent_requests (via search snippet).
- Assert:
  - responses are equal;
  - side effects (charges, emails, rows) happen exactly once;
  - the mismatched-params replay is an error.

**Retries exhausted.**
- Use a WireMock Scenario or a Toxiproxy `reset_peer` that never heals. Advance the clock.
- Assert:
  - attempt count == N;
  - the terminal action (DLQ, error status, user message);
  - no attempt N+1.

**Concurrency / races at e2e.**
- Fire K identical or conflicting requests with `Promise.all`, or use two browser contexts acting at once. Examples: last seat, double-submit, two editors.
- To make the race deterministic, hold one request in `page.route` until the other completes, then release it.
- Oracle = an **invariant**, not a specific winner:
  - seats sold ≤ capacity;
  - exactly one 201 and K−1 of 409;
  - the balance is conserved.
- Optimistic locking: a stale `If-Match` / version → 409 or 412, the user sees a conflict message, and nothing is overwritten.
- For DB-level isolation claims, black-box history checkers such as Jepsen's **Elle** infer anomalies from client-observed histories (https://arxiv.org/abs/2003.10554). This is the gold standard when the requirement claims serializability.

**Limits.**
- Random concurrency finds bugs by chance. Prefer forced interleavings (held routes, failpoint `pause`/`sleep`) for each specified race, plus one stress run.

---

## 9. Security-negative cases and input fuzzing

**Authorization denial (OWASP WSTG-ATHZ-04, IDOR):**
- use ≥2 users with different objects, and ≥2 privilege levels;
- swap object IDs in path, query, body and headers;
- expect 403 or 404 *per spec* (https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References).

Oracle set for a denial:
- status code;
- body does not leak whether the object exists (when the spec says 404-masking);
- **no state change** (§7);
- audit or security log entry if the spec requires it.

Cover each of: unauthenticated, expired token, wrong tenant, wrong role, revoked mid-session.

**Input fuzzing at e2e.**
- **Schemathesis** generates valid and **negative** inputs from OpenAPI or GraphQL (`--mode=negative`).
  - `negative_data_rejection`: invalid input must get an error status.
  - `positive_data_acceptance`: valid input must not be rejected.
  - Sources: https://schemathesis.readthedocs.io/en/stable/reference/checks/ ; paper https://arxiv.org/abs/2112.10328 (via search snippet).
- UI-level fuzzing: drive form fields with boundary and hostile strings (empty, whitespace, max+1 length, Unicode RTL and emoji, `<script>`, `' OR 1=1`, huge numbers, negative numbers, NaN) [INFERENCE].
- Assert:
  - the inline error is shown;
  - no 500;
  - nothing is reflected unescaped;
  - no row is written.

**Limits.** Fuzzers check generic properties: no 5xx, schema conformance. They cannot know business rules, so they *complement* the clause-mapped tests.

---

## 10. Taxonomy of unhappy-path classes + minimal oracle set

For **every** requirement clause, enumerate each class below. Mark it *N/A with reason* or produce ≥1 test. Oracle columns: **U**ser-visible / **P**ersisted / **S**ide-effect / **N**egative.

| # | Class | Typical trigger | U | P | S | N |
|---|---|---|---|---|---|---|
| 1 | Invalid input (type/format/semantic) | bad field via UI and API; Schemathesis negative | 4xx + field-level error; `toHaveAccessibleErrorMessage`; input preserved | unchanged | no error-tracker event (expected error); optional validation metric | no row, no outbound call, no email |
| 2 | Missing / empty | omit required field; empty list/string/file; empty DB result | 4xx with field named, **or** the specified empty state | unchanged | — | no default silently persisted unless specified |
| 3 | Boundary / overflow | min−1, min, max, max+1; int overflow; oversized payload (413) | exact accept/reject at each edge | only in-range values stored, not truncated | — | no truncated or wrapped value stored |
| 4 | Unauthenticated / unauthorized | no token, expired, other tenant, low role | 401 vs 403 vs 404 per spec; redirect to login | unchanged | security/audit log if required | no data leak in body or timing; no write |
| 5 | Not found | unknown ID, deleted ID, soft-deleted ID | 404 / not-found page | unchanged | no error-tracker event | no auto-create unless specified |
| 6 | Conflict / duplicate | same unique key; same idempotency key; stale version | 409/412 or idempotent replay; user conflict message | one row only | — | no second charge/email/event |
| 7 | Dependency down | Toxiproxy `down`; route `abort('connectionrefused')` | specified fallback (§1) or error (§2) | consistent (no half-write) | error log/span `ERROR`; alert if required | no data loss; no partial row |
| 8 | Dependency slow | Toxiproxy `latency`/`timeout`; WireMock delay | spinner then timeout message at the specified bound | no duplicate from a late reply | timeout span/metric | late reply does not double-apply |
| 9 | Dependency returns garbage | WireMock `MALFORMED_RESPONSE_CHUNK`/`RANDOM_DATA_THEN_CLOSE`; `fulfill` with wrong schema | graceful error, not a crash page | unchanged | parse-error log with dependency name | no garbage persisted |
| 10 | Partial failure | failpoint between steps; Chaos Mesh pod kill | specified outcome (retry later / error) | rolled back or compensated or resumable — as specified | compensation calls in journal; outbox row | no orphan rows; no step applied twice after recovery |
| 11 | Timeout (own deadline) | Clock API + slow dep; request deadline exceeded | specified timeout UX/status (504/408/message) | no commit after the deadline unless specified | timeout logged once | no zombie work completing later |
| 12 | Concurrent modification / race | parallel requests; held routes; two contexts | one winner + specified loser message | invariant holds | conflict metric if specified | no lost update, no oversell |
| 13 | Resource exhaustion | quota/rate limit; disk full (IOChaos); pool exhausted (Toxiproxy `limit_data`); queue full | 429 + `Retry-After` or 503 per spec | unchanged | rate-limit metric/log | other tenants unaffected |
| 14 | Retries exhausted | never-healing fake + clock advance | terminal error to user or async notice | terminal state recorded (`FAILED`) | DLQ message / alert / tracker event | exactly N attempts, no N+1 |

Extra classes worth checking when relevant [INFERENCE]: expired or stale state (TTL, token, cache); out-of-order events; replayed webhook (signature + dedupe); locale/timezone/DST edges; feature flag off; schema/version skew between client and server.

---

## 11. Designer workflow (for skill A) [INFERENCE]

1. Split the requirement into atomic clauses (each "shall/must/if/unless/when"). Give each an ID.
2. For each clause, draw its decision table: conditions × outcomes. Each cell is a branch.
3. For each branch, choose the trigger at the outermost layer that can produce it (§6).
4. Name the primary outcome type (§1–§5) and write the four-part oracle (§0, §10).
5. Add negative assertions over **every** side-effect channel the feature can touch (inventory them once per feature).
6. Control nondeterminism: fake clocks, held routes, seeded data, unique per-test IDs, bounded polls.
7. Add one real-backend test per error class even when the others use stubs.

## 12. Judge workflow (for skill B) [INFERENCE]

1. Rebuild the clause and branch list from the requirement *without reading the tests*.
2. Map each test to the branches it covers. Missing branches = gaps.
3. For each covered unhappy branch, grade the oracle completeness (U/P/S/N). Missing parts = weak.
4. **Mutation thought-experiment:** for each branch, ask "if the code took a *different* unhappy action (return default instead of erroring; log instead of DLQ; retry 4× instead of 3×), would some assertion fail?" If no, the test is non-discriminating.
5. Flag flakiness smells: fixed sleeps, real time, unbounded waits, order-dependent shared data, stubs that never fail.
6. Flag over-coupling: assertions on incidental span names or exact log text that the requirement does not name.

---

## Actionable rules

1. Every requirement clause has an ID. Each clause maps to ≥1 test ID, and each conditional branch of a clause maps to ≥1 test ID.
2. For each clause, record all 14 taxonomy classes (§10) as either covered (test IDs) or `N/A: <reason>`. A blank entry fails.
3. Every unhappy-path test names exactly one primary expected action: `default | error | delegate | user-message | emit`.
4. Every unhappy-path test asserts the user-visible outcome **and** persisted state **and** each side-effect channel the spec names **and** ≥1 negative assertion.
5. Status-code checks also assert a stable machine-readable error code (`type` / `code`). Status alone does not satisfy rule 4.
6. Error bodies are asserted free of stack traces, SQL, internal hostnames and PII.
7. Fallback tests seed data so the real result differs from the default, and they assert the exact default value.
8. Delegation tests assert the delegate's call count and order from a request journal, and assert `exactly(0)` calls to paths that must not be taken.
9. Retry tests assert the exact attempt count, the same idempotency key on every attempt, the terminal action after the last attempt, and that no attempt N+1 occurs after the clock is advanced past the retry horizon.
10. Idempotency tests replay the same key both sequentially and concurrently. They assert identical responses and exactly-once side effects, and that the same key with changed params is rejected.
11. Partial-failure tests inject a fault at each step boundary (failpoint or chaos). They assert the specified end state and exactly-once completion on recovery.
12. Race tests force the interleaving (held route or failpoint pause) and assert an invariant (≤ capacity, one winner, conserved totals). They do not assert a specific winner unless the spec names one.
13. Authorization tests cover unauthenticated, expired, wrong tenant, wrong role and revoked mid-session. Each asserts the specified status, no existence leak (when masking is specified) and no state change.
14. UI error tests locate errors by role (`alert`, `status`) or `toHaveAccessibleErrorMessage`, and assert that input is preserved and that focus or visibility follows the spec.
15. Time-dependent behaviour (timeouts, toast dismissal, backoff, expiry) uses a controlled clock. No test contains a fixed sleep longer than a polling interval.
16. Async-channel assertions (queue, DLQ, mail, webhook, telemetry) use a bounded poll with an explicit deadline. Negative async assertions wait for a positive completion signal first.
17. Each feature has a channel inventory (DB tables, queues, outbox, mail, webhooks, third parties, tracker, metrics, audit log). Every unhappy test's negative assertion covers every channel in the inventory, or the gap is listed.
18. Each error class has ≥1 test against the real backend and real dependencies (containers). Stub-only coverage of an error class is a gap.
19. Expected errors (validation, not-found, authz) assert **zero** error-tracker events. Unexpected or infrastructure errors assert **exactly one**.
20. Telemetry assertions check only fields the requirement names (event exists, status `ERROR`, reason tag). Incidental span or log names are not asserted.
21. Schema-driven negative fuzzing (e.g. Schemathesis `--mode=negative`) runs on every public endpoint in scope, in addition to clause-mapped tests.
22. Every boundary is tested at min−1, min, max and max+1, and the persisted value is asserted not truncated.
23. JUDGE: a test that would still pass after swapping its primary expected action for any other action type is non-discriminating, and is marked failing.
24. JUDGE: a test whose fault injection cannot actually fire (stub never matched, toxic on an unused proxy) is invalid. Require evidence that the trigger fired, such as a journal hit or a toxic counter.

## Research agent notes (unverified sources)

I did not open these sources; they come from search snippets only: RFC 9457, the Stripe idempotency page, the Schemathesis checks and paper, gofail and pingcap/failpoint, Chaos Mesh, the SQS DLQ page, MSW, and the Spotlight pages. The OTel Python API names and the Testcontainers log consumer are [from memory], and I did not check them.

The content runs about 330 lines once saved. Nothing exists on disk until the main agent writes it to `local://research-e2e-unhappy.md`.
