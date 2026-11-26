---
id: R86
title: A test or e2e server runs with every outbound side effect switched off
tier: semantic
severity: should-fix
status: ok
refs: The Twelve-Factor App "Config" and "Dev/prod parity", Django docs Testing tools (email backend in tests), Sentry Python SDK docs (empty DSN disables sending), pytest docs monkeypatch
---
## Rule

- A server started for a test, an e2e run, or a capture has every outbound third-party integration (error reporting, chat, mail) off before the process starts. (C1)
- "The run does not trigger it" is not acceptable; the run's own configuration switches it off. (C2)
- One key per integration, all pinned, in the configuration the process actually reads. (C3)
- Disabling one integration and leaving the others live is a violation. (C4)
- Pin the error-reporting DSN empty, the chat token null, and the mail server empty, plus their socket/relay siblings. (C5)
- Assert the pins at run time rather than trusting that the configuration file exists. (C6)
- The run reports which integrations are off. (C7)
- Exception: a chat token may be live only when it belongs to the configured sandbox workspace. (C8)
- The sandbox workspace is asserted by its team/workspace id before the run. (C9)
- The run's health ("doctor") check passes for that workspace, and the run overview names the live transport. (C10)
- Under the exception everything else stays pinned: no error reporting, no mail relay, no socket token, never a production workspace. (C11)
- Every message under the exception lands on the operator running the run, never a colleague. (C12)
- Direct sends address the operator's own id; a service-side sender has its resolved recipient ids remapped to the operator for the run and restored afterwards. (C13)
- A run that messages a third party, or leaves fixture ids remapped afterwards, is a violation regardless of test results. (C14)

## Incorrect

- An e2e settings builder that empties the error-reporting DSN but inherits the chat token and mail host from the base config.
- A test server fixture that relies on the scenario never sending mail instead of pinning the mail host.
- A sandbox run that remaps recipients to the operator and never restores them.
- A chat-enabled run that never checks the workspace id before starting.

## Correct

- A run-config builder pinning the DSN empty, the chat token and socket token to `None`, the mail host and relay empty, asserting every pin, and returning the list of disabled integrations for the report.
- The sandbox exception: workspace id asserted before start, every other pin asserted and reported as off, the chat health check required to pass, the overview naming the live transport, and recipients remapped to the operator inside a `try/finally` that restores them.
- Look-alike: a production settings module that reads live values (not a test server).

## LLM scan

- Find configuration that starts a server for tests, e2e runs, or captures (fixtures, run scripts, settings overlays,
  compose/env files). For each, list the outbound integrations the base configuration enables (error reporting, chat,
  mail, plus socket and relay siblings) and report every one not pinned off in the configuration the process actually
  reads (C1, C3, C5); report partial pinning explicitly (C4).
- Report a run that relies on scenarios not triggering an integration instead of disabling it (C2), that never asserts
  its pins at run time (C6), or that does not report which integrations are off (C7).
- For a live chat token, require all of: the sandbox workspace asserted by id before the run (C8, C9), a passing
  health check and the overview naming the transport (C10), everything else pinned and never a production workspace
  (C11), every message addressed to the operator (C12), recipient remapping restored in a `finally` (C13, C14).
- Do not flag production or staging configuration, or integrations replaced by an in-process fake (locmem mail
  backend, a recording transport).
