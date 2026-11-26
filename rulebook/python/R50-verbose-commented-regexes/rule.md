---
id: R50
title: Regexes compile verbose, every part commented, every literal space escaped
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs re.VERBOSE, Python docs Regular Expression HOWTO (verbose patterns)
---
## Rule

- Every compiled regex uses the `re.VERBOSE` flag. (C1)
- Every part of the pattern has its own trailing `#` comment naming what it matches or captures. (C2)
- Every literal space in the pattern is escaped as `\ `, because verbose mode ignores unescaped whitespace. (C3)
- These per-part `#` comments are allowed even where comments are otherwise discouraged: they are the pattern's own grammar, not commentary about code. (C4)
- The real example string the pattern matches lives in the docstring of the pattern's module, never in a `#` line above the pattern. (C5)

## Incorrect

- A one-line pattern compiled with no flags.
- A pattern compiled with another flag but not `re.VERBOSE`.
- A pattern held in an annotated module-level string constant, compiled with no flag.
- A one-line pattern compiled `re.VERBOSE` whose single part has no comment.
- A verbose pattern line with an unescaped space between two words, meant to match a space.
- A verbose pattern with one part lacking a comment, and its example in a `#` line above it.
- A commented, escaped verbose pattern whose example string sits in a `#` line above it instead of the module docstring (model only).

## Correct

- Verbose patterns, one commented part per line, literal spaces written `\ `, examples in the module docstring.
- Flags combined (`re.VERBOSE | re.IGNORECASE`) or passed as `flags=re.X`.
- A space inside a character class (literal there even in verbose mode).
- An inline `(?x)` flag; `VERBOSE` imported from `re`.
- Layout spaces around an alternation in a verbose pattern.
- A pattern held in a module-level string that opens with an inline `(?x)`.
- `str.split(" ")`, which is not a regex.

## Detection

Covers C1, C2 for literal patterns, and a definite subset of C3, for `re.compile` / `regex.compile` calls. C1: the
flag arguments are all flag names (`re.I`, imported `IGNORECASE`, `0`, joined with `|`) and none is `VERBOSE`/`X`,
and the pattern (a literal, or a module-level string constant it names, plain or annotated) does not open with an inline `(?x)`; one hit
at the call. A flag held in a variable or built by a call, or a pattern computed at run time, is not decided here. For verbose patterns given as a string literal: C2, one hit at the call counting the
non-blank pattern lines that have no unescaped `#` outside a character class; C3, one hit per pattern line with an
unescaped space, outside a character class, between two literal letters or digits (`from (`, `km h`), at that line.
Spaces next to operators and brackets (`(?: GET | POST )`) may be layout and are left to the model. C4 is a
permission and needs no check.

## LLM scan

Look at every compiled regex. Report a `#` comment line directly above the pattern (or above its assignment) that
holds an example of the text it matches (C5): the example belongs in the module docstring. For patterns built from
non-literal strings (variables, f-strings, concatenation of names), or compiled with flags held in a variable, check
C1, C2 and C3 by reading how the string and flags are built. For every verbose pattern, check that each line holds
one part: a line packing several groups or tokens under a single comment breaks C2. Report unescaped spaces next to
operators or brackets that were meant to match a space (C3); spaces that are only layout are fine.
Do not flag the per-part `#` comments inside a verbose pattern (C4), comments above a pattern that explain intent but
show no example string, or `re.match` / `re.search` called with a pattern that is not compiled.
