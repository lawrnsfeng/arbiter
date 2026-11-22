---
id: A1b
output: findings
refs: [{"file": "idioms.md", "rows": ["Types", "Data modeling"]}]
---
# A1b edge
## Mission
Find added code that breaks on a reachable boundary input: null or empty, overflow, encoding, time zone, unchecked index or malformed input.
## Axes
`edge` only (research-axes.md §2a axis 2; CWE-20, CWE-476).
## Read these language references
`idioms.md` rows Types, Data modeling (appended below).
## Checklist
1. Empty and missing: empty list, string, map; `None`/`nil`/`null`/`undefined`; `Option::None`; zero-length reads.
2. Numbers: integer overflow or truncating casts, division by zero, negative values where only positive make sense, float equality, NaN.
3. Indexing: unchecked index or key, `unwrap()`/`!`/`[0]` on a value that can be absent, `get_unchecked`.
4. Text: Unicode vs bytes, encoding assumptions, case folding, trailing newline, locale.
5. Time: naive vs aware datetimes, time zones, DST, month/year boundaries, monotonic vs wall clock.
6. Malformed external input: parsing (`parse`, `JSON.parse`, `int()`) without handling failure, type assertions on unvalidated data (`as User`).
7. **Reachability is required.** Find the entry point or caller that passes the boundary value (grep the function name, read the callers). If no caller can pass it, do not report it. Tools over-raise robustness issues compared with humans (research-axes.md §2a, S8).
## Do not report
- Inputs that a type, validator or caller already rules out (read it and cite it if you rely on it).
- Wrong results on normal inputs (A1a), swallowed errors (A2), injection (A3).
- Defensive checks you would like for unreachable values.
- Lines this change did not add.
## Proof plan hints
- E3: a snippet calling the function with the boundary input, showing the crash or wrong value.
- E4: a regression test with that input, oracle from the type contract or docstring.
- E6: a property test or fuzz target when a class of inputs fails; keep the minimized input.
## Output
`{"findings": [...]}`; `axis` = `edge`; `trigger` names the exact input and the caller path that delivers it.
