# Python security checklist

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

## Supply chain

| Ecosystem | Review on every lockfile/manifest diff | Policy to check exists | Tool or evidence |
|---|---|---|---|
| **PyPI / uv / pip** | New packages; sdists that execute `setup.py` at install `[from memory]`; model files loaded with `torch.load` or HF downloads without a pinned revision (B614, B615) | `uv.lock` committed; `exclude-newer` window (S32); hash-pinned installs `pip --require-hashes` `[from memory]`; trusted publishing (S28) | `pip-audit` `[from memory]`; bandit B614/B615 |
| **GitHub Actions / CI** | `pull_request_target` or `workflow_run` plus checkout of PR code (critical, S33); `${{ github.event.* }}` interpolated into `run:`; actions not pinned by SHA; broad `GITHUB_TOKEN` permissions `[from memory: Scorecard Pinned-Dependencies / Token-Permissions]` | Branch protection: 1–2 reviewers, code owners, status checks (S33); SLSA Build L2+ signed provenance (S34); a published artifact matches its source (S29) | Scorecard `Dangerous-Workflow`, `Branch-Protection`, `Binary-Artifacts` (S33); ToB `agentic-actions-auditor`, `supply-chain-risk-auditor` skills (S39 repo) |

**Supply-chain "don't flag" defaults:** outdated-but-not-vulnerable dependencies. S35 exclusion 9 routes known-CVE dependency findings to a separate SCA gate instead of the code reviewer.
