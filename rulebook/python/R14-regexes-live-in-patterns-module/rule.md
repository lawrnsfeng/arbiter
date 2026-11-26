---
id: R14
title: Regexes live in one patterns module, each named for what it matches
tier: ast+semantic
severity: should-fix
status: ok
refs: Python docs re.compile (https://docs.python.org/3/library/re.html#re.compile), Python docs re.VERBOSE (https://docs.python.org/3/library/re.html#re.VERBOSE), Fowler Refactoring catalog "Replace Magic Literal" (https://refactoring.com/catalog/replaceMagicLiteral.html)
---
## Rule

- Compiled regexes live in one dedicated patterns module per subsystem (for example `<package>/<subsystem>/patterns.py`),
  not scattered across modules next to unrelated functions. (C1)
- Each regex is a named constant whose name says what it matches. (C2)
- The example of what the pattern matches lives in the patterns module's docstring, next to the pattern's name, not
  in a `#` comment above the pattern; the pattern's identity is its name plus that example (see also R75). (C3)
- The docstring example is a real string the pattern matches. (C4)

## Incorrect

- Module-level `re.compile(...)` constants sitting above unrelated functions, one with a `# matches "..."` comment.
- A `re.compile(...)` inside a function body.
- A `compile` imported from `re` and called in a class body.
- A regex in the patterns module named vaguely (`RX1`) or documented by an example it does not match (model checks the
  name's meaning).

## Correct

- A patterns-only module whose docstring lists each UPPER_CASE pattern constant with a backticked example it matches.
- Look-alikes: `re.escape`, an uncompiled string constant, verbose patterns whose flag is `re.VERBOSE`, `re.X`, a
  `VERBOSE` imported from `re` under another name, or an inline `(?x)`.

## Detection

`check.py` treats a module with no function or class definitions as a patterns module.
- Elsewhere, it reports every `re.compile` / `regex.compile` (or `compile` imported from them) with a literal pattern
  (C1); computed patterns are skipped because they cannot move.
- In a patterns module, for each module-level `NAME = re.compile(...)`, it reports: a name that is not UPPER_CASE
  (C2); a `#` comment on the line directly above (C3); no backticked example on a module-docstring line naming the
  constant (C3); a literal pattern that `search`es none of those examples, compiled with its flags (`re.X`, a flag
  name imported from `re`, or inline flags) (C4).

## LLM scan

- Report UPPER_CASE pattern names that do not say what they match (`PATTERN`, `RX1`, `REGEX_A`) (C2).
- Report a subsystem with more than one patterns module, or regexes passed inline to `re.match` / `re.search` /
  `re.sub` instead of a named compiled constant (C1, C2).
- Report examples that are invented placeholders rather than a real string from the data the pattern parses (C4).
- Do not flag computed patterns built from runtime input, or `re.escape` of a literal.
