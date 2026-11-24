# Hosted and static code-quality platforms as a rule source for arbiter: research brief, 2026-11-23

Question: should arbiter use Codacy's rule set (all of it, or only its Critical/Security tier), or another platform's, for findings? Is the Codacy approach obsolete?

Evidence rules: every claim cites a source I opened (table in §0). `[from memory]` = recalled, not opened. `[unverified]` = seen only in a search snippet. `[measured]` = I computed it from primary data during this research; the method is stated next to the number.

**Short answer.** Do not adopt any platform's rule set or severity tier. Codacy, Qlty and (partly) DeepSource wrap the same open-source engines arbiter already runs, and their "Critical" label is a mechanical remap of the upstream tool's level, not a precision signal. Sonar, Semgrep Pro, Snyk Code and CodeQL have real proprietary value (cross-file taint), but all of it is cloud-only, paid, or licence-barred for automated use on closed code. Take four narrow things instead (§5): secrets plus SCA scanners, high-confidence semgrep rules for Go, optional cross-file taint through Opengrep, and CodeQL as an opt-in oracle for OSI-licensed repos.

---

## 0. Sources

### Platform sources (opened)

| # | Source (date seen 2026-11-23) | URL |
|---|---|---|
| P1 | Codacy, Supported languages and tools | https://docs.codacy.com/getting-started/supported-languages-and-tools/ |
| P2 | Codacy, Which metrics does Codacy calculate? | https://docs.codacy.com/faq/code-analysis/which-metrics-does-codacy-calculate/ |
| P3 | Codacy, Issues page (severity levels, categories) | https://docs.codacy.com/repositories/issues/ |
| P4 | Codacy, Adjusting quality goals | https://docs.codacy.com/repositories-configure/adjusting-quality-goals/ |
| P5 | Codacy Analysis CLI docs | https://docs.codacy.com/codacy-analysis-cli/ |
| P6 | `codacy/codacy-cli-v2` README (MIT, deprecated) | https://github.com/codacy/codacy-cli-v2 |
| P7 | `codacy/codacy-analysis-cli` (old Scala CLI, AGPL-3.0) | https://github.com/codacy/codacy-analysis-cli |
| P8 | Codacy pricing | https://www.codacy.com/pricing |
| P9 | `codacy/codacy-bandit` README and `docs/patterns.json` | https://github.com/codacy/codacy-bandit ; https://raw.githubusercontent.com/codacy/codacy-bandit/master/docs/patterns.json |
| P10 | `codacy/codacy-semgrep` README, `internal/docgen/parsing.go`, `docs/codacy-rules*.yaml` | https://github.com/codacy/codacy-semgrep |
| P11 | `codacy/codacy-eslint` `docs/patterns.json` | https://raw.githubusercontent.com/codacy/codacy-eslint/master/docs/patterns.json |
| P12 | Codacy Security and risk management | https://docs.codacy.com/security/ |
| P13 | SonarQube Server, Rules overview (precision targets) | https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-rules/rules.md |
| P14 | SonarQube Server, Metrics definition (ratings, debt ratio) | https://docs.sonarsource.com/sonarqube-server/user-guide/code-metrics/metrics-definition.md |
| P15 | SonarQube Cloud, Quality standards and new code | https://docs.sonarsource.com/sonarqube-cloud/standards/about-new-code.md |
| P16 | SonarQube Cloud, Security-related rules (taint) | https://docs.sonarsource.com/sonarqube-cloud/standards/managing-rules/security-related-rules.md |
| P17 | SonarQube Server editions | https://docs.sonarsource.com/sonarqube-server/discovering/sonarqube-server-editions.md |
| P18 | SonarQube Cloud, Rust | https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/languages/rust.md |
| P19 | SonarQube Cloud, AI features (AI CodeFix) | https://docs.sonarsource.com/sonarqube-cloud/managing-your-projects/issues/with-ai-features.md |
| P20 | `SonarSource/sonar-python` LICENSE (SSAL v1.0) | https://github.com/SonarSource/sonar-python |
| P21 | `SonarSource/sonarlint-core` (LGPL-3.0) | https://github.com/SonarSource/sonarlint-core |
| P22 | `qltysh/qlty` README and LICENSE.md (BUSL-1.1) | https://github.com/qltysh/qlty |
| P23 | Qlty, Maintainability metrics and ratings | https://docs.qlty.sh/cloud/maintainability/metrics.md |
| P24 | Qlty, Migration overview (Code Climate Quality to Qlty) | https://docs.qlty.sh/migration/overview.md |
| P25 | Code Climate, Our 10-Point Technical Debt Assessment (legacy) | https://codeclimate.com/legacy/10-point-technical-debt-assessment |
| P26 | DeepSource, How we ensure less than 5% false positive rate (2020-06-05) | https://deepsource.com/blog/how-deepsource-ensures-less-false-positives |
| P27 | DeepSource, Benchmarks (OpenSSF CVE Benchmark) | https://deepsource.com/benchmarks |
| P28 | DeepSource, Product docs | https://deepsource.com/docs/product |
| P29 | DeepSource, Compliance reporting | https://deepsource.com/docs/product/compliance-reporting |
| P30 | `DeepSourceCorp/cli` README (BSD-2) | https://github.com/DeepSourceCorp/cli |
| P31 | Semgrep, Semgrep CE vs AppSec Platform | https://docs.semgrep.dev/semgrep-pro-vs-oss.md |
| P32 | Semgrep Rules License v1.0 | https://semgrep.dev/legal/rules-license |
| P33 | Opengrep README (LGPL-2.1) | https://github.com/opengrep/opengrep |
| P34 | `semgrep/semgrep-rules` (shallow clone, HEAD 2026-11-10) | https://github.com/semgrep/semgrep-rules |
| P35 | Snyk Code docs | https://docs.snyk.io/scan-fix-and-prevent/scan-with-snyk/snyk-code.md |
| P36 | `github/codeql-cli-binaries` README (licence terms) | https://github.com/github/codeql-cli-binaries |
| P37 | GitHub, CodeQL query suites | https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-query-suites |
| P38 | gosec RULES.md | https://raw.githubusercontent.com/securego/gosec/master/RULES.md |
| P39 | Bandit `bandit/plugins/injection_shell.py`, `injection_sql.py` | https://github.com/PyCQA/bandit/tree/main/bandit/plugins |

### False-positive and actionability sources (opened)

| # | Source | URL |
|---|---|---|
| F1 | Sadowski et al., *Lessons from Building Static Analysis Tools at Google*, CACM 61(4) 2018 (PDF) | https://storage.googleapis.com/gweb-research2023-media/pubtools/4365.pdf |
| F2 | Sadowski et al., *Tricorder*, ICSE 2015 (abstract page) | https://research.google/pubs/tricorder-building-a-program-analysis-ecosystem/ |
| F3 | OWASP Benchmark for Python v0.1, `expectedresults-0.1.csv` + `results/BenchmarkPython-Bandit.sarif` (Bandit 1.8.6, committed 2025-11-05) | https://github.com/OWASP-Benchmark/BenchmarkPython |
| F4 | Lenarduzzi et al., *Are SonarQube Rules Inducing Bugs?*, SANER 2020, arXiv:1907.00376 | https://arxiv.org/abs/1907.00376 |
| F5 | Marcilio et al., *Are Static Analysis Violations Really Fixed?*, ICPC 2019 (PDF) | https://dvmarcilio.github.io/papers/icpc2019.pdf |
| F6 | Kang, Aw, Lo, *Detecting False Alarms from ASATs: How Far are We?*, ICSE 2022, arXiv:2202.05982 | https://arxiv.org/abs/2202.05982 |
| F7 | Charoenwet et al., *An Empirical Study of Static Analysis Tools for Secure Code Review*, ISSTA 2024, arXiv:2407.12241 | https://arxiv.org/abs/2407.12241 |
| F8 | Hu, Wang, Rubin, Pradel, *An Empirical Study of Suppressed Static Analysis Warnings*, FSE 2025 (Pylint, ESLint, PMD, Checkstyle) | http://hhyemin.github.io/files/FSE25_suppression_study.pdf |
| F9 | Luke Plant, *Pylint false positives* (2019-07-29), a hand-labelled run on an 11k-line Django app | https://lukeplant.me.uk/blog/posts/pylint-false-positives/ |
| F10 | HN, *Sonar is destroying my job and it's driving me to despair* (2024-07-02, 69 comments) | https://news.ycombinator.com/item?id=40859937 |
| F11 | HN, *Launch HN: DeepSource (YC W20)* | https://news.ycombinator.com/item?id=22547183 |

Total: 50 sources opened, 11 of them on false positives and actionability (F1–F11), plus P13, P26 and P27 for vendor precision claims.

---

## 1. What each platform is today (2026)

### 1.1 Codacy

**Products.** These are Codacy Cloud (hosted PR analysis), the IDE extension "Guardrails", the **Codacy Analysis CLI** and the Codacy Cloud CLI.
- The Analysis CLI is `npm i -g @codacy/analysis-cli` and needs Node 20 or later.
  - It "runs Codacy's analyzers locally", and "Your code never leaves your machine unless you run `upload`".
  - Without an account, `codacy-analysis init --auto` lets the CLI "detect your stack and pick the rules. No token, no account" (P5).
- **Codacy CLI v2** (Go, MIT) "is deprecated and no longer receives new features" (P6).
- The older `codacy-analysis-cli` (Scala, Docker-based) is AGPL-3.0 (P7).
- I did not open the licence of the npm `@codacy/analysis-cli` package `[unverified]`.

**Cost.** Developer plan "Free forever $0" covers "CLI integration … Local Quality and Security Scans (SAST, SCA, Secrets)". Team plan "Starting at $18 Per dev/mth"; "Free forever for open-source projects" (P8).

**Grade A–F.**
- "Grades represent a weighted average of the available code quality metrics (issues, complexity, duplication, and coverage), and range from A to F" (P2).
- **The weights and letter cut-offs are not published.** P2 and P4 describe only the inputs:
  - issues per kLoC;
  - complexity: a file "is considered complex if its cyclomatic complexity value is higher than the threshold **File is complex when over**", where file complexity is "the total sum of the cyclomatic complexities of all methods";
  - duplication: a file is duplicated when its clone count exceeds **File is duplicate when over**;
  - coverage: **Coverage is under** (P4).
- I recall that older Codacy docs gave a formula based on issue density `[from memory]`. The 2026 page does not.

**Severity.** UI levels (P3):
- "**Critical (red):** The most dangerous issues … susceptible to serious problems regarding security and compatibility"
- "**Medium (yellow):** … based on coding standards and conventions"
- "**Minor (blue):** … most code style issues"
- "Each code pattern has a pre-defined severity level and at the moment Codacy doesn't support customizing that information."

Internally, patterns carry `Error`/`Warning`/`Info` (P9, P11). Security findings get their own severity rules on the Security page (P12).

**Categories** (P2, P3):
- Code style, Error prone, Code complexity, Performance, Compatibility, Unused code;
- Security, split into secrets, SCA and SAST;
- Documentation, Best practice, Comprehensibility.

### 1.2 SonarQube Cloud / Server / for IDE

**Editions.**
- SonarQube Server 2026.5 comes as Developer, Enterprise and Data Center, "licensed per instance per year based on Lines of Code" (P17).
- Developer "Adds branch/PR analysis, more languages, and stronger security on top of SonarQube Community Build" (P17).
- SCA and "Advanced SAST" need a separate Advanced Security subscription (P17).

**Licences.**
- The language analyzers are **source-available, not open source**: sonar-python is "SONAR Source-Available License v1.0". It forbids "Competing", meaning "marketing a product or service as a substitute for the functionality or value of SonarQube" (P20).
- The IDE core `sonarlint-core` is LGPL-3.0 (P21). It loads the same SSAL analyzers `[from memory]`.

**Proprietary rules.** Yes, Sonar writes its own rules (S-numbers, for example S3649 and S2077).
- Taint analysis: "Security-injection rules are supported only by SonarQube Cloud and SonarQube Server. SonarQube for IDE pulls the injection vulnerabilities raised by these products" (P16).
- SQL-injection taint (S3649) covers Python, JS/TS and Go. Rust has none ("All other supported languages … such as Swift, Scala, Rust") (P16).
- For Rust, Sonar *imports* Clippy: "The analyzer does not run Clippy for you" (P18).

**Ratings.**
- Security and Reliability are worst-issue grids: "A = 0 or more info issues, B = at least one low issue, C = at least one medium, D = at least one high, E = at least one blocker issue" (P14).
- Maintainability comes from the SQALE debt ratio: `sqale_debt_ratio = technical debt / (cost to develop one line of code * number of lines of code)`. The cost per line is "by default, 30 minutes". The default scale starts "A ≤ 5%" (P14). The page render was cut after B. The 6–10/11–20/21–50/>50% bands are `[from memory]`.
- Severities: "Blocker, High, Medium, Low, or Info" in MQR mode, and "Blocker, Critical, Major, Minor, or Info" in Standard mode (P13).

**Clean as You Code.** "SonarQube Cloud warns you whenever issues are detected in your new code … analyzing and cleaning new code allows you to fix issues in your old code and gradually improve the overall quality" (P15). Arbiter already works this way: it reports only on added lines.

**AI CodeFix.** "AI CodeFix generates a fix suggestion for an individual issue", alongside a "Remediation Agent" and a "Hunter Agent [that] raises complex, logic-level vulnerabilities" (P19). This is cloud-only.

**Security hotspots** "are being phased out. Rules that previously raised hotspots now raise vulnerabilities … or security issues" (P14).

### 1.3 Code Climate Quality → Qlty

- Code Climate Quality was spun out as Qlty Software. "Qlty is the next generation of Code Climate Quality" (P24).
- Old Code Climate maintainability used ten checks (P25): argument count, complex boolean logic, file length, identical blocks, method count, method length, nested control flow, return statements, similar blocks, method complexity.
- **Qlty CLI** "is completely free for all use" (P22). The LICENSE is **BUSL-1.1**, with this Additional Use Grant: "provided that you do not use the Licensed Work for a Code Quality Service or to produce (by integration, ingestion, analysis, training, or otherwise) an **Artificial Intelligence Coding Service**" (P22). Arbiter is plausibly such a service. **Embedding Qlty is a licence risk.**
- The CLI wraps "60+ linter plugins" and "20,000 code quality rules", including gitleaks, semgrep, trivy, trufflehog and osv-scanner. Its own `qlty-smells` engine handles complexity and duplication (P22).
- Maintainability grade (P23):
  - debt = summed remediation minutes of "structure and duplication" issues;
  - debt ratio = debt ÷ basic-COCOMO rewrite effort;
  - project grade: A <5%, B 5–10%, C 10–20%, D 20–50%, F ≥50%;
  - files use "a logorithmic function based on the total Technical Debt".
  - Issue levels are "high, medium, and low".

### 1.4 DeepSource

- Hosted platform: "Static analysis for 18 languages … with AI-powered Autofix™". It offers secrets detection with "97% precision", OSS vulnerability scanning "with reachability analysis", IaC and licence compliance (P28), and OWASP Top 10 compliance reports (P29).
- The CLI (BSD-2) only views cloud results and uploads coverage: "Access DeepSource analysis data directly from your terminal" (P30). **Analysis does not run locally.**
- Rules: a proprietary engine that also wraps open-source tools. "a security issue that DeepSource detects in a Python codebase that comes from the popular security analysis tool Bandit which we use behind the scenes" (P26).
- Precision claims:
  - "keep the rate of false positives to a minimum — less than 5%" (2020 blog). They anchored on Google's 2018 paper (P26).
  - A 2026 self-run benchmark on 165 JS/TS OpenSSF CVE diffs: DeepSource precision 100% and recall 73.17%; **Semgrep CE precision 74.07%, recall 24.39%** (P27). This is vendor-run and vendor-judged.

### 1.5 Semgrep AppSec Platform vs Semgrep CE vs Opengrep

- Semgrep CE does "Single file, cross function constant propagation; Single function taint analysis … It can't track data beyond a single function or file and may find more false positives" (P31).
- Semgrep Code (paid) adds "Cross file, cross function taint analysis" and Pro Rules. It also adds "Semgrep Multimodal (AI-assisted) post-processing" that "Reduces noise by 20%". It is "free for up to 10 contributors" (P31).
- **Rules licence.** The registry rules (`p/python` and the rest, which arbiter already downloads) are under the Semgrep Rules License v1.0: "only for your own internal business purposes. This license does not allow you to distribute the rules, or to make them available to others as a service" (P32). Arbiter runs them on the user's machine for the user, which is internal use. **Arbiter must not ship or host the rule files.**
- **Opengrep** (LGPL-2.1, a fork backed by Aikido, Endor Labs, Orca and others) advertises "Cross-function and cross-file taint tracking … Compatible with Semgrep rules" (P33). Codacy now runs Opengrep instead of Semgrep (P1).

### 1.6 Snyk Code

- The engine is proprietary ("semantic, AI-based analysis engine"; the DeepCode lineage shows in `.dcignore`).
- Default deployments upload code: "Snyk Code bundles these files … and sends them to Snyk". The no-upload option "requires Snyk Code Local Engine", an enterprise deployment that "receives slower updates" (P35).
- There is no offline open engine. Rules and severities cannot be exported `[from memory]`.

### 1.7 GitHub CodeQL / code scanning

- The CLI is free to download, but under these terms: "GitHub CodeQL can only be used on codebases that are released under an OSI-approved open source license, or to perform academic research. **It can't be used to generate CodeQL databases for or during automated analysis, continuous integration or continuous delivery**" (P36).
- Query suites (P37):
  - `default`: queries that "are highly precise and return few false positive code scanning results";
  - `security-extended`: adds "queries with slightly lower precision and severity";
  - `security-and-quality`: everything.
- Each query carries `@precision` and `@security-severity` metadata, and suites select on those `[from memory]`.
- Languages include Python, Go, JS/TS, and Rust since 2025 `[from memory]`.

---

## 2. Where the rules come from

### 2.1 Codacy's engines for arbiter's four languages (P1)

| Language | Static analysis | Secrets | SCA / malicious pkgs | Complexity / duplication | Already in arbiter? |
|---|---|---|---|---|---|
| Python | Bandit, Prospector, Pylint, Ruff, Opengrep | Bandit, Prospector, Opengrep, Trivy | Trivy (`requirements.txt`, `Pipfile.lock`, `poetry.lock`, `uv.lock`) | Lizard / PMD-CPD | Bandit ✔, semgrep `p/python` ✔ (≈ Opengrep), Ruff only if the repo declares it. Pylint, Prospector and Trivy ✘ |
| Go | Revive, Opengrep (server-side); gosec, Staticcheck, GolangCI-Lint, aligncheck, deadcode are "Supported as a client-side tool" (the user runs them and uploads) | Opengrep, Trivy | Trivy (`go.mod`) | Lizard / PMD-CPD | gosec ✔, staticcheck/golangci ✔, govulncheck ✔ (better than Trivy: it is call-graph-reachable). **No semgrep/Opengrep for Go** ✘, Revive ✘ |
| TypeScript | Oxlint, BiomeJS, ESLint, Opengrep | Opengrep, Trivy | Trivy (`package.json`, `package-lock.json`, `yarn.lock`) | Lizard / jscpd | tsc ✔, semgrep `p/typescript` ✔, ESLint only with repo config. Oxlint, Biome, Trivy ✘ |
| Rust | **Opengrep only** (no Clippy) | Opengrep, Trivy | Trivy (`Cargo.lock`) | Lizard / jscpd | clippy ✔, `p/rust` ✔, cargo-deny only if `deny.toml` exists |

Codacy has no proprietary analyzer for these languages. Its own `Codacy Scalameta Pro` is Scala-only (P1).

### 2.2 Proprietary Codacy rules

`codacy-semgrep/docs/` holds Codacy's own Semgrep rules: 27 in `codacy-rules.yaml`, 1 in `codacy-rules-ai.yaml` and 5 in `codacy-rules-i18n.yaml` (P10). For arbiter's languages they are:
- `codacy.javascript.security.hard-coded-password` (ERROR);
- three `codacy.python.openai.*` "guardrails" rules (WARNING/INFO);
- four `codacy.js.i18n.*` rules.

The rest target PL/SQL, Java, C# and Kubernetes. **Codacy adds no security rules worth having for arbiter's languages.**

### 2.3 Codacy's severity is a mechanical remap of the upstream level

- **Semgrep/Opengrep** (`toCodacyLevel`, P10):
  - security-severity `HIGH` → Critical, `MEDIUM` → Medium;
  - otherwise `ERROR` → Critical, `WARNING` → Medium, `INFO` → Low.
  - In Go, the empty `case "CRITICAL":` does not fall through. So rules tagged `CRITICAL` fall back to their plain `severity`. The tiers are bookkeeping, not calibration.
- **Bandit** (P9): Codacy's levels are hand-assigned and often contradict upstream.
  - `B602` `subprocess_popen_with_shell_equals_true` is Codacy `Info` (Minor). Upstream Bandit emits `severity=bandit.HIGH` for the non-literal shell case (P39).
  - `B608` SQL injection is Codacy `Warning`; upstream is `MEDIUM` (P39).
  - `B324` (weak hash) is Codacy `Error`, but **disabled by default**.
  - Split across 81 Bandit patterns: 21 Error, 39 Warning, 21 Info.
- **ESLint** (P11): of 2,811 patterns, **all 40 Security patterns are `Warning`** (Medium), none Critical. They come from eslint-plugin-security, security-node, no-unsanitized and xss.
  - The 81 enabled `Error` (Critical) patterns are ESLint core rules such as `no-undef`, `no-dupe-keys` and `no-unreachable`. In TypeScript, `tsc` already rejects most of them.
  - So for TypeScript, **"Codacy Critical" means "eslint:recommended correctness", not security.**

### 2.4 Other platforms

| Platform | Own rules? | Severity source |
|---|---|---|
| SonarQube | Yes: S-rules plus a closed taint engine (P16, P20) | Sonar's own levels. Published precision *targets* (§3.1) |
| Qlty | Wraps 60+ OSS tools; own smells engine (P22) | Its own high/medium/low (P23) |
| DeepSource | Own engine plus wrapped Bandit and others (P26) | Its own. Critical/Major/Minor `[from memory]` |
| Semgrep Pro | Pro Rules plus interfile taint (P31) | Rule `severity` plus `metadata.confidence`/`impact` |
| Snyk Code | Proprietary (P35) | High/Medium/Low `[from memory]` |
| CodeQL | Own queries (open source in `github/codeql`, but the CLI terms in P36 restrict use) | `@precision` plus `@security-severity` `[from memory]` |

---

## 3. Precision of severity tiers: is "only Critical/Security is worth acting on" supported?

### 3.1 Industry bars

- **Google:** code-review checks must "Produce less than 10% effective false positives. Developers should feel the check is pointing out an actual issue at least 90% of the time." An issue is an "effective false positive" if "developers did not take positive action after seeing the issue". Checks above "10%, the Tricorder team disables" (F1, F2).
- **Sonar's own stated targets** (P13): "For code smells and bugs, zero false positives are expected. At least this is the target … For vulnerabilities, the goal is to have more than 80% of issues be true positives." Even the vendor's target for security (≥80% TP) misses Google's 90% bar.
- **DeepSource's target:** <5% FP (P26), a self-reported vendor claim.

### 3.2 Measured: Bandit on OWASP Benchmark for Python, by severity tier `[measured]`

**Method.**
- Data: OWASP's own committed Bandit 1.8.6 SARIF (F3), scored against `expectedresults-0.1.csv`: 1,230 test cases in 14 CWE categories, 452 real vulnerabilities, base rate 36.7%.
- A test counts as flagged when a Bandit result in that file comes from a rule that targets the test's category. Mapping: B311→weakrand, B324→hash, B307/B102→codeinj, B301/B403/B506→deserialization, B602/B603/B404→cmdi, B608→sqli, B314/B317/B318/B405/B406/B408→xxe.
- This approximates the official scorecard but is not it.

| Tier counted as a finding | Precision | TPR (recall) | FPR |
|---|---|---|---|
| Bandit any severity (LOW+) | 31.6% | 11.1% | 13.9% |
| Bandit MEDIUM+ | 38.7% | 6.4% | 5.9% |
| Bandit HIGH only | 44.4% | 4.4% | 3.2% |
| Codacy levels, Codacy default-enabled patterns, Minor+ | 26.5% | 6.6% | 10.7% |
| Codacy default-enabled, Medium+ | 30.0% | 2.0% | 2.7% |
| **Codacy default-enabled, Critical only** | n/a (0 findings) | **0%** | 0% |

What the table shows:
- Raising the tier trades recall for a small precision gain. Even Bandit HIGH (44%) sits only 8 points above the 36.7% base rate, and far below the 80–90% bars in §3.1.
- Codacy's default Critical tier finds **nothing**, because its one relevant Critical rule (B324) is off by default.
- Bandit found nothing in 9 of 14 categories: path traversal, XSS, XPath, LDAP, redirect, secure cookie, trust boundary, SQLi, and cmdi except 1 case.

### 3.3 Studies

- **SonarQube rules vs faults (F4).** "Among the 202 rules defined for Java by SonarQube, only 25 can be considered to have relatively low fault-proneness. Moreover, violations considered as 'bugs' by SonarQube were generally not fault-prone." This is direct evidence that a vendor's "bug"/high-severity label does not predict faults.
- **Fix rate (F5).** Organizations ran SonarQube "with more than one thousand distinct checkers … on average, 13% of the issues have been solved". The authors "conjecture that just a subset of the checkers reveal real design and coding flaws, and this might artificially increase the technical debt".
- **ML false-alarm filters (F6).** Near-perfect "Golden Features" results came from "data leakage and data duplication". The future-revision label heuristic "produces labels that do not agree with human oracles". Fix-rate-based actionability labels (like F5's 13%) are themselves noisy.
- **SAST in secure code review (F7).** On 815 real vulnerability-contributing commits:
  - a SAST tool warns in the vulnerable function for 52% of them;
  - "at least 76% of the warnings in vulnerable functions are irrelevant";
  - 22% of commits go undetected.
  - Prioritising by SAST improves precision by 12%.
  - So SAST is useful as a ranking signal (E2), not as proof.
- **Pylint/ESLint suppressions (F8).** 7,357 suppressions in 46 Python projects, "one out of six code files". Pylint `invalid-name` alone accounts for 639 suppressions. "50.8% of all suppressions do not affect any warning". The noise is concentrated in convention rules.
- **Pylint hand-labelled (F9).** On 11k lines of Django: "Good" (bugs and helpful) **17**, "Neutral" (cosmetic) 252, "Bad" (unhelpful, can't fix, incorrect) **766**. That is about 1.6% helpful (a single practitioner's labels).
- **Practitioner threads.**
  - Sonar (F10): "people chase metrics for the sake of metrics, instead of understanding that issue count is supposed to reflect the underlying code quality".
  - DeepSource launch (F11): "Critical issues were hidden amongst other minor issues and false-positives, and often missed."

### 3.4 Validity of A–F maintainability grades

- Codacy's grade weights are unpublished (P2), so the grade cannot be checked.
- Sonar's and Qlty's maintainability grades are both debt ratios: summed per-rule remediation minutes ÷ an assumed build cost. Sonar uses 30 min/LoC (P14); Qlty uses COCOMO (P23). Both inputs are constants nobody calibrated against defects.
  - F4 and F5 show the underlying rules mostly do not predict faults and are mostly not fixed.
- Sonar's security and reliability letters are worst-issue grids (P14). One Blocker gives E however good the rest is. That is a gate, not a measurement.

**Verdict on the tier question.**
- Partly supported. Restricting to security/high severity raises precision a little (31.6% → 44.4% in §3.2) and removes most convention noise (F8, F9).
- But no platform's Critical tier reaches the 80–90% precision a blocking finding needs (F1, P13).
- Codacy's tier is a remap, so it is not even a consistent signal (§2.3).
- **Severity labels are not proof.** That matches arbiter's existing rule that analyzer hits are E2 only.

---

## 4. Options for arbiter

### (a) Run the Codacy Analysis CLI as another gate

- **Cost:**
  - a Node 20 dependency;
  - a second copy of tools arbiter already runs (Bandit, Opengrep ≈ semgrep, ESLint);
  - Codacy-chosen default rule sets that differ from the repo's own config;
  - severity remaps (§2.3) that would leak into arbiter's tally;
  - the npm package licence is unchecked `[unverified]`.
- **Value:** Trivy SCA and secrets, plus Pylint and Revive. Trivy is available directly.
- **No.** The same applies to `qlty check`, and Qlty's BUSL grant excludes "Artificial Intelligence Coding Service" use (P22).

### (b) Take the upstream Critical/Security rules and run them through arbiter's tools

I diffed `semgrep/semgrep-rules` (P34) against arbiter's cached packs in `~/.cache/arbiter/semgrep/`: `p-python.yml` has 151 rules, `p-rust.yml` 11, `p-typescript.yml` 74. I counted rules with `metadata.category: security` and `severity: ERROR`, which Codacy maps to Critical `[measured]`:

| Language | Security ERROR rules in repo | Not in arbiter's pack | Confidence of the missing ones |
|---|---|---|---|
| Python | 80 | 25 | **all LOW** (audit rules, such as `python.lang.security.audit.dangerous-subprocess-use-audit`) |
| JavaScript | 38 | 17 | **all LOW** |
| TypeScript | 5 | 2 | HIGH: `typescript.mcp.security.mcp-command-injection-typescript`, `typescript.mcp.security.mcp-ssrf-typescript` (taint) |
| Go | 17 | **17** (arbiter runs no Go pack) | 4 HIGH, 4 MEDIUM, 9 LOW |
| Rust | 0 | 0 | none |
| generic/secrets | 48 | 48 | 1 HIGH, 2 MEDIUM, 45 LOW |

What this means: Semgrep's curated `p/*` packs already exclude exactly the LOW-confidence ERROR rules. For Python and JS, Codacy's "Critical" adds only audit rules that Semgrep itself rates low-confidence.

**Concrete gaps per language, after removing what arbiter's tools already cover:**

- **Go.** Arbiter runs gosec, which covers G201/G202/G701 SQL, G204/G702 exec, G304/G703 path and G708 `text/template` SSTI (P38). Still missing:
  - `go.jwt-go.security.jwt-none-alg.jwt-go-none-algorithm` (HIGH);
  - `go.grpc.security.grpc-client-insecure-connection.grpc-client-insecure-connection` (HIGH);
  - `go.grpc.security.grpc-server-insecure-connection.grpc-server-insecure-connection` (HIGH, taint).
  - Covered by gosec, so redundant: `go.lang.security.injection.tainted-sql-string`, `go.template.security.ssti.go-ssti`, `go.lang.security.audit.dangerous-exec-cmd`, `go.lang.security.filepath-clean-misuse`.
  - Fix: add `Lang.GO: "p/golang"` to `SEMGREP_PACKS` in `arbiter/tools.py`. I did not open that pack's content `[unverified]`.
- **TypeScript.**
  - The two MCP taint rules above.
  - DOM-XSS sinks are already covered: `p/typescript` contains `react-unsanitized-method`, `react-unsanitized-property` and `react-dangerouslysetinnerhtml`, the semgrep equivalents of ESLint `no-unsanitized/*`.
  - eslint-plugin-security rules (`detect-object-injection`, `detect-non-literal-fs-filename`, `detect-unsafe-regex`, …) are Codacy Medium. They are known for noise, so skip them `[from memory]`.
  - ESLint runs only with a repo config. That is correct; keep it.
- **Python.**
  - No HIGH/MEDIUM-confidence security gap. Bandit plus `p/python` covers what Codacy's Python Critical tier contains.
  - Pylint/Prospector are convention-heavy (F8, F9). Skip them.
- **Rust.** No gap. Codacy runs only Opengrep with no Clippy, which is less than arbiter.
- **All languages: secrets.** Arbiter has only Bandit B105–B107 (Python, hard-coded passwords). Codacy, Qlty and DeepSource all ship a secrets scanner (Trivy, gitleaks, trufflehog). **This is a real gap.**
- **Python, TypeScript, Rust: SCA.**
  - Go has govulncheck.
  - Rust has cargo-deny only when `deny.toml` exists.
  - Python and TypeScript have no lockfile vulnerability scan.
  - Codacy uses Trivy for all three (P1); Qlty offers osv-scanner and trivy (P22). **This is a real gap.**

**How each enters arbiter** (methodology §3.4: analyzer output is never shown to finders):

| Addition | Way in | Why |
|---|---|---|
| Secrets scanner (gitleaks or `trivy fs --scanners secret`) | **Verifier candidate seed + E2** | A secret in an added line is a security finding, and the security axis accepts E3/E4 only. Keep it on the never-auto-dismiss list. Whether an exact-match provider token should count as E1 is a methodology decision for Main |
| SCA on lockfiles (osv-scanner or trivy) for Python/TS, and Rust without `deny.toml` | **Deterministic gate, E1** | The deps axis accepts E1. A known advisory on a changed lockfile entry is a measured fact. Compare with base, like build failures |
| `p/golang` semgrep pack (or only the 3 HIGH rules above) | **E2 oracle + seed** | Same handling as `p/python` today |
| `typescript.mcp.security.*` rules | **E2 oracle + seed** | Add to the TS semgrep config |
| Opengrep in place of semgrep CE | **Same E2 slot, better dataflow** | Cross-file taint without Pro (P33). Needs a precision A/B on arbiter's benchmark before switching |
| CodeQL `default` suite | **E2 oracle, opt-in, OSI-licensed repos only** | Highest-precision open query set (P37). The licence (P36) bars it on closed code in automated runs |

### (c) Ignore Codacy

- Cost: zero. Value lost: none that cannot be had directly from Trivy, gitleaks or osv-scanner and the semgrep registry.
- **Chosen for Codacy itself. Option (b) applies, but sourced from upstream tools, not from Codacy's tiers.**

---

## 5. Verdict and ranked recommendation

**Verdict.** Codacy is not obsolete as a product: it now ships a free local CLI, Opengrep, Trivy and AI review. But as a *rule source* for arbiter it adds nothing:
- its engines are the ones arbiter already runs;
- its Critical tier is a remap of upstream levels. That tier is empty for ESLint security rules and default-off for Bandit's one Critical hit (§2.3, §3.2).
- The A–F grade uses unpublished weights.
- Debt-ratio grades (Sonar, Qlty, old Code Climate) rest on rules that mostly do not predict faults (F4) and mostly do not get fixed (F5).

"Only Critical/Security" is directionally right but too weak: even then, precision sits at 44% (§3.2), short of the 80–90% bars (P13, F1). So any such hit stays E2 and seeds the verifier. It never blocks on its own.

### Ranked table: which platforms to leverage

| Rank | Platform / component | Runs locally? Licence / cost | Adds coverage beyond arbiter? | Leverage how |
|---|---|---|---|---|
| 1 | **Secrets + SCA scanners that the platforms wrap** (gitleaks or Trivy secrets; osv-scanner or Trivy for `uv.lock`, `package-lock.json`, `Cargo.lock`) | Yes. OSS (gitleaks MIT, Trivy Apache-2.0, osv-scanner Apache-2.0 `[from memory]`) | **Yes**: secrets in all 4 languages; SCA for Python/TS, and Rust without `deny.toml` | SCA → **deterministic gate (E1, deps axis)**. Secrets → **verifier seed + E2**, never-auto-dismiss |
| 2 | **Semgrep registry / Opengrep** | Yes. Engine LGPL (Opengrep) or LGPL CE; rules under Semgrep Rules License, internal use only (P32) | **Yes for Go** (no Go pack today: jwt-none-alg, 2 gRPC insecure-connection rules); TS MCP taint rules; Opengrep adds cross-file taint (P33) | **E2 oracle + seeds**. It is also the **learned-rules deterministic tier's** target engine. Keep that tier on Semgrep-compatible syntax so Opengrep can run it |
| 3 | **CodeQL** (`default` suite) | Yes, but the licence covers only OSI-licensed code and bars CI/automated use otherwise (P36) | Yes: interprocedural taint in Python, Go and JS/TS, plus Rust `[from memory]` | **Opt-in E2 oracle** when the reviewed repo's licence is OSI-approved. Off by default |
| 4 | SonarQube (Cloud / Server / for IDE) | Taint is server/cloud only (P16). Analyzers under SSAL "Competing" clause (P20). Paid per LoC (P17) | Yes, taint (S3649 and others), but not reachable locally or legally embeddable | **Do not integrate.** Use its precision targets (P13) as a benchmark for arbiter's own rules |
| 5 | Semgrep Code (Pro) | CLI with a cloud login. Free ≤10 contributors (P31) | Cross-file Pro rules | Only if a user already has it: accept its SARIF as E2. Opengrep gives most of the engine gain for free |
| 6 | Codacy Analysis CLI | Yes. Free Developer plan (P8) | No: the same engines; Trivy is the only new piece, and it is available directly | **Ignore** (option c) |
| 7 | Qlty CLI | Yes. **BUSL-1.1 excludes AI coding services** (P22) | No: it wraps the same tools | **Ignore**. Use its plugin list only as a map of tools |
| 8 | DeepSource | No, analysis is cloud-only (P30) | Unknown: closed engine, vendor-run benchmark (P27) | **Ignore** |
| 9 | Snyk Code | No: code upload, or an enterprise Local Engine (P35) | Unknown: closed | **Ignore** |

### Gaps and unverified points

- The `@codacy/analysis-cli` npm licence, and exactly which Opengrep rule sets Codacy enables by default for Python/Go/TS, were not opened `[unverified]`.
- Codacy's grade weights are unpublished. The old formula is only `[from memory]`.
- The Sonar maintainability bands beyond "A ≤ 5%" were cut off in the page render `[from memory]`.
- `p/golang` pack contents were not opened. I recommend it from the semgrep-rules `go/` tree (P34).
- CodeQL `@precision` selectors, Rust support, and the DeepSource and Snyk severity names are `[from memory]`.
- §3.2 uses my own CWE-category scorer, not the OWASP scorecard tool. Benchmark v0.1 is synthetic. Use the numbers as tier *ratios*, not absolute tool precision.
- There is no published per-severity false-positive study for Codacy, Qlty or DeepSource specifically. F4 and F5 are Java/SonarQube. F8 and F9 cover Pylint/ESLint conventions, not security tiers.
- Before switching semgrep CE to Opengrep, it needs a precision A/B on arbiter's own benchmark (`docs/benchmarks.md`). I did not run one.
