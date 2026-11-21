# False-positive exclusions

Do not report these. Sources: the official `code-review` plugin (`commands/code-review.md` lines 42–52 and 80–87) and the S35 security precedents in `research/research-security.md` §2.

## General (code-review plugin)

Report only high-signal issues: code that will fail to compile or parse, code that definitely produces wrong results, or a clear repo-rule violation whose exact rule you can quote. Do not report:

- Pre-existing issues: code this change did not add.
- Something that appears to be a bug but is actually correct. Read the surrounding code before deciding.
- Pedantic nitpicks that a senior engineer would not flag.
- Issues that a linter, type checker or compiler will catch.
- General code quality concerns (e.g. lack of test coverage, general security worries) with no cited rule. Evolvability findings need a `rule`.
- Issues silenced in the code with an ignore comment that gives a reason (e.g. `# noqa: E501  -- generated table`).
- Subjective suggestions or improvements with no concrete defect or rule behind them.
- Potential issues that depend on specific inputs or state you cannot show are reachable.

If you are not certain an issue is real, do not flag it. False positives erode trust.

## Security precedents (S35, with research-security.md §2 overrides)

- Environment variables and CLI flags are trusted input.
- UUIDs (v4) are unguessable; do not report enumeration of them.
- Test files, fixtures and docs are out of scope for security findings.
- React and Angular escape output by default. Report XSS there only with `dangerouslySetInnerHTML`, `bypassSecurityTrust*` or direct DOM sinks (`innerHTML`, `outerHTML`, `document.write`).
- SSRF counts only when the attacker controls the host or the protocol, not just the path.
- Missing client-side authorization checks are not a vulnerability; the server must enforce.
- Logging URLs is safe; logging secrets or PII is not.
- User text in an LLM prompt with no tools, secrets or write scope is not a vulnerability (S35 exclusion 14).
- DoS, ReDoS and resource exhaustion: only when the threat model's DoS policy puts them in scope.
- Hard-coded placeholder values and test credentials are not secrets.
