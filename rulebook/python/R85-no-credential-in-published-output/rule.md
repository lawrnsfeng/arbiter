---
id: R85
title: No credential is written where another system will publish it
tier: ast+semantic
severity: should-fix
status: ok
refs: OWASP Logging Cheat Sheet (data to exclude), CWE-532 Insertion of Sensitive Information into Log File, CWE-209 Error Message Containing Sensitive Information, Python docs urllib.parse (urlsplit), SQLAlchemy docs URL.render_as_string(hide_password=True)
---
## Rule

- A connection string, API token, session cookie, or password is never interpolated into a string that leaves the process (a log line, a JSON verdict, a rendered report, an artifact file, an exception message). (C1)
- Emit the parts, never the credential-bearing string. (C2)
- A database identity is emitted as scheme, host, port and database name, never as a URL with a userinfo section. (C3)
- A token is emitted as a boolean "configured" or a fingerprint, never its value. (C4)
- A URL destined for an artifact drops its userinfo at construction, not at the sink. (C5)
- Redact at the producer, never at the sink; a masking pass over finished output is not a substitute. (C6)
- If a value must reach a log or report, the producer builds the redacted form. (C7)

## Incorrect

- A health probe putting `str(config.database_url)` into the verdict dict it returns.
- A logger call passing an API key as a `%s` argument.
- An f-string log line embedding a token attribute.
- An exception message built from a DSN.
- A `print` concatenating a session cookie.
- A log call carrying a DSN as a keyword argument and inside `extra={...}`.
- An exception raised with a message local built from a database URL first.
- A report writer that masks secrets in the finished JSON with a regex (model only).
- An artifact URL built with `user:password@` and redacted later (model only).

## Correct

- The probe as `StoreIdentity.from_config(config)`, returning scheme, host, port and database parsed from the URL; a token reported as configured plus a short fingerprint; a project error whose template names only the host.
- Look-alikes: a bearer token passed into a request header; `bool(api_key)` and `token is not None` in log lines; a
  pagination `next_page_token` logged and passed to an exception.

## Detection

`check.py` reports a value whose name (the last identifier of a name or attribute) is credential-like —
`password`, `passwd`, `secret`, `api_key`, `token`, `dsn`, `cookie`, `credential(s)` as a whole word or `_`-suffix, or
`database/db/conn/connection` + `url/uri/string/str`, but not a pagination cursor (`page_token`, `next_token`,
`continuation_token`, …) — when it is rendered as text (directly, inside an f-string, a dict literal, through
`str()`/`repr()`/`.format()`, `+` or `%`, or through a local first bound to such a rendering) into:

- a positional or keyword argument (`extra={...}` included) of `print(...)` or of a
  `debug/info/warning/error/exception/critical/log` call on a receiver whose name contains `log` (C1, C7);
- a positional or keyword argument of a raised exception, including a message local built before the `raise` (C1);
- a dict literal value `str(<credential>)` (C1, C2, C3).

Wrapping the value in any other call (`bool`, `len`, a hash) hides it (C4).

## LLM scan

- Confirm or dismiss each detector hit: dismiss values whose name only looks like a credential (a lexer token, a
  cursor under an unusual name, a CSRF form field name rather than its value) and say why; every other hit stands.
- Follow credentials the detector cannot name: values read from settings under neutral names (`target`, `url`,
  `conn`), URLs that carry `user:password@`, values copied into verdict/report dicts, artifact files, rendered HTML or
  Markdown, or JSON dumps (C1, C3, C5).
- Report masking or redaction applied to finished output (regex over a JSON string, a log filter that scrubs) as the
  only protection (C6), and URLs whose userinfo is stripped at the sink rather than at construction (C5).
- Report tokens emitted by value where a boolean or fingerprint suffices (C4); check that a value which must reach a
  report is built redacted by its producer (C7).
- Do not flag credentials sent to the system that needs them (request headers, driver connect calls, auth payloads),
  nor fingerprints, booleans, lengths, or lexer/parser tokens.
