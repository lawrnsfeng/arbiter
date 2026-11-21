# Threat model

Template for `THREAT_MODEL.md` (research-security.md §2 step 1, S7; S36: 90% exploitable findings with a threat model). Keep each section to a few bullets.

## Assets
What must be protected: data, credentials, money, availability of a service, integrity of outputs.

## Entry points
Where outside input enters: HTTP routes, RPCs, CLI commands, file or queue readers, webhooks, LLM output.

## Trust boundaries
Where data crosses from a less trusted to a more trusted zone, e.g. internet → server, user → admin, plugin → host.

## Trusted inputs
Inputs this code may trust without validation, e.g. env vars, CLI flags, config files, authenticated admins, internal queues (S35 precedents).

## In-scope classes
Vulnerability classes to report, with CWE ids, e.g. injection (89, 78, 79), authz (862, 863, 639), SSRF (918), deserialization (502).

## Out-of-scope classes
Classes not to report for this system, e.g. client-side authz checks, issues in test files, DoS for a local CLI.

## DoS policy
State whether DoS, ReDoS and resource exhaustion are in scope. Default: in scope only for a long-running, internet-facing service where unauthenticated input reaches the panic or allocation.
