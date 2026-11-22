# Code-review axes: evidence-based taxonomy for an accuracy-first multi-agent reviewer

Research date: 2026-11-21. Every claim below links a URL I opened, unless it is tagged `[from memory]`. "SWR" means SWR-Bench, "c-CRAB" means the Code Review Agent Benchmark, and "CRBugBench" means the "Lights-off" paper.

**Short answer:** about 23 axes, run as 6 always-on agents plus 4 that only start when the diff touches their area. The split follows how each axis is verified, not the axis count. The evidence shows that functional findings (logic, interface, resource, error) can be checked by execution and are detected with higher recall. Evolvability findings (readability, design, docs) make up about 75% of what humans fix in review, but have low benchmark F1. They must be grounded in the repo's own conventions and reported separately.

---

## 1. Source table

| # | Source | Type / date | What it contributes | URL |
|---|---|---|---|---|
| S1 | Mäntylä & Lassenius, TSE 2009 | Paper | 388 industrial (C/C++) + 371 student defects. **75% of review defects affect evolvability, not visible function.** | https://mmantyla.github.io/wiki/What+Types+of+Defects+Are+Really+Discovered+in+Code+Reviews%253F.html |
| S2 | Beller, Bacchelli, Zaidman, Juergens, MSR 2014 | Paper | Over 1,400 review changes in 2 OSS projects. 75:25 evolvability:functional holds (ConQAT 81/19 and 75/25). Taxonomy: Documentation, Visual repr., Structure (Organization, Solution approach) / Resource, Check, Interface, Logic, Support, Larger defects. 7–35% of comments discarded. 10–22% of changes not triggered by a comment. κ 0.5–0.6 on fine categories. | https://sback.it/publications/msr2014.pdf |
| S3 | Bacchelli & Bird, ICSE 2013 (Microsoft) | Paper | 570 comments: code improvements 29%, **defects only 14% (78)**. Of the 78 defect comments: 65 logic, 6 high-level, 5 security, 3 exception handling. "Understanding" is the 2nd most frequent comment type. Review "rarely detects deep, subtle, or macro level issues". | https://cabird.com/pdfs/bacchelli2013eoc.pdf |
| S4 | Sadowski et al., ICSE-SEIP 2018 (Google) | Paper | Review motivations: education, maintaining norms, gatekeeping, accident prevention, tracking history. Original aim: understandable code. Later additions: style/design consistency, adequate tests, security. Cites Rigby & Bird convergent practices (e.g. "two reviewers find an optimal number of defects"). | https://sback.it/publications/icse2018seip.pdf |
| S5 | McIntosh et al., MSR 2014 | Paper | Low review coverage and participation are linked to post-release defects. Lax participation means up to 5 more post-release defects per component. | https://rebels.cs.uwaterloo.ca/papers/msr2014_mcintosh.pdf |
| S6 | Thongtanunam et al., MSR 2015 | Paper | Future-defective and historically risky files get *less* scrutiny. Risky files with many lax, evolvability-focused reviews are more likely to have future defects. | https://rebels.cs.uwaterloo.ca/papers/msr2015_thongtanunam.pdf |
| S7 | SWR-Bench (Zeng et al., arXiv 2509.01494, 2025/26) | Benchmark | 1,000 PRs with full repo context. Best tool F1 18.73%. Functional types beat evolvability (Logic F1 26.2 vs max evolvability 16.45). Recall falls from 38% to 8.9% as issues per PR go from 1 to 5+. False-positive root causes: 48% lack of context. Multi-review aggregation raises F1. Fine-tuned CodeReviewer reaches F1 6.13%. | https://arxiv.org/html/2509.01494 |
| S8 | c-CRAB (arXiv 2603.23448, 2026) | Benchmark | Human review comments turned into executable tests. All tools together solve about 40%. Highest pass on robustness and functional correctness. Lowest on design and docs. Maintainability 7.9–27%. Tools over-raise robustness and testing comments compared with humans. | https://arxiv.org/html/2603.23448v2 |
| S9 | CRBugBench, "Lights-off" (arXiv 2610.13668, Oct 2026) | Benchmark | 1,800 tasks. Best agent catches 71.9% of bugs in its top-5 findings. Up to −25.5% on proprietary repos. Agents execute code in only about 10% of turns. Agents trust misleading PR descriptions. Exploration prompts give +5.8% at 1.10× cost. Multi-agent gives +4.7% at 5.55× cost. | https://arxiv.org/html/2610.13668 |
| S10 | "What types of review comments do developers resolve?" (arXiv 2510.05450) | Paper | LLM comment resolution rate: readability 43.3%, bugs 41.9%, maintainability 36.2%, design 28.6%. 60–70% of LLM comments go unresolved. Humans write more readability comments (46.0% vs 33.2%). | https://arxiv.org/html/2510.05450 |
| S11 | RevMate at Mozilla/Ubisoft (arXiv 2411.07091) | Field study | 8.1% / 7.2% of LLM comments accepted. Refactoring comments accepted 18.2–18.6%, functional 4.8–5.2%. Rejections: about 33% "incorrect" and about 35% "trivial" at Mozilla. | https://arxiv.org/html/2411.07091 |
| S12 | Spadini et al., ICSE 2018 | Paper | Test files are no less likely to have future defects than production files, so they deserve review. | https://sback.it/publications/icse2018b.pdf |
| S13 | Chromium/OpenSSL/PHP security-weakness study (arXiv 2311.16396) | Paper | Memory-buffer and resource-management weaknesses are the least discussed in review (4–9%) but cause 17–29% of known vulnerabilities. Only 39–41% of raised concerns get fixed. | https://arxiv.org/html/2311.16396v2 |
| S14 | ISO/IEC 25010:2023 (via arc42 and TNLab summaries) | Standard 2023-11 | 9 characteristics. New: safety. Usability became interaction capability (adds inclusivity, self-descriptiveness). Portability became flexibility (adds scalability). Security adds resistance. Maturity became faultlessness. | https://quality.arc42.org/articles/iso-25010-update-2023 ; https://tnlab.org/en/iso-iec-250102023-square-product-quality-model |
| S15 | OWASP ASVS 5.0.0 (published 2025-05-30) | Standard | 17 chapters, 345 requirements: V1 Encoding/Sanitization … V8 Authorization … V13 Config, V14 Data Protection, V15 Secure Coding & Architecture (deps, concurrency), V16 Logging & Error Handling. | https://softwaresecurity.com/asvs/5.0/ |
| S16 | OWASP Code Review Guide v2 (2017) | Guide | Organized by OWASP Top 10 2013. Separate chapters on reviewing logging code and error handling. | https://owasp.org/www-project-code-review-guide/assets/OWASP_Code_Review_Guide_v2.pdf |
| S17 | CWE Top 25 2025 (MITRE, 2025-12) | Standard | #1 XSS, #2 SQLi, #3 CSRF, **#4 Missing Authorization (up 5)**, #5 OOB write … #12 Unrestricted upload, #13 NULL deref (up 8), #15 deserialization, #20 info exposure, #22 SSRF, #24 IDOR-style CWE-639, #25 CWE-770 unbounded allocation. | https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25 |
| S18 | Google SRE Book, Appendix E + ch. 1 | Industry | Launch checklist: capacity, failover, timeouts/retries, monitoring, config change control, canaries, external dependencies. "Roughly 70% of outages are due to changes in a live system." | https://sre.google/sre-book/launch-checklist/ ; https://sre.google/sre-book/introduction |
| S19 | Microsoft Engineering Playbook, Reviewer Guidance (updated 2024-08-22) | Industry | Design pass, then quality pass: complexity, naming, error handling, race conditions, DB call count, security, PII in logs and names, tests with edge cases, scope ("don't block on out-of-scope"). | https://microsoft.github.io/code-with-engineering-playbook/code-reviews/process-guidance/reviewer-guidance |
| S20 | SmartBear/Cisco | Industry | 200–400 LOC over 60–90 min gives 70–90% defect discovery. Slower than 500 LOC/h. Max about 60 min per session. Checklists catch omissions. | https://smartbear.com/learn/code-review/best-practices-for-peer-code-review/ |
| S21 | Yuan et al., OSDI 2014 | Paper | **92% of catastrophic failures (198 studied) come from incorrect handling of non-fatal errors.** Many are trivial: empty handlers, "TODO" in handlers. | https://www.usenix.org/publications/login/feb15/yuan |
| S22 | Tu et al., ASPLOS 2019 (Go concurrency) | Paper | 171 bugs: 85 blocking, 86 non-blocking. 58% of blocking bugs come from message passing. Go's deadlock detector caught 2 of 21 blocking bugs. The race detector caught about half of non-blocking bugs. | https://blog.acolyer.org/2019/05/17/understanding-real-world-concurrency-bugs-in-go ; https://songlh.github.io/paper/go-study.pdf |
| S23 | Qin et al., PLDI 2020 (Rust) | Paper | All studied Rust blocking bugs are in *safe* code. Many concurrency bugs come from misreading lifetime and safety rules. | https://songlh.github.io/paper/rust-study.pdf |
| S24 | Raemaekers et al. (Maven) | Paper | About one third of library releases introduce at least one breaking change, minor releases included. | https://jstvssr.github.io/assets/pdf/semantic-versioning-maven.pdf |
| S25 | DB access bugs in Java (TOSEM, arXiv 2405.15008) | Paper | 423 bugs. SQL query, schema and API bugs cover 84.2%. Schema bugs are 22.5%. | https://arxiv.org/html/2405.15008v1 ; https://petertsehsun.github.io/papers/db_empirical_tosem.pdf |
| S26 | Yuan et al., ICSE 2012 (logging) | Paper | Developers rarely get log messages right first time and fix them later "as after-thoughts". | https://cs.uwaterloo.ca/~m2nagapp/courses/CS846/1171/papers/yuan_icse12.pdf |
| S27 | Sadowski et al., CACM 2018 (Google static analysis) | Paper | "Effective false positive" means the developer took no positive action. Code-review checks may have **up to 10%** effective FP. Compile-time checks must have zero. Analyzers with a high "Not useful" ratio are disabled. | https://storage.googleapis.com/gweb-research2023-media/pubtools/pdf/3198e114c4b70702b27e6d88de2c92734c9ac4c0.pdf |
| S28 | Spracklen et al., USENIX Sec 2025 | Paper | Hallucinated packages in LLM code: at least 5.2% (commercial models) and 21.7% (open models). 205,474 unique fake names. | https://arxiv.org/abs/2406.10279 |
| S29 | Veracode GenAI Code Security Report (2025-07-30) | Vendor | 45% of samples failed security tests across more than 100 LLMs. Java 72%. | https://www.veracode.com/genai-code-security-report |
| S30 | WebAIM Million 2025 | Survey | 94.8% of the top 1M home pages have detectable WCAG failures. 6 error types make up 96% of errors (low contrast 79.1%, missing alt 55.5%, missing labels 48.2%). | https://webaim.org/projects/million/2025 |
| S31 | Tang et al. 2023 (GDPR review) | Paper | Personal-data review is often deferred to specialized reviewers. Static analysis that pinpoints personal-data code helps them prioritize. | https://arxiv.org/abs/2306.11495 |
| S32 | Chroma "Context Rot" (2025-07-14) | Tech report | Performance drops as input grows, across 18 LLMs. Distractors make it worse, unevenly. | https://www.trychroma.com/research/context-rot |
| S33 | Anthropic multi-agent research post (2025-06-13) | Vendor | Agents use about 4× the tokens of chat, multi-agent about 15×. Token use explains 80% of performance variance. | https://www.anthropic.com/engineering/multi-agent-research-system |
| V1 | Cursor Bugbot "Building a better Bugbot" (2026-01-15) | Vendor | v1: 8 parallel passes with shuffled diff order, majority vote, validator model, filter out docs and compiler-warning categories. Resolution rate went from 52% to over 70%. The agentic version needed *aggressive* prompts. Planned next: run code to verify its own reports. | https://cursor.com/blog/building-bugbot |
| V2 | CodeRabbit "Understand findings" (read 2026-11-21) | Vendor | Four separate label axes: Type (nitpick / potential issue / refactor), Severity, **6 Categories** (functional correctness; security & privacy; data integrity & integration; performance & scalability; stability & availability; maintainability & code quality), Effort/reward. | https://docs.coderabbit.ai/change-stack/findings |
| V3 | Qodo "How code review works" (read 2026-11-21) | Vendor | Specialist agents: bugs, rule violations, **requirement gaps vs linked spec**, UX vs Figma, cross-repo breaking changes, skill findings. | https://docs.qodo.ai/code-review/overview |
| V4 | Greptile Key Features (read 2026-11-21) | Vendor | Defaults: logic, security, performance, architecture. Style and syntax can be turned down. Impacted callers and contracts found via a repo graph. Separate runtime E2E check (TREX). | https://www.greptile.com/docs/code-review/key-features |
| V5 | GitHub Copilot code review docs (read 2026-11-21) | Vendor | Lite tier: "bugs, security vulnerabilities, and style inconsistencies". Balanced tier sends complex logic, security-sensitive and cross-service changes to a higher-reasoning model. | https://docs.github.com/en/copilot/concepts/agents/code-review |

---

## 2. Consolidated axis taxonomy

Legend for the **Verify** column:
- **X** = execution: a failing test, fixture or snippet that passes after the fix.
- **T** = deterministic tool output.
- **R** = reasoning only. R-only findings must be capped in severity or dropped (see §5).

Tool names marked `[fm]` are `[from memory]`: well known, but I did not open their docs here.

### 2a. Functional axes (Beller/Mäntylä "functional", about 25% of human review fixes)

| # | Axis | Definition | Concrete checks | Evidence | Human / AI find rate | Verify |
|---|---|---|---|---|---|---|
| 1 | **Correctness / logic** | Code computes the intended result on intended inputs. | Wrong condition or operator, off-by-one, inverted branch, wrong variable, stale state, wrong unit, partial update. | S2 "Logic"; S3 (65 of 78 defect comments are logic); ISO functional correctness (S14); CodeRabbit category (V2) | Human: defects are 14% of comments (S3), functional changes 25% (S2). AI: SWR Logic P17.3 / R54.6 / F1 26.2 (S7). c-CRAB highest pass category (S8). CRBugBench 71.9% top-5 on GitHub, worse when non-local reasoning is needed (S9). | **X**: failing unit test or snippet |
| 2 | **Robustness / edge cases ("Check")** | Input and state validation at boundaries: null/empty, overflow, encoding, malformed input. | Unchecked index or nil, missing bounds or type check, integer overflow, empty collection, Unicode, time zones. | S2 "Check"; CWE-20 #18, CWE-476 #13 (S17); ASVS V2 (S15) | AI: SWR Check F1 19.6 (R 39.7) (S7). Tools **over-raise** robustness compared with humans, a false-positive risk (S8). | **X**: boundary-input test or property test. Drop if no input can reach the path. |
| 3 | **Error handling & resilience** | Failures are detected, propagated, reported and recovered from, without silent loss. Includes timeouts, retries, degradation and fail-safe (ISO 25010 safety). | Swallowed errors, empty catch or `_ = err`, `unwrap()` on fallible I/O, retry without backoff or idempotency, missing timeout, partial-failure rollback, wrong error type at an API boundary. | **S21: 92% of catastrophic failures from mishandled non-fatal errors**; ASVS V16 (S15); SRE timeouts/retries/degradation (S18); MS playbook (S19); c-CRAB "Error Handling" (S8) | Human: only 3 of 78 defect comments (S3), so heavily under-reviewed. AI: c-CRAB says comparable to humans (S8). | **X**: fault-injection test (mock dependency returns an error or timeout). **T**: errcheck, clippy `unwrap_used`, ruff BLE [fm] |
| 4 | **Concurrency** | Correct behavior under interleaving: races, deadlocks, leaks of goroutines/tasks, atomicity, ordering. | Shared mutable state without a lock, lock order, channel never closed or read, `WaitGroup` misuse, loop-variable capture, `await` holding a lock, `Send`/`Sync` misuse, async cancellation. | S22 (Go: 171 bugs, message passing causes 58% of blocking bugs); S23 (Rust: blocking bugs all in safe code); ASVS V15 safe concurrency; MS playbook "race conditions" (S19); S2 "Support/timing" | Tools miss most: Go deadlock detector 2 of 21, race detector about half (S22). No AI-specific stat found. | **X** + **T**: stress test under `-race` / TSan / loom / miri [fm]. A detector miss is *not* evidence of absence. |
| 5 | **Resource management** | Acquire/release of memory, handles, connections, goroutines, file descriptors. Bounded allocation. | Unclosed file or connection, `defer` in a loop, unbounded buffer or queue (CWE-770), use-after-free / unsafe aliasing in Rust `unsafe`, context not cancelled. | S2 "Resource"; CWE-770 #25, CWE-416 #7 (S17); S13 (resource weaknesses discussed least, 4–9%, but cause 17–29% of vulnerabilities) | AI: SWR Resource R 53.5 / F1 24.3 (S7). Humans rarely discuss it (S13). | **X**: leak test (goleak, tracemalloc, fd count) [fm]. **T**: miri / valgrind [fm] |
| 6 | **Security** | Confidentiality, integrity, authenticity, accountability, resistance (ISO). | Injection (CWE-79/89/78/77/94), path traversal, SSRF, deserialization, **authz missing or incorrect, IDOR** (CWE-862 #4, 863, 639), CSRF, secrets in code, weak crypto, JWT validation. | S15 ASVS V1–V16; S16 OWASP CRG; S17 CWE 2025; S29 (45% of LLM code fails) | Human: 5 of 78 defect comments (S3). Fixed only 39–41% of the time when raised (S13). AI: c-CRAB comparable to humans (S8). | **X**: proof-of-concept exploit test. **T**: semgrep, gosec, bandit, cargo-audit [fm]. Authz needs X plus repo context. |
| 7 | **Privacy / data protection** | Personal data is collected, stored, logged and returned only as needed. | PII in logs, metrics or error messages. Over-broad API responses. Missing retention or deletion. Client-side storage of sensitive data. Customer data in identifiers. | ASVS V14 (S15); CWE-200 #20 (S17); MS playbook "PII / EUII, logging PII" (S19); S31 (GDPR review deferred); CodeRabbit "security and privacy" (V2) | No frequency stat found. | **R+T**: trace sources to sinks (grep log calls for PII fields). **X**: capture logs in a test. |
| 8 | **Performance / efficiency** | Time behavior, resource utilization, capacity (ISO). | N+1 queries, O(n²) on hot paths, allocation in loops, sync I/O on an async path, missing pagination, cache misuse. | ISO (S14); MS playbook "more calls to the database than need be" (S19); SRE capacity and load test (S18); c-CRAB "Efficiency" (S8) | AI: comparable to humans in comment share (S8). | **X**: micro-benchmark before vs after, or query-count assertion. R-only allowed only for asymptotic class with a stated n. |
| 9 | **API / contract & compatibility** | Public surface (types, signatures, wire formats, CLI flags, schemas, env vars) stays compatible, or is versioned on purpose. | Removed or renamed export, changed default, changed error semantics, proto field renumbering, JSON field rename, semver bump mismatch, callers not migrated. | S2 "Interface"; **S24 (1/3 of releases break, minor releases included)**; ISO compatibility (S14); c-CRAB "Compatibility" + "Design: API signature" (S8); Qodo cross-repo conflicts (V3); Greptile impacted callers (V4) | AI: SWR Interface R 40.8 / F1 23.6 (S7). | **T**: cargo-semver-checks, gorelease/apidiff, api-extractor, buf breaking, oasdiff [fm]. **X**: compile the old caller against the new API. |
| 10 | **Data integrity & migrations** | Schema and data changes are safe, reversible and consistent with the code. Transactions and locking are correct. | Non-reversible migration, locking DDL on a large table, NOT NULL without default or backfill, code/schema deploy order, missing transaction, ORM query semantics, lost update. | **S25 (SQL, schema and API bugs are 84.2% of DB-access bugs; schema 22.5%)**; ASVS V2 transactions/locking; SRE backup/restore (S18); Bugbot rules for "unsafe migrations" (V1); CodeRabbit "data integrity and integration" (V2) | No review-detection stat found. | **X**: apply migration up/down on a fixture DB, run the code against both schemas. **T**: squawk / atlas lint [fm] |
| 11 | **Spec / requirements conformance** | The change does what the issue, spec or PR claims, completely and nothing else. | Acceptance criteria missed, partial implementation, behavior contradicts the issue, unrelated changes bundled in. | ISO functional completeness/appropriateness (S14); MS playbook "goals of the task achieved", "unrelated changes" (S19); Qodo requirement gaps (V3); S3 "understanding the reason of the change" is the top challenge | **Agents trust misleading PR descriptions and comments** (S9). | **X**: one test per acceptance criterion. R for scope creep. |

### 2b. Evolvability axes (about 75% of human review fixes; low AI precision)

| # | Axis | Definition | Concrete checks | Evidence | Human / AI find rate | Verify |
|---|---|---|---|---|---|---|
| 12 | **Test quality & adequacy** | Tests exist, assert the behavior, fail when it is broken, and are not flaky. | New branch with no test, assertion-free tests, mocks that mirror the implementation, test passes when the change is reverted, flaky sleeps, missing edge cases. | Google added review partly for "ensuring adequate tests" (S4); S12 (tests just as defect-prone); MS playbook "tests in same PR" (S19); c-CRAB "Testing" (S8) | Tools raise testing **more than humans**, so false positives are likely (S8). | **X**: revert the prod change and confirm the tests fail (mini mutation). Mutation tools [fm]. |
| 13 | **Maintainability / readability** | Analysability, modifiability, modularity (ISO). Naming, dead code, complexity, duplication. | Unclear names, dead or unused code, long function, deep nesting, copy-paste, magic numbers. | S1/S2 (75%); S3 code improvements 29% (58 practices, 55 dead code, 52 readability) | Humans: largest category. LLM: readability resolved 43.3%, maintainability 36.2% (S10). Refactor comments accepted 18% vs 5% functional (S11). But c-CRAB maintainability pass is only 7.9–27% (S8), and SWR evolvability F1 is at most 16.45 (S7). | **T**: linters and complexity metrics. **R** for the rest. Ground in repo conventions; label non-blocking. |
| 14 | **Idiom / language fit** | Uses the language's and the repo's established constructs. (The canon is already covered by existing research.) | Non-idiomatic error wrapping, iterator vs index loops, ownership/borrow style, `any`, mutable defaults. | S2 "Supported by language"; S3 "better code practices" | SWR E.1.2 language features F1 **7.85** (S7). **13% of false positives come from "lack of domain knowledge" and 3% from misjudging "anti-best-practices"** (S7). | **T**: clippy, staticcheck, ruff, typescript-eslint [fm]. R only if backed by a cited canon rule *and* matching repo precedent. |
| 15 | **Design / architecture / layering** | Components interact sensibly, respect boundaries, follow the house patterns, no needless abstraction. | Layer violation, wrong module owns the logic, leaky abstraction, new pattern next to an existing one, over-engineering. | S3 (6 high-level comments; review "rarely" finds macro issues); S5 (developers complain reviews skip design); MS playbook design pass (S19); Google "consistency of design" (S4) | LLM design comments resolved 28.6%, the lowest (S10). c-CRAB low pass (S8). Tools comment on design less than humans (S8). | **R** plus **T** for dependency rules (import-linter, depguard [fm]). Present as a question or advisory unless a rule is broken. |
| 16 | **Documentation** | Docs, comments, examples and changelog match the behavior. | Stale docstring, wrong example, missing changelog or README for a user-visible change, comment says "what" not "why". | S2 (code comments are the single largest change category); MS playbook README (S19) | SWR textual F1 14.3 (S7). c-CRAB low pass (S8). Bugbot filters docs findings out (V1). | **T**: doctest, rustdoc tests, link check [fm]. Doc/code contradictions are X-verifiable. |

### 2c. Production / non-code-surface axes

| # | Axis | Definition | Concrete checks | Evidence | Human / AI find rate | Verify |
|---|---|---|---|---|---|---|
| 17 | **Observability** | Logs, metrics and traces let operators detect and diagnose this change. | Error path with no log or metric, log at wrong level, missing context IDs, high-cardinality labels, PII in logs (cross-links to axis 7), no alert for a new failure mode. | SRE monitoring and "monitoring the monitoring" (S18); ASVS V16 (S15); S26 (logs fixed as afterthoughts); c-CRAB lists "information logging" under maintainability (S8) | No detection stat found. | **X**: run the failure path in a test, assert the log or metric is emitted. Otherwise R. |
| 18 | **Operability / config / deploy** | Safe rollout and rollback, config validation, feature flags, capacity. | New config without default or validation, flag not wired, env-specific paths, non-backward-compatible deploy order, missing rate limit, secrets in config (ASVS V13). | **SRE: about 70% of outages come from changes to a live system** (S18); launch checklist (S18); ASVS V13 (S15); CodeRabbit "stability and availability" (V2) | No stat found. | **T**: config schema validation, dry-run, `terraform plan` [fm]. Otherwise R. |
| 19 | **Dependencies / supply chain / licensing** | New or updated deps exist, are needed, free of known vulnerabilities, license-compatible and pinned. | Hallucinated or typosquatted package, vulnerable version, unnecessary new dependency, license conflict, lockfile drift. | OWASP A9 (S16); ASVS V15 (S15); **S28 (5.2–21.7% of LLM-suggested packages do not exist)** | No review stat found. | **T**: registry existence check, osv-scanner, govulncheck, cargo-deny, pip-audit, npm audit [fm] |
| 20 | **Accessibility & i18n (UI only)** | Interaction capability: inclusivity, user assistance, self-descriptiveness (ISO). | Contrast, alt text, form labels, empty buttons/links, `lang` attribute, keyboard focus, hard-coded strings, locale formatting. | ISO interaction capability (S14); **S30 (94.8% of pages fail; 6 types make up 96% of errors)**; MS playbook "UI changes" (S19); Qodo UX vs Figma (V3) | — | **T**: axe / pa11y / Lighthouse [fm] on a rendered fixture. i18n: grep for literals, R. |
| 21 | **Portability / flexibility** | Adaptability, installability, scalability (ISO). Builds and runs on the supported OS, arch and runtime versions. | Platform-specific paths or syscalls, minimum supported versions (MSRV, Go, Python, TS target), conditional compilation, endianness. | ISO flexibility (S14); c-CRAB compatibility "version, software or hardware" (S8); RevMate's "Functional – Conditional Compilation" category (S11) | — | **T/X**: CI matrix or cross-compile build. |

### 2d. Extra axes the evidence supports

| # | Axis | Why it is in | Verify |
|---|---|---|---|
| 22 | **Change hygiene / reviewability** | SmartBear: effectiveness falls above 400 LOC (S20). SWR: recall drops from 38% to 8.9% as issues per PR rise (S7). CRBugBench: worse on large, heterogeneous PRs (S9). MS playbook: unrelated changes (S19). | T: diff stats. This is a gating step, not a finding. |
| 23 | **Risk-history weighting** | Historically defective files get *less* scrutiny and later have defects (S6). Lax participation links to post-release defects (S5). | T: `git log` churn and bug-fix history to set review depth per file. |
| — | **Safety (ISO 2023)** | Fail-safe, hazard warning, operational constraints (S14). | Fold into axis 3 unless the domain is safety-critical. |

---

## 3. Separate subagents vs merged

### Evidence on splitting

| Finding | Source | Implication |
|---|---|---|
| Model accuracy falls with input length, and distractors make it worse | S32 | Narrow context per agent. Feed module slices, not the whole repo. |
| Recall drops sharply as issues per PR grow; precision holds | S7 | Each agent should hunt a *small set* of defect types. |
| 48% of false positives come from lack of surrounding context; 13% from domain or convention blindness | S7 | Narrow focus must still **read callers and repo precedent**. Splitting by file without that context causes false positives. |
| Multi-agent CR-Agent scored F1 9.22% vs 18.73% for single-pass PR-Review ("error propagation") | S7 | Too many agents and hand-offs make results worse. |
| Multi-agent +4.7% at 5.55× cost; exploration-nudge prompt +5.8% at 1.10× | S9 | Prefer a strong prompt per agent over more agents. |
| Multi-agent uses about 15× the tokens of chat | S33 | Budget the agent count. |
| Majority voting over shuffled passes plus a validator cut false positives; self-aggregation of n=5 cheap runs beat one expensive run | V1, S7 | Use **redundancy within an axis** (k passes, then vote), not more axes. |
| Functional vs evolvability: different precision, subjectivity and resolution | S7, S8, S10, S11 | Separate the evolvability agent and its report section. |
| Code-review findings may tolerate at most 10% effective false positives | S27 | Each agent needs an evidence gate. |
| Concurrency detectors miss most bugs; the needed reasoning is specialized | S22, S23 | Concurrency gets its own focused agent, triggered only when relevant. |
| Security needs its own knowledge base (CWE/ASVS) and tools | S15, S17 | Separate agent. |

### Recommended grouping

The rule: group axes that share **the same verification harness and the same context**. Split axes whose knowledge base or false-positive profile differs.

| Agent | Axes merged | Trigger | Why merged / why separate |
|---|---|---|---|
| **A0 Intent & scope (orchestrator pre-pass)** | 11 spec conformance, 22 hygiene, 23 risk weighting | Always | Bacchelli: understanding comes first (S3). It produces the module split and per-module "claims to verify". It must **not trust** the PR description (S9). |
| **A1 Correctness** | 1 logic, 2 edge cases, 12 test adequacy (the "does a test catch it" half) | Always, per module | Same harness: write a failing test. Highest AI recall (S7, S8). |
| **A2 Failure paths** | 3 error handling/resilience, 5 resource mgmt, 17 observability-on-error | Always | Same question ("what happens when X fails?") and the same fault-injection harness. S21 and S13 show both are under-reviewed by humans. |
| **A3 Security & privacy** | 6, 7, plus 19 dependency vulnerabilities | Diff touches a trust boundary, I/O, auth, serialization, deps, or logging | Distinct canon (CWE/ASVS) and tools. Authz is #4 in CWE 2025 and needs context. |
| **A4 Concurrency** | 4 | Diff touches threads, async, channels, locks, atomics, `unsafe` | Specialized reasoning. Detectors are weak (S22). Skipping it when not triggered saves tokens. |
| **A5 Contracts & data** | 9 API/compat, 10 migrations, 21 portability, 19 dependency existence and licensing | Diff touches a public surface, schema, migrations, manifests or CI matrix | Mostly **tool-verifiable**, so cheap and precise. Shares "consumers outside the diff" context (S24, V3, V4). |
| **A6 Evolvability (per language)** | 13 maintainability, 14 idiom, 15 design, 16 docs | Always, but low priority | Subjective and low benchmark F1 (S7, S8). Must be grounded in repo conventions plus the existing language-canon research. Separate report section, as SWR recommends (S7). |
| **A7 Performance** | 8 | Hot path, DB, loops over unbounded input, or a perf-labelled PR | Needs a benchmark harness. Low frequency, so conditional. |
| **A8 Ops/config** | 18 (+17 non-error observability) | Config, infra, flags or deploy files changed | Different files and context (SRE S18). |
| **A9 UI a11y/i18n** | 20 | UI files changed (TSX/HTML/CSS) | Tool-driven on a rendered fixture (S30). Only relevant for TypeScript UI. |
| **V Validator** | none (cross-cutting) | Every candidate finding | Reproduce or drop (V1 validator, S8 test oracle, S27 FP budget). |

That makes **6 always-on agents** (A0, A1, A2, A3 when its trigger is cheap, A6, V) and **4 conditional ones**. More splitting is not supported by the evidence (S7 CR-Agent, S9 cost).

---

## 4. Ordering / priority

Severity of escaped defects, multiplied by AI detectability, multiplied by verification cost.

| Rank | Axis group | Reason for rank |
|---|---|---|
| 1 | A0 Intent/spec + risk map | Everything depends on understanding (S3). Sets per-file depth (S6). |
| 2 | A1 Correctness/edge cases | Highest AI recall and executable proof (S7, S8, S9). |
| 3 | A3 Security/privacy | Highest impact (S17). LLM code fails 45% of security tests (S29). Humans fix only 39–41% of raised concerns (S13). |
| 4 | A2 Error handling/resources | 92% of catastrophic failures (S21). Humans under-review it (S3, S13). |
| 5 | A5 Contracts/data/migrations/deps | Breaks other people's code or data. Irreversible (S24, S25). Tools are cheap. |
| 6 | A4 Concurrency (if triggered) | Severe but rare. Proving it is expensive. |
| 7 | Tests adequacy (inside A1) | Gives evidence for everything else (S12). |
| 8 | A8 Ops/config/observability | About 70% of outages come from changes (S18), but much of this is out of diff scope. |
| 9 | A7 Performance | Conditional. Needs a benchmark. |
| 10 | A6 Design | Valuable but subjective. Low resolution (28.6%, S10). |
| 11 | A6 Maintainability/idiom/docs | 75% of human comments, but low benchmark precision. Report as non-blocking. |
| 12 | A9 a11y/i18n, portability | Conditional. Tool-driven. |

---

## 5. Design implications

1. **Gate every finding on ground truth, and tie its severity to the proof.** Findings proven by execution can block. Tool findings can block if the rule is cited. Reasoning-only findings go to advisory or are dropped. Evidence: c-CRAB's test-as-oracle idea (S8). Google's ≤10% effective-FP budget for review checks (S27). Agents execute code in only about 10% of turns, so they must be forced to (S9).
2. **Split the report into functional and evolvability sections** with different bars. Functional detection is much higher (Logic F1 26.2 vs at most 16.45) (S7). Design comments are the least resolved (28.6%) (S10). SWR explicitly recommends separate reports (S7).
3. **Use redundancy within an axis, not more axes.** Run k=3–5 shuffled-order passes per high-value agent (A1, A2, A3), keep findings with ≥2 votes, then validate. Evidence: Bugbot's 8-pass majority vote plus validator (V1). SWR self-aggregation n=5 beats one big-model pass (S7). The multi-agent split costs 5.55× for +4.7% (S9).
4. **Keep the agent count around 6 always-on plus conditional triggers.** Many-agent pipelines lose to a well-prompted single pass (CR-Agent 9.22% vs 18.73%) (S7). Tokens cost 15× (S33).
5. **Shard large codebases by module, but give each shard its callers and repo precedent.** Recall drops with issues per PR (S7). Context rot (S32). But 48% of false positives come from missing context and 13% from convention blindness (S7). Proprietary repos lose 25.5% from missing project context (S9). A shard = changed module + its callers + similar code elsewhere (V4).
6. **Run A0 first and make it adversarial to the PR description.** Turn every claim in the PR, issue or commit into a check to verify. Agents trust misleading descriptions (S9). Understanding is the reviewer's top challenge (S3). Requirement gaps are a vendor category of their own (V3).
7. **Make error handling a first-class always-on agent, separate from logic.** 92% of catastrophic failures (S21). Only 3 of 78 human defect comments cover it (S3). Fault-injection tests give cheap proof.
8. **Use deterministic tools before LLM reasoning in A5.** Semver/API checkers, migration up/down on a fixture DB, registry existence and vulnerability scans. One third of releases break compatibility (S24). 84.2% of DB bugs are SQL, schema or API (S25). 5.2–21.7% of LLM-suggested packages are hallucinated (S28).
9. **For concurrency, never accept "the detector found nothing" as clean.** Require a stress test or an explicit interleaving argument tied to code lines. Go's deadlock detector caught 2 of 21 bugs and the race detector about half (S22). All Rust blocking bugs were in safe code (S23).
10. **Ground idiom and maintainability findings in canon plus repo precedent.** Each finding must cite (a) the canon rule from the existing research and (b) ≥1 matching in-repo example, or a linter rule ID. Language-feature F1 is 7.85 (S7). 16% of false positives are convention or anti-best-practice misjudgments (S7). c-CRAB maintainability pass is 7.9–27% (S8).
11. **Scale depth by file risk history and PR size.** Use git churn and bug-fix history to pick k (number of passes) and whether conditional agents run. Risky files get lax review and later have defects (S6). Low participation leads to more defects (S5). Recall falls on large PRs (S7, S9). SmartBear caps at 200–400 LOC per pass (S20).
12. **Make the triage schema multi-axis, not one severity ladder.** Fields: category (the 23 axes), type (defect / refactor / nit), severity, effort/reward, and evidence kind (X/T/R). CodeRabbit's four independent label axes show the field shape (V2). Effort/reward explains why refactor comments get accepted more than functional ones (18% vs 5%) (S11).
13. **Expect tools to over-generate robustness and testing findings, and filter hard.** c-CRAB shows tools raise these more than humans, a false-positive burden (S8). Require a reachable input (axis 2) or a revert-and-fail test (axis 12) before reporting.
14. **Prompt agents to explore, then filter in a validator.** Bugbot's agentic version needed aggressive prompts (V1). Exploration nudges were the best value per cost (+5.8% at 1.10×) (S9). Precision then comes from the validator gate (item 1), not from a timid hunting prompt.

---

## Gaps

- **SEI CERT** coding standards: not opened. Python, Go and TS have no CERT standard `[from memory]`, so their value here is limited. Not used.
- **Rigby & Bird 2013**: cited only through Sadowski's convergent-practices table (S4). The original paper was not opened.
- **Bosu et al. 2015 (Microsoft useful comments)** and **Turzo & Bosu 2024 (OpenDev)**: search snippets only. Usefulness-by-category numbers not extracted.
- **CodeReviewer (Li 2022)**: known only through SWR's F1 6.13% for fine-tuned hunk-level models.
- **ISO 25010:2023 sub-characteristics**: taken from secondary summaries (arc42, TNLab). The ISO text is paywalled.
- **Google CACM static-analysis paper**: the ≤10% figure came from the Google-hosted PDF. The CACM HTML was blocked (403).
- **No found per-axis detection stats** for privacy, migrations (review side), observability, ops/config, i18n, portability or licensing. Their rows rely on standards and incident studies, not review-comment frequencies.
- **No study found on AI reviewers for concurrency specifically.**
- **Tool names marked `[fm]`** (errcheck, clippy lints, cargo-semver-checks, buf, oasdiff, squawk, osv-scanner, axe, goleak, miri, etc.): their docs were not opened. Check flags and coverage before relying on them.
- **CRBugBench bug-category breakdown** (S9 figure 4): not extractable as text.
- **Vendor docs (V2–V5)** are as read on 2026-11-21 and change often. The Bugbot pipeline describes v1 (July 2025); the current agentic version's internals are not published.

### Critical Files for Implementation
None exist yet in the repo. These are the skill files this plan implies:
- `skills/review-orchestrator/SKILL.md`: A0 intent/risk pre-pass, module sharding with caller context, trigger rules, and the vote-and-validate loop.
- `skills/review-correctness/SKILL.md`: A1 + A2 harness (failing-test, fault-injection and revert-and-fail rules).
- `skills/review-security/SKILL.md`: A3 CWE-2025/ASVS-5.0 checklists and proof-of-concept rules.
- `skills/review-contracts-data/SKILL.md`: A5 tool-first checks (semver, migrations, dependency existence and vulnerabilities).
- `skills/review-findings-schema.md`: shared finding schema (axis, type, severity, effort, evidence X/T/R) and the severity-by-evidence gate.

Skipped: the OWASP CRG v2 text beyond its table of contents, and the full c-CRAB/SWR per-tool tables. Risk: vendor and benchmark numbers move fast, and the CRBugBench figures are from a single Oct 2026 preprint.