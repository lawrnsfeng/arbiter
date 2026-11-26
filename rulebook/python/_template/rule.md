---
id: R0
title: One-line generalised name of the rule
tier: ast
severity: should-fix
status: ok
refs: owner convention
---
## Rule

- First clause of the rule, generalised. (C1)
- Every further clause, threshold, exception and scope note as its own bullet. (C2)

## Incorrect

- One line per case in bad.py.

## Correct

- One line per case in good.py, look-alikes included.

## Detection

Exactly what check.py reports, and which clauses it covers. Omit this section when the tier is `semantic`.

## LLM scan

Present iff the tier contains `semantic`: what the model must look for beyond the detector, and what not to flag.
