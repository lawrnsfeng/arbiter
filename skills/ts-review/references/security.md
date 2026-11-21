# TypeScript security checklist

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

## Supply chain

| Ecosystem | Review on every lockfile/manifest diff | Policy to check exists | Tool or evidence |
|---|---|---|---|
| **npm / pnpm** | New direct or transitive packages; `resolved` changed to git or tarball URLs; integrity hash changed without a version change `[from memory]`; a dependency that newly gained `preinstall`/`install`/`postinstall`; a version published under 24 h ago | pnpm: `allowBuilds` allowlist, `strictDepBuilds`, `blockExoticSubdeps`, `minimumReleaseAge` (default 1440), `trustPolicy: no-downgrade`, `namedRegistries` (S30). npm: `allowScripts` plus `strict-allow-scripts`, `min-release-age`, `ignore-scripts` in CI (S31). Publishing via trusted publishing, not tokens (S28) | `npm audit`/`pnpm audit` `[from memory]`; provenance or trust-level downgrade (S30); some scanners read only the first document of the two-document `pnpm-lock.yaml` and wrongly report zero dependencies (S30) |
| **GitHub Actions / CI** | `pull_request_target` or `workflow_run` plus checkout of PR code (critical, S33); `${{ github.event.* }}` interpolated into `run:`; actions not pinned by SHA; broad `GITHUB_TOKEN` permissions `[from memory: Scorecard Pinned-Dependencies / Token-Permissions]` | Branch protection: 1–2 reviewers, code owners, status checks (S33); SLSA Build L2+ signed provenance (S34); a published artifact matches its source (S29) | Scorecard `Dangerous-Workflow`, `Branch-Protection`, `Binary-Artifacts` (S33); ToB `agentic-actions-auditor`, `supply-chain-risk-auditor` skills (S39 repo) |

**Supply-chain "don't flag" defaults:** outdated-but-not-vulnerable dependencies. S35 exclusion 9 routes known-CVE dependency findings to a separate SCA gate instead of the code reviewer.
