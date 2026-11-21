# Go security checklist

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

## Supply chain

| Ecosystem | Review on every lockfile/manifest diff | Policy to check exists | Tool or evidence |
|---|---|---|---|
| **Go** | New modules; new `replace` directives `[from memory]`; widened `GOPRIVATE`/`GONOSUMDB`, which disables checksum-database verification (S22); `GOFLAGS=-mod=mod` in CI | `go.sum` committed; `-mod=readonly` (S22) | `govulncheck ./...`: findings are only call-stack-reachable symbols (S21) |
| **GitHub Actions / CI** | `pull_request_target` or `workflow_run` plus checkout of PR code (critical, S33); `${{ github.event.* }}` interpolated into `run:`; actions not pinned by SHA; broad `GITHUB_TOKEN` permissions `[from memory: Scorecard Pinned-Dependencies / Token-Permissions]` | Branch protection: 1–2 reviewers, code owners, status checks (S33); SLSA Build L2+ signed provenance (S34); a published artifact matches its source (S29) | Scorecard `Dangerous-Workflow`, `Branch-Protection`, `Binary-Artifacts` (S33); ToB `agentic-actions-auditor`, `supply-chain-risk-auditor` skills (S39 repo) |

**Supply-chain "don't flag" defaults:** outdated-but-not-vulnerable dependencies. S35 exclusion 9 routes known-CVE dependency findings to a separate SCA gate instead of the code reviewer.
