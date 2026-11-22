# Security as a code-review axis (Python, Go, Rust, TypeScript): research brief, 2026-11-21

Every factual claim cites a URL I opened. Claims I did not verify carry `[from memory]`. Claims taken from a secondary summary carry `[secondary]`. Vendor facts carry their publication date.

---

## 1. Source table

| # | Source (date) | What it gives the skill design | URL |
|---|---|---|---|
| S1 | OWASP Top 10:2025 | A01 Broken Access Control, A03 Software Supply Chain Failures (new), A05 Injection, A10 Mishandling of Exceptional Conditions (new) | https://owasp.org/Top10/2025/ |
| S2 | CWE Top 25 2025 (page updated 2025-12-15) | Ranks: 79 XSS #1, 89 SQLi #2, 352 CSRF #3, 862 Missing Authz #4 (up 5), 22 path traversal #6, 78 OS cmd #9, 94 code injection #10, 502 deserialization #15, 863 #17, 306 #20, 918 SSRF #22, 639 IDOR #24, 770 #25 | https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html |
| S3 | OWASP ASVS 5.0.0 (May 2025) | Citable requirement IDs in the form `v5.0.0-1.2.5` (OS command injection) | https://github.com/OWASP/ASVS |
| S4 | OWASP API Security Top 10 2023 | BOLA, BOPLA (mass assignment plus excessive exposure), BFLA, SSRF, unsafe consumption of APIs | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ |
| S5 | OWASP LLM Top 10 2025 | LLM01 prompt injection, LLM05 improper output handling, LLM06 excessive agency | https://genai.owasp.org/llm-top-10/ |
| S6 | LLM05 page (modified 2025-05-05) | Model output into shell/eval/SQL/HTML/file path. Treat the model as an untrusted user | https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/ |
| S7 | OWASP Threat Modeling Cheat Sheet | Four questions, DFD with trust boundaries, STRIDE table | https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html |
| S8 | OWASP SSRF Cheat Sheet | Allowlist the host and build the request yourself. Reject URLs that parsers read differently. Validate the resolved IP and connect to that IP (DNS rebinding). Disable redirects | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html |
| S9 | OWASP Prototype Pollution Cheat Sheet | `Map`/`Set`, `Object.create(null)`, `--disable-proto=delete` | https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html |
| S10 | OWASP Node.js Cheat Sheet | Express query parsing yields arrays/objects. Body limits, event-loop blocking, `trust proxy` pitfall, csurf deprecated | https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html |
| S11 | OWASP FastAPI Cheat Sheet | `OAuth2PasswordBearer` does not validate tokens. Router-level `Depends`, `extra="forbid"`, `response_model`, explicit JWT `algorithms`/`aud`/`iss` | https://cheatsheetseries.owasp.org/cheatsheets/FastAPI_Security_Cheat_Sheet.html |
| S12 | RFC 8725 JWT BCP | Use allowed algorithms only (§3.2). Validate `aud` (§3.9) | https://www.rfc-editor.org/rfc/rfc8725.html |
| S13 | OWASP Code Review Guide | Lab project. Page lists no current version, so I did not use it for content | https://owasp.org/www-project-code-review-guide/ |
| S14 | Microsoft SDL practices | 10 practices; #3 is design review plus threat modeling, #5 is supply chain | https://www.microsoft.com/en-us/securityengineering/sdl/practices |
| S15 | Bandit plugin list and blacklist calls | B1xx–B7xx IDs, including B113 request without timeout, B202 tarfile, B614 torch.load, B615 HF download, B301 pickle, B307 eval | https://bandit.readthedocs.io/en/latest/plugins/index.html ; https://bandit.readthedocs.io/en/latest/blacklists/blacklist_calls.html |
| S16 | Semgrep rules `python/lang/security` | Rule files: `dangerous-subprocess-use`, `dangerous-system-call`, `use-defused-xml`, `unverified-ssl-context`, `deserialization/` | https://github.com/semgrep/semgrep-rules/tree/develop/python/lang/security |
| S17 | Python `tarfile` docs (3.15) | 3.12 added extraction filters. 3.14 made `data` the default (before, it was effectively `fully_trusted`) | https://docs.python.org/3/library/tarfile.html |
| S18 | requests advanced docs | "By default, requests do not time out unless a timeout value is set explicitly" | https://requests.readthedocs.io/en/latest/user/advanced/#timeouts |
| S19 | gosec RULES.md | G101–G125, G2xx, G3xx, G4xx, G5xx, G6xx, plus taint rules G701–G710 (SQL, cmd, path, SSRF, XSS, log, SMTP, SSTI via `text/template`, deserialization, open redirect) | https://raw.githubusercontent.com/securego/gosec/master/RULES.md |
| S20 | Go blog "Traversal-resistant file APIs" (2025-03-12) | `filepath.IsLocal` (1.20), `Localize` (1.23), `os.Root`/`OpenInRoot` (1.24). Does not stop bind mounts. TOCTOU-prone on GOOS=js | https://go.dev/blog/osroot |
| S21 | Go vuln management and govulncheck tutorial | Reports only vulnerable symbols that your code transitively calls. Other matches are "Informational" | https://go.dev/doc/security/vuln/ ; https://go.dev/doc/tutorial/govulncheck |
| S22 | Go modules reference | Checksum database authenticates modules. `GOPRIVATE`/`GONOSUMDB` turn it off for listed prefixes | https://go.dev/ref/mod |
| S23 | Rust Reference: overflow, behavior not considered unsafe | Overflow panics only with debug assertions. Other builds may wrap silently (two's complement) | https://doc.rust-lang.org/reference/behavior-not-considered-unsafe.html |
| S24 | Trail of Bits Testing Handbook: Rust footguns, static analysis, supply chain | Panic sources, `debug_assert!` misuse, `PathBuf::join` with absolute paths, `with_capacity(user)`, unsafe checklist. Favourite clippy lints. cargo audit/deny/vet/cackle | https://appsec.guide/docs/languages/rust/gotchas-and-footguns/ ; …/static-analysis/ ; …/supply-chain-analysis/ |
| S25 | Cargo build scripts | Build scripts run on the host machine | https://doc.rust-lang.org/cargo/reference/build-scripts.html |
| S26 | cargo-deny checks | advisories, bans, licenses, sources | https://embarkstudios.github.io/cargo-deny/checks/index.html |
| S27 | eslint-plugin-security | 15 rules. README: "finds a lot of false positives which need triage by a human" | https://github.com/eslint-community/eslint-plugin-security |
| S28 | GitHub "Our plan for a more secure npm supply chain" (2025-09-22) | Shai-Hulud found 2025-09-14: self-replicating, injected postinstall scripts, 500+ packages removed. Roadmap: trusted publishing, 2FA, short-lived tokens | https://github.blog/security/supply-chain-security/our-plan-for-a-more-secure-npm-supply-chain/ |
| S29 | GitHub "Preparing for the next malware campaign" (2025-12-23) | Shai-Hulud 2.0 targets CI and self-hosted runners and is destructive. Blind spots: source vs published artifact, lifecycle scripts | https://github.blog/security/supply-chain-security/strengthening-supply-chain-security-preparing-for-the-next-malware-campaign/ |
| S30 | pnpm supply-chain docs (current) | Dependency build scripts do not run unless listed in `allowBuilds`. `strictDepBuilds` and `blockExoticSubdeps` default on. `minimumReleaseAge` defaults to 1440 minutes. `trustPolicy: no-downgrade` | https://pnpm.io/supply-chain-security |
| S31 | npm config v11 docs | `min-release-age`, `allowScripts` policy plus `strict-allow-scripts`, `ignore-scripts` | https://docs.npmjs.com/cli/v11/using-npm/config |
| S32 | uv settings | `exclude-newer`, `exclude-newer-package` | https://docs.astral.sh/uv/reference/settings/ |
| S33 | OpenSSF Scorecard checks | Binary-Artifacts, Branch-Protection, Code-Review (AI bots do not count), Dangerous-Workflow (`pull_request_target`/`workflow_run` plus untrusted checkout) | https://github.com/ossf/scorecard/blob/main/docs/checks.md |
| S34 | SLSA v1.1 levels | Build L1 provenance exists. L2 signed by a hosted platform. L3 hardened build (v1.2 is current) | https://slsa.dev/spec/v1.1/levels |
| S35 | Anthropic `/security-review` command (repo, 2025) | Above 80% confidence only. 17 hard exclusions, 12 precedents. Parallel FP-filter subtasks. Keeps findings at confidence ≥ 8 of 10. README says the action is not hardened against prompt injection | https://github.com/anthropics/claude-code-security-review ; raw `.claude/commands/security-review.md` |
| S36 | Anthropic "Using LLMs to secure source code" (2026-05-27) | Six-step loop: threat model, sandbox, discovery, independent verification, triage, patch. Field data on FP reduction | https://claude.com/resources/articles/using-llms-to-secure-source-code |
| S37 | Anthropic OSS Scanner launch (2026-10-08) | Experts checked 97 crit/high findings: 85 (88%) met the CVD bar, 11 were duplicates, 1 was invalid. CyberGym went from under 20% to over 85% | https://www.anthropic.com/research/launching-opt-in-vuln-finding-service-for-open-source |
| S38 | GitHub Security Lab Taskflow triage (2026-01-20) | About 30 real vulns from CodeQL alerts. Small tasks with fresh context. file:line evidence required. Deterministic checks moved into MCP tools. Dismissal reasons fed back as memory | https://github.blog/security/ai-supported-vulnerability-triage-with-the-github-security-lab-taskflow-agent/ |
| S39 | Trail of Bits skills: fp-check, vulnerability-triage-brocards (2026) | 13-item false-positive checklist, 6 mandatory gates, 7 triage brocards | https://github.com/trailofbits/skills ; raw `plugins/fp-check/skills/fp-check/references/{false-positive-patterns,gate-reviews}.md` |
| S40 | PrimeVul, Ding et al. (ICSE 2025, arXiv 2403.18624) | 68.26% F1 on BigVul falls to 3.09% on PrimeVul. GPT-3.5/4 score near random in the strictest setting | https://arxiv.org/abs/2403.18624 |
| S41 | SecLLMHolmes, Ullah et al. (S&P 2024, arXiv 2312.12575) | Answers are non-deterministic and reasoning is unfaithful. Renaming functions or variables flips answers in 26% (PaLM2) and 17% (GPT-4) of cases | https://arxiv.org/abs/2312.12575 |
| S42 | CASTLE (arXiv 2503.09433, 2025-03) | 250 micro-programs, 25 CWEs. LLMs do well on small snippets, but accuracy falls and hallucinations rise as code grows. SAST has high FP | https://arxiv.org/abs/2503.09433 |
| S43 | SecVulEval (arXiv 2505.19828, 2025-05) | Statement-level C/C++. Best result, Claude-3.7-Sonnet: 23.83% F1 with correct reasoning | https://arxiv.org/abs/2505.19828 |
| S44 | IRIS (ICLR 2025, arXiv 2405.17238) | LLM-inferred taint specs plus CodeQL find 55 of 120 Java CVEs, against 27 for CodeQL alone. FDR improves 5 points | https://arxiv.org/abs/2405.17238 |
| S45 | LLM4FPM (arXiv 2411.03079) | Precise slice plus related files: Juliet F1 above 99%, D2A label accuracy 86% | https://arxiv.org/abs/2411.03079 |
| S46 | Wagner et al. (arXiv 2506.16899, 2025-06) | OWASP Benchmark: 62.5% of FPs removed with zero TPs lost; an ensemble reaches 78.9%. Real-world project: 33.85%, ensemble 38.46% | https://arxiv.org/abs/2506.16899 |
| S47 | ZeroFalse (arXiv 2510.02534, 2025-10) | SAST trace plus CWE-specific prompt: F1 0.912 (OWASP Java) and 0.955 (OpenVuln). CWE-specific prompts beat generic ones | https://arxiv.org/abs/2510.02534 |
| S48 | Du et al., Tencent (ICSE-SEIP 2026, arXiv 2601.18844) | 433 industrial alarms (328 FP, 105 TP). Hybrid LLM plus static analysis removes 94–98% of FPs. Manual review costs 10–20 min per alarm | https://arxiv.org/abs/2601.18844 |
| S49 | "Sifting the Noise" (arXiv 2601.22952, 2026-01) | Agents cut the OWASP Benchmark FP rate from over 92% to 6.3%. On post-cutoff data, SWE-agent with Sonnet 4 identifies 95.5% of FPs at 95.5% precision, against 36.4% for vanilla prompting. Aggressive filtering suppresses true positives | https://arxiv.org/abs/2601.22952 |
| S50 | Conceptualise blog (2026-11-15) `[secondary]` | Tencent recall stayed at 65–88%. Basic prompting removed only 26–52% of FPs. QASecClaw lost 40 TPs. Base rate is about 70% real on the OWASP Benchmark against 24% in production | https://www.conceptualise.de/en/blog/llm-sast-triage-experiment |

---

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

### 3b. Python

| Vuln class | Flag | Don't flag | Verify | CWE |
|---|---|---|---|---|
| OS command injection | `subprocess.*(…, shell=True)` or `os.system` with tainted string interpolation | List argv with a constant program and `shell=False`. B603 is low-signal | **T:** B602, B605, B604; semgrep `dangerous-subprocess-use`, `dangerous-system-call`; **P:** input `x; touch /tmp/pwn` | 78 |
| SQL injection | f-string, `%` or `+` into `cursor.execute`; Django `.extra()`/`RawSQL` with input | Parameter tuple or dict; ORM filters; identifiers from an allowlist | **T:** B608, B610, B611; **P:** test with `' OR '1'='1` returning extra rows | 89 |
| Unsafe deserialization | `pickle`/`dill`/`shelve`/`jsonpickle`/`pandas.read_pickle`/`marshal` on untrusted bytes; `yaml.load` without SafeLoader; `torch.load`; unpinned HF download | Data written and read by the same trusted process in a private directory (state it in the threat model); `yaml.safe_load` | **T:** B301, B302, B506, B614, B615; **P:** a `__reduce__` payload that runs `os.system` (S15) | 502 |
| Code injection | `eval`/`exec` on input | `ast.literal_eval` | **T:** B307, B102 | 94, 95 |
| SSRF | `requests`/`httpx`/`urlopen` with a user-controlled host or scheme; `urlopen` also allows `file:` | Path-only control under a fixed host (S35 exclusion 13) | **T:** B310; **P:** fixture targeting 127.0.0.1 or 169.254.169.254 plus a redirect; `urlsplit("http://example.com\@evil.com").hostname == "evil.com"` parser mismatch (S8) | 918 |
| Missing HTTP timeout | `requests.*` without `timeout=`, which hangs forever by default (S18) | Batch scripts or CLIs with no availability requirement (threat-model gated) | **T:** B113 | 400 |
| Path traversal / archive slip | `open(os.path.join(base, user))`; `tarfile.extractall` without `filter=` on Python < 3.14; `zipfile` with manual paths | Python ≥ 3.14 default `data` filter (S17); `filter="data"` passed | **T:** B202; **P:** archive containing a `../../x` member or an absolute symlink | 22 |
| XML attacks | stdlib `xml.etree`/`sax`/`minidom` on untrusted XML | `defusedxml` | **T:** B313–B319; semgrep `use-defused-xml` | 611, 776 |
| TLS disabled | `verify=False`; unverified SSL context; paramiko `AutoAddPolicy` | Code that runs only in tests | **T:** B501, B507, semgrep `unverified-ssl-context` | 295 |
| Weak randomness | `random.*` for tokens, OTPs or reset links | Non-security randomness (sampling, jitter) | **T:** B311; fix with `secrets` | 338 |
| Template XSS | `mark_safe`/`Markup` on input; Jinja `autoescape=False` | Constant strings | **T:** B308, B703, B704, B701 | 79 |
| FastAPI authn/authz | `OAuth2PasswordBearer` used as if it validated the token; endpoint missing a router `Depends`; `jwt.decode` without `algorithms=` and `aud`/`iss` | Router-level dependency plus a permission dependency (S11) | **P:** `TestClient` calls with no token, forged token or other user's ID | 287, 347, 862 |
| Debug in production | `app.run(debug=True)`; Django `DEBUG=True` in prod settings | dev-only settings module | **T:** B201 | 489, 94 |

### 3c. Go

| Vuln class | Flag | Don't flag | Verify | CWE |
|---|---|---|---|---|
| SQL injection | `fmt.Sprintf` or `+` into `db.Query`/`Exec` | `?`/`$1` placeholders; table names from a constant allowlist | **T:** G201, G202, G701; **P:** `sqlmock` or SQLite test with a tautology | 89 |
| Command / argument injection | `exec.Command("sh","-c", tainted)`; tainted first argument | Constant program with tainted args when the program does not parse `-flags` from them (otherwise argument injection) | **T:** G204, G702; **P:** arg `--output=/etc/x` or `;id` | 78, 88 |
| Path traversal | `os.Open(filepath.Join(base, untrusted))`; zip/tar extraction | CLIs where the operator chooses the path (S20 "should not use os.Root"); `filepath.IsLocal` check; `os.OpenInRoot`/`os.Root` (Go ≥ 1.24) | **T:** G304, G305, G703; **P:** `../../etc/passwd` and a symlink-then-file archive (S20). Note: `os.Root` does not stop bind mounts and is TOCTOU-prone on GOOS=js | 22, 59 |
| XSS / SSTI | `text/template` producing HTML; `template.HTML(userInput)` | `html/template` with ordinary data (contextual autoescape `[from memory]`) | **T:** G203, G705, G708 | 79, 1336 |
| SSRF | `http.Get(userURL)`; redirect policy forwarding auth headers | Fixed host with a path parameter | **T:** G107, G704, G119 | 918 |
| Weak randomness | `math/rand` for tokens or keys | Non-security use | **T:** G404 | 338 |
| TLS / SSH verification | `InsecureSkipVerify: true`; `ssh.InsecureIgnoreHostKey`; TLS resumption bypassing `VerifyPeerCertificate` | Test-only code | **T:** G402, G106, G123 | 295 |
| Integer conversion | `int64`→`int32`/`int` narrowing of attacker lengths used for bounds or alloc; `strconv.Atoi` result to `int16`/`int32` | Range proven by an earlier check (ToB FP gate 5) | **T:** G115, G109; **P:** table test with `math.MaxInt32+1` | 190, 681 |
| Server DoS knobs | `http.ListenAndServe` without timeouts; no `ReadHeaderTimeout`; `io.Copy` decompress; unbounded `ParseMultipartForm` | Internal-only services, per threat model | **T:** G112, G114, G110, G120 | 400, 409 |
| Secret exposure | Struct with `Password`/`Token` fields JSON-marshaled to clients or logs | Fields tagged `json:"-"` | **T:** G117 | 200 |
| Cookies / CSRF | Missing `Secure`/`HttpOnly`/`SameSite`; `CrossOriginProtection` bypass patterns | — | **T:** G124, G121 | 614, 352 |
| Known-vulnerable deps | **Only** govulncheck's "Your code is affected" section with call stacks | The "Informational" section (vulnerable module imported, symbol not called; S21) | **T:** `govulncheck ./...` | 1395 |
| `unsafe`, pprof exposure | New `unsafe.Pointer` arithmetic; `net/http/pprof` on a public mux | Audited wrappers | **T:** G103, G108 | 119, 200 |

### 3d. Rust

| Vuln class | Flag | Don't flag | Verify | CWE |
|---|---|---|---|---|
| Unsoundness at the safe/unsafe boundary | Safe `fn` whose `unsafe` block relies on caller-supplied invariants; `transmute`/cast `&`→`&mut`; `assume_init` before full init; `static mut`; `repr(packed)` field refs; `mem::zeroed`/`uninitialized` (S24) | `unsafe` with a `// SAFETY:` comment whose invariant is local and type-enforced | **P:** Miri test `cargo +nightly miri test` `[from memory]`; ToB `rust-review` skill (S24) | 119, 416, 787, 908 |
| Panic as DoS | `unwrap`/`expect`, indexing, `&str` slicing, `RefCell::borrow_mut`, `HeaderMap` over 32,768 entries, `Duration::from_secs_f64(neg)` on attacker data in a long-running server (S24) | CLIs, tests, or invariant-proven indices; also S35 excludes DoS by default, so gate on the threat model | **T:** clippy `unwrap_used`, `indexing_slicing` `[from memory]`, `string_slice` (S24); **P:** proptest or fuzz input that panics | 248 `[from memory]`, 129 |
| Integer overflow in release | Arithmetic on lengths, offsets or money from input. Release builds may silently wrap (S23) | `checked_*`/`saturating_*`/`wrapping_*`, `Wrapping<T>`, or `overflow-checks = true` | **T:** clippy `arithmetic_side_effects` (S24); **P:** a test that runs under `--release` and shows the wrap | 190 |
| Validation in `debug_assert!` | `debug_assert!` used as the only guard (removed in release, S24) | `assert!` or explicit `if … return Err` | **P:** release-mode test | 20, 617 |
| Allocation / recursion DoS | `Vec::with_capacity(user_len)`, including via serde `size_hint`; deeply nested structs whose drop overflows the stack (S24) | Capped capacity | **P:** a 10⁹-length header or a 100k-depth JSON fixture | 770, 674 |
| Path traversal | `base.join(user)` where `user` may be absolute, which replaces `base` (S24) | A component check before the join | **P:** `join("/etc/passwd")` unit test | 22 |
| Partial-match comparisons | `starts_with`/`contains`/case-insensitive comparison in authz, host or path checks (S24) | Exact equality on a normalized form | **P:** bypass test such as `admin.evil.com` | 697 |
| FFI | Lifetime of `CString::as_ptr`; ownership/free across the boundary; panics crossing `extern "C"` `[from memory]` | `bindgen` wrappers with a documented contract | **P:** ASan or Miri test `[from memory]` | 762, 416 |
| Test features in prod | Mock or test features in `[dependencies]` or `default` (S24) | `dev-dependencies` | **T:** `cargo tree -e features` | 489 |
| Secret zeroization | Secret built in a growing `Vec`, then wrapped in `Zeroizing` (reallocation copies survive, S24) | Pre-sized buffer zeroized from creation | ToB `zeroize-audit` skill (S39 repo) | 226 |
| Known-vulnerable deps | RUSTSEC advisory in `Cargo.lock` | Advisory scoped to a feature or target that is unused (state why) | **T:** `cargo audit`, `cargo deny check advisories` (S24, S26) | 1395 |

### 3e. TypeScript (browser and Node)

| Vuln class | Flag | Don't flag | Verify | CWE |
|---|---|---|---|---|
| DOM / stored XSS | `innerHTML`/`outerHTML`/`insertAdjacentHTML`/`document.write`; `dangerouslySetInnerHTML`; Angular `bypassSecurityTrust*`; `href={userUrl}` allowing `javascript:` (S38 GHSL true positive) | React or Angular text interpolation (S35 precedent 6); DOMPurify output (S10) | **T:** CodeQL `js/xss` (S38); **P:** Playwright or jsdom test that payload `<img src=x onerror=…>` does not run | 79 |
| Code injection | `eval`, `new Function`, `setTimeout(string)`, `require(variable)` | Literal arguments | **T:** eslint `detect-eval-with-expression`, `detect-non-literal-require` | 94, 95 |
| Prototype pollution | Recursive merge, clone or set-by-path over user JSON or nested `req.query` (S10 shows `?foo[bar]=baz` becomes an object) | `Map`/`Set`, `Object.create(null)`, schema-validated keys (S9). S35 says report only if extremely high confidence, so a gadget PoC is required | **P:** `merge({}, JSON.parse('{"__proto__":{"p":1}}'))`, then assert `({}).p === undefined` | 1321 |
| ReDoS | `new RegExp(userInput)`; nested-quantifier pattern on user strings. Node's single thread stalls (S10) | Bounded input length; RE2 `[from memory]`. S35 excludes regex DoS by default, so gate on the threat model | **T:** eslint `detect-unsafe-regex`, `detect-non-literal-regexp`; **P:** timing test with a 30-char evil string | 1333 |
| Command injection | `child_process.exec(\`… ${x}\`)` | `execFile`/`spawn` with an args array and no `shell: true` | **T:** eslint `detect-child-process` | 78 |
| Path traversal | `fs.*(path.join(base, user))` | `path.resolve` plus a `startsWith(base + sep)` check | **T:** eslint `detect-non-literal-fs-filename` (noisy, S27); **P:** `../` request test | 22 |
| SSRF | Server-side `fetch(userUrl)` | Fixed origin. Note: a host allowlist alone fails against DNS rebinding; connect to the validated IP (S8) | **P:** fixture targeting 169.254.169.254 or a redirect | 918 |
| NoSQL operator injection | `req.query.x` or a body value passed into a Mongo filter, where `{ "$ne": null }` is reachable (S10 parse table) | zod or JSON-schema validation to primitive types at the boundary | **P:** `?user[$ne]=x` login bypass test | 943 |
| JWT misuse | `jwt.decode` used as verify; `verify` without an `algorithms` allowlist; missing `aud`/`iss`/`exp` checks (S12, S11) | Library verify call with a pinned algorithm and audience | **P:** forged `alg:none` or HS/RS key-confusion token test | 347 |
| Boundary validation | `req.body` cast `as T` with no runtime check (TS types are erased `[from memory]`) | Internal typed calls; `schema.parse()` at the handler | **P:** malformed-body test | 20 |
| Proxy trust / rate limit | `app.set('trust proxy', true)`, which lets a spoofed `X-Forwarded-For` bypass IP limits (S10) | Hop count or explicit proxy list | **P:** header-spoof test | 348 |
| CSRF | Cookie-auth, state-changing routes without a token; `csurf` (archived) | Bearer-token APIs; framework CSRF on | **P:** cross-origin form POST test | 352 |
| Secret comparison | `===` on HMACs or API keys | `crypto.timingSafeEqual`. The eslint `detect-possible-timing-attacks` rule is noisy; S35 also excludes theoretical timing attacks | **T:** eslint rule (triage only) | 208 |
| Client-side authz | (none) | Missing checks in browser code are not vulnerabilities (S35 precedent 8) | — | — |

---

## 4. Supply-chain review checklist per ecosystem

Attack pattern to design against: Shai-Hulud (Sept 2025 and 2.0) used stolen tokens, injected install scripts, published under existing names with bumped versions, and targeted CI runners (S28, S29). OWASP made supply chain A03:2025 (S1).

| Ecosystem | Review on every lockfile/manifest diff | Policy to check exists | Tool or evidence |
|---|---|---|---|
| **npm / pnpm** | New direct or transitive packages; `resolved` changed to git or tarball URLs; integrity hash changed without a version change `[from memory]`; a dependency that newly gained `preinstall`/`install`/`postinstall`; a version published under 24 h ago | pnpm: `allowBuilds` allowlist, `strictDepBuilds`, `blockExoticSubdeps`, `minimumReleaseAge` (default 1440), `trustPolicy: no-downgrade`, `namedRegistries` (S30). npm: `allowScripts` plus `strict-allow-scripts`, `min-release-age`, `ignore-scripts` in CI (S31). Publishing via trusted publishing, not tokens (S28) | `npm audit`/`pnpm audit` `[from memory]`; provenance or trust-level downgrade (S30); some scanners read only the first document of the two-document `pnpm-lock.yaml` and wrongly report zero dependencies (S30) |
| **PyPI / uv / pip** | New packages; sdists that execute `setup.py` at install `[from memory]`; model files loaded with `torch.load` or HF downloads without a pinned revision (B614, B615) | `uv.lock` committed; `exclude-newer` window (S32); hash-pinned installs `pip --require-hashes` `[from memory]`; trusted publishing (S28) | `pip-audit` `[from memory]`; bandit B614/B615 |
| **Go** | New modules; new `replace` directives `[from memory]`; widened `GOPRIVATE`/`GONOSUMDB`, which disables checksum-database verification (S22); `GOFLAGS=-mod=mod` in CI | `go.sum` committed; `-mod=readonly` (S22) | `govulncheck ./...`: findings are only call-stack-reachable symbols (S21) |
| **Cargo** | New crates; new or changed `build.rs` and proc-macros, which run on the build host (S25); duplicate versions; git or alternate-registry sources | `cargo deny` advisories, bans, sources, licenses (S26); `cargo vet` with imported audits (Google, Bytecode Alliance) (S24); crates.io trusted publishing since July 2025 (S28) | `cargo audit`; `cackle` for unexpected FS/network API use; `cargo-supply-chain` for publisher sprawl (S24) |
| **GitHub Actions / CI** | `pull_request_target` or `workflow_run` plus checkout of PR code (critical, S33); `${{ github.event.* }}` interpolated into `run:`; actions not pinned by SHA; broad `GITHUB_TOKEN` permissions `[from memory: Scorecard Pinned-Dependencies / Token-Permissions]` | Branch protection: 1–2 reviewers, code owners, status checks (S33); SLSA Build L2+ signed provenance (S34); a published artifact matches its source (S29) | Scorecard `Dangerous-Workflow`, `Branch-Protection`, `Binary-Artifacts` (S33); ToB `agentic-actions-auditor`, `supply-chain-risk-auditor` skills (S39 repo) |

**Supply-chain "don't flag" defaults:** outdated-but-not-vulnerable dependencies. S35 exclusion 9 routes known-CVE dependency findings to a separate SCA gate instead of the code reviewer.

---

## 5. Evidence on LLM vulnerability-detection accuracy

### 5a. Raw detection is weak without structure

| Finding | Number | Source |
|---|---|---|
| Benchmark leakage inflates scores | 68.26% F1 on BigVul falls to 3.09% on PrimeVul; GPT-4 near random in the strictest setting | S40 |
| Statement-level localisation (C/C++, real CVEs) | Best result 23.83% F1 with correct reasoning (Claude-3.7-Sonnet) | S43 |
| Small changes flip verdicts | Renaming flips 17% (GPT-4) and 26% (PaLM2); answers are non-deterministic and reasoning unfaithful | S41 |
| Accuracy falls as code grows | LLMs are strong on small snippets; accuracy drops and hallucinations rise with size | S42 |
| Base rate matters | About 70% of OWASP Benchmark alerts are real against 24% in Tencent production | S50 `[secondary]` |

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

---

## Gaps

- I did not open the OWASP Code Review Guide v2 PDF. The project page shows no current release, so none of its content is used.
- The ASVS 5.0 chapter list beyond V1 (encoding/sanitization) and the OWASP Top 10:2025 category details beyond titles are not quoted.
- Scorecard checks after Dangerous-Workflow (Pinned-Dependencies, Token-Permissions) were cut off in my read. I tagged them `[from memory]`.
- The CISA Shai-Hulud alert returned 403. I used GitHub's primary posts instead.
- Semgrep's "96% agreement" claim (2025 blog) appeared only in a search snippet and is not used. The QASecClaw and Tencent recall figures come from a secondary blog (S50).
- Unverified Rust details: Miri, cargo-fuzz, and panic-across-FFI semantics. Clippy `unwrap_used`/`indexing_slicing` names are from memory; `arithmetic_side_effects` and `string_slice` are verified.
- Unverified Python details: the pip `--require-hashes` and pip-audit specifics. Unverified TypeScript details: zod strict-mode defaults, React `javascript:` URL handling, `vm` not being a sandbox.
- Python/Go/TS-specific LLM detection benchmarks: most papers cover C/C++ or Java (S40–S49). No Python/Go/TS-specific LLM precision numbers were found or verified.
- NCC Group methodology and Google's internal security-review checklists: not found as primary sources.
- Some CWE IDs carry `[from memory]` (248 for panics, 1427 for prompt injection).

---

## Design implications

1. **Make `THREAT_MODEL.md` a hard input to every security subagent.** It lists the trust list, entry points, and in-scope and out-of-scope classes, with DoS gated per service. Evidence: 90% exploitable with a threat model versus a 40% FP rate from mismatch (S36). The trusted-env/CLI precedent comes from S35. The first brocard, "no vulnerability without a threat model", comes from S39.
2. **Split agents into discovery (recall) and verification (precision).** The verifier gets a fresh context, only the finding plus the repo, and the instruction to disprove. Evidence: the S36 self-censorship lesson, and the adversarial verifier halving non-exploitable findings (S36, S49).
3. **Gate blocking findings on proof.** A blocking finding needs a running PoC or a failing test in a sandbox pinned to the lockfile. Everything else ships as "unproven" and advisory. Evidence: PoC requirement gives near-zero FP (S36); the S39 PoC gate; the dependency-version mismatch that produced a fake finding (S36).
4. **Run deterministic tools first and let the LLM adjudicate their output with CWE-specific guidance.** Use bandit, gosec G7xx, clippy plus semgrep `p/rust`, eslint-plugin-security, CodeQL. Do not use the LLM as the sole detector. Evidence: S44, S47, S45. Raw LLM detection collapses on realistic data (S40, S43).
5. **Partition large codebases by entry point and trust boundary, one CWE family per subagent, small tasks with fresh context.** Evidence: accuracy falls with code size (S42); taskflow design (S38); partitioned parallel discovery (S36).
6. **Require file:line for every hop of source → sanitizer → sink.** Reject findings that cite lines that do not exist, or that have missing or inconsistent hops. Evidence: S38 report validation; the hallucination check in S50; S39 checklist items 1 and 3.
7. **Push mechanical facts to tools, not prompts.** Examples: workflow triggers, govulncheck reachability, `cargo deny`, lockfile script diffs, npm/pnpm policy settings. Evidence: S38 "Delegate to MCP server whenever possible"; govulncheck's "Informational" tier removes unreachable CVEs (S21).
8. **Embed the ToB 13-item FP checklist and 6 gates (reachability, impact, PoC, math bounds, environment) in the verifier prompt verbatim.** Embed S35's exclusions and precedents as defaults, with an explicit override that DoS and ReDoS are in scope only when the threat model says so. Evidence: S39, S35, and the S24 vs S35 conflict.
9. **Score severity with the six-question rubric before assigning a label.** The questions are reachability, attacker control, preconditions, authentication, read/write, and blast radius. Evidence: severity inflation by anchoring on the bug class (S36).
10. **Keep a never-auto-dismiss list** for injection, authn/authz bypass, deserialization and SSRF. Measure the verifier's recall per CWE on a labelled set: at least 100 confirmed real bugs, with a Wilson CI. Evidence: every FP-reduction method loses true positives (S48, S49, S50).
11. **Run the verifier at least twice, or with two models, and treat disagreement as "unsure", which routes to a human.** Evidence: non-determinism and rename sensitivity (S41); ensemble gains (S46).
12. **Use a dedicated supply-chain reviewer on lockfile and manifest diffs.** It checks new install scripts, release age, exotic sources, `GONOSUMDB` changes, new `build.rs`/proc-macros, and `pull_request_target` checkouts. Evidence: the Shai-Hulud mechanics (S28, S29); pnpm/npm controls (S30, S31); S25 and S33.
13. **In any code that calls an LLM, treat model output as a taint source,** the same as request input. Flag prompt injection only when the agent has tools, secrets or write scope. Evidence: S6 (LLM05); S35 exclusion 14.
14. **Fix with a failing test first, then re-run the PoC, run the full suite, and re-attack with a fresh agent. After confirmation, run variant analysis for the same pattern and the same class.** Evidence: the S36 patch ladder and variant step.
15. **Run the reviewer only on trusted diffs, or sandboxed with no secrets.** Repository content can carry prompt injection aimed at the reviewer itself. Evidence: S35 README "not hardened against prompt injection"; the S36 sandbox and egress guidance.

### Critical Files for Implementation
- `THREAT_MODEL.md` template (per repo): trust list and scope that every agent reads (implications 1, 8).
- Verifier prompt or skill: FP checklist, gates, exclusions and precedents (implications 2, 8, 11).
- Per-language checklist reference files (Python, Go, Rust, TS): the section 3 tables with tool rule IDs (implication 4).
- Supply-chain diff reviewer skill: the section 4 table (implication 12).
- Proof harness spec: sandbox pinned to lockfile, PoC and failing-test conventions (implications 3, 14).

I did not check Python/Go/TS-specific LLM precision data, because none was found, and none of these claims comes from running tools.

The biggest risk is that published false-positive cuts always cost real bugs: Tencent's best methods kept only 65–88% of them. Do not let any configuration auto-dismiss findings until its recall is measured on your own labelled data.