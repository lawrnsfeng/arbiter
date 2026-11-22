# Security review method

Source: `research/research-security.md` §2, §3a, §5b and "Design implications" items 1, 8, 9, 10, 13, copied verbatim. Source ids (S4…S50) refer to that file's §1 table. S35 is the Anthropic `claude-code-security-review` prompt (exclusions and precedents); S36 is the triage rubric; S39 is the Trail of Bits FP checklist and gates.

**DoS/ReDoS rule for arbiter:** report denial of service, ReDoS or resource exhaustion only when the threat model lists DoS in scope (its `DoS policy` heading). With no threat model, they are out of scope.

## 2. Security review method

The steps merge S7 (threat model), S14 (SDL #3), S35 and S36 (LLM loop), S38 (taskflows) and S39 (gates).

| Step | Action | Output artifact | Evidence |
|---|---|---|---|
| 0. Scope | Diff mode: review only security impact that the change *adds* (S35 "newly added by this PR"). Full mode: partition by **entry point and trust boundary**, not by directory | Partition list | S35; S36 "partition the search space… by attack surface, endpoint, or component" |
| 1. Threat model | Answer the four questions and draw a DFD with trust boundaries. Write down **what is trusted** (env vars, CLI flags, config, authenticated admins, internal queues) and which classes are out of scope (for example DoS for a CLI) | `THREAT_MODEL.md` in repo | S7; S36: model findings were exploitable "90 percent of the time" with a defined threat model. One team's 40% FP rate came from threat-model mismatch |
| 2. Deterministic tools first | Run the language SAST (bandit / gosec / clippy+semgrep / eslint-plugin-security+semgrep), then SCA with reachability (govulncheck, cargo audit/deny, npm/pip audit) | SARIF plus tool logs | S15, S19, S21, S24, S27; S44 and S47: SAST trace plus LLM beats either alone |
| 3. Trace | For each candidate, walk source → transforms → sanitizer → sink. Cite file:line for each hop. Mark the trust boundary crossed | Trace block | S36 triage rubric; S38 requires file:line; S39 checklist items 1, 3, 4 |
| 4. Discovery agent (recall) | Short, goal-oriented prompt: why we scan, what a finding that matters looks like, an optional CWE-class focus. Parallel agents run per partition | Structured candidates | S36: "more prescriptive prompts make discovery worse"; S47: CWE-specific helps in adjudication |
| 5. Verifier agent (precision) | Fresh context, separate from the finder. Gets only the finding plus the repo, and is told to **disprove** it. Applies the FP checklist and 6 gates (reachability, real impact, PoC, math bounds, environment) | TRUE/FALSE POSITIVE with gate log | S36: an adversarial verifier roughly halved non-exploitable findings; S39 gates |
| 6. Proof | Build a PoC, failing test, or tool rule hit in a sandbox pinned to production dependency versions. A failed PoC does **not** prove a false positive; label the finding "unproven" | Test file, PoC script or semgrep rule | S36: verifier plus PoC brought FP to "near zero"; a mismatched dependency version once produced a fake finding |
| 7. Severity | Answer six questions *before* rating: reachability, attacker control, preconditions, authentication, read vs write, blast radius. Unauthenticated, zero-precondition remote access is critical/high. One or two preconditions or an authenticated path is medium. Three or more, or local-only, is low | Rated finding | S36 rubric (prevents "SQLi so critical" anchoring) |
| 8. Dedup and variants | Group by root cause (same root cause, one missing global auth check reported per endpoint, cause and consequence in one path). After a confirmed finding, search the same pattern and the same class | Deduped list | S36 |
| 9. Fix | Write a failing test first. Fix the root cause minimally. Re-run the PoC, run the full suite, then re-attack with a fresh agent | Test plus patch | S36 patch ladder |

**STRIDE prompts per trust boundary** (S7): Spoofing→authn, Tampering→integrity, Repudiation→logging, Information disclosure→confidentiality, DoS→availability, Elevation→authz.

**Default exclusions and precedents.** Adopt S35's list as defaults, with these overrides:
- S35 excludes DoS, ReDoS and resource exhaustion. Trail of Bits treats panics and `with_capacity(user)` as DoS findings (S24). OWASP API4 (S4) also ranks resource consumption. **Resolution:** gate DoS on the threat model. Report it only for long-running, internet-facing services where an unauthenticated input reaches the panic or allocation.
- S35 treats env vars and CLI flags as trusted, UUIDs as unguessable, and test files and docs as out of scope. React and Angular escape by default unless code uses `dangerouslySetInnerHTML` or `bypassSecurityTrust*`. Missing client-side authz checks are not a vulnerability. SSRF counts only if the attacker controls the host or protocol. Logging URLs is safe; logging secrets or PII is not.

---

## 3. Per-language security checklists

Legend for the verification column: **T** = tool rule ID, **P** = PoC or failing test to build.

### 3a. Cross-language (the top-ranked classes)

| Vuln class | Flag | Don't flag | Verify | CWE |
|---|---|---|---|---|
| Object-level authz (IDOR/BOLA) | Handler loads or mutates a record by a client-supplied ID with no owner, tenant or role check | A global policy, middleware or router dependency enforces ownership; IDs scoped by the session query (`WHERE owner_id = session.user`) | **P:** two-user integration test where user B requests A's object and the test expects 403/404 | 639, 862, 863 |
| Missing authn on a critical function | New route or RPC not covered by the auth middleware or router dependency | Health checks or routes the threat model marks public | **P:** unauthenticated request test | 306 |
| Mass assignment / property authz | `Model(**request.json)`, `Object.assign(entity, body)`, binding into a struct that has `is_admin`/`role` | Separate input schema without server-owned fields (S11) | **P:** POST with `"is_admin":true`, then assert it is unchanged | 915 |
| LLM output to sink (LLM05) | Model text reaches `eval`/`exec`/shell/SQL/`innerHTML`/file path/URL fetch | Output parsed into a strict schema and allowlisted actions | **P:** fixture prompt that makes the model emit a payload, then assert the sink is not reached; treat model output as a taint source (S6) | 94, 78, 89, 79 |
| Prompt injection with agency (LLM01/06) | Untrusted content (web, email, RAG docs, issues) enters the context of an agent that holds tools, secrets or write scopes | User text in a prompt with no tools or secrets: S35 exclusion 14 says this alone is "not a vulnerability" | **P:** injected-instruction document, then assert no tool call or exfiltration | 1427 `[from memory]` |
| Secrets | Hard-coded credential, or a secret in logs, errors or serialized structs | Test fixtures; placeholder values; URLs in logs (S35 precedent 1) | **T:** B105–B107, G101, G117; **P:** grep the log output in a test | 798, 532 |

### 5b. What raises precision (and what it costs)

| Lever | Effect | Source |
|---|---|---|
| SAST plus LLM (neuro-symbolic) | 55 vs 27 of 120 CVEs found; FDR down 5 points | S44 |
| Precise slice plus related-file context | Juliet F1 above 99%; D2A 86% | S45 |
| Flow trace plus CWE-specific guidance | F1 0.912 and 0.955; CWE-specific prompts beat generic | S47 |
| Hybrid path-feasibility in industry | Removes 94–98% of FPs; recall stays 65–88% `[secondary]` | S48, S50 |
| Chain-of-thought, self-consistency, multi-LLM ensemble | 62.5% of FPs removed with zero TPs lost; 78.9% for an ensemble. Real-world gains are smaller (34–38%) | S46 |
| Agentic verifier (tools, repo access) | Benchmark FP rate from over 92% to 6.3%; post-cutoff 95.5% FP identification at 95.5% precision vs 36.4% vanilla. Gains depend on model and CWE, and can suppress TPs | S49 |
| Small tasks, file:line evidence, deterministic checks in tools, dismissal-reason memory | About 30 real vulns found; fewer hallucinations | S38 |
| Defined threat model | Findings exploitable "90 percent of the time"; one team's 40% FP rate traced to threat-model mismatch | S36 |
| Independent adversarial verifier | About half the non-exploitable findings removed | S36 |
| Verifier must build a working PoC | FP "near zero"; another team reports true positives "nearly 100 percent" with live-request tools | S36 |
| Separate discovery from verification | Agents that did both self-censored true positives | S36 |
| Frontier model plus full pipeline, expert-checked | 85 of 97 (88%) crit/high met the CVD bar; 1 invalid; wolfSSL had 72 of 74 valid | S37 |
| Explicit confidence floor plus exclusion list plus parallel FP filter | Production prompt keeps confidence ≥ 8 of 10 and "better to miss some theoretical issues" | S35 |

**Verification artifacts, in order of strength:**
1. Running PoC or exploit in a pinned sandbox.
2. Failing unit or integration test.
3. Taint path from a SAST tool (CodeQL, semgrep, gosec G7xx) plus a manual trace with file:line.
4. Tool rule hit alone. This is **not** sufficient, given the high SAST FP rates in S42, S48 and S27.

The base claim is from S36 ("the PoC is the validation") and the S39 gates. The ladder ordering is my synthesis.


## Design implications (selected)

1. **Make `THREAT_MODEL.md` a hard input to every security subagent.** It lists the trust list, entry points, and in-scope and out-of-scope classes, with DoS gated per service. Evidence: 90% exploitable with a threat model versus a 40% FP rate from mismatch (S36). The trusted-env/CLI precedent comes from S35. The first brocard, "no vulnerability without a threat model", comes from S39.
8. **Embed the ToB 13-item FP checklist and 6 gates (reachability, impact, PoC, math bounds, environment) in the verifier prompt verbatim.** Embed S35's exclusions and precedents as defaults, with an explicit override that DoS and ReDoS are in scope only when the threat model says so. Evidence: S39, S35, and the S24 vs S35 conflict.
9. **Score severity with the six-question rubric before assigning a label.** The questions are reachability, attacker control, preconditions, authentication, read/write, and blast radius. Evidence: severity inflation by anchoring on the bug class (S36).
10. **Keep a never-auto-dismiss list** for injection, authn/authz bypass, deserialization and SSRF. Measure the verifier's recall per CWE on a labelled set: at least 100 confirmed real bugs, with a Wilson CI. Evidence: every FP-reduction method loses true positives (S48, S49, S50).
13. **In any code that calls an LLM, treat model output as a taint source,** the same as request input. Flag prompt injection only when the agent has tools, secrets or write scope. Evidence: S6 (LLM05); S35 exclusion 14.
