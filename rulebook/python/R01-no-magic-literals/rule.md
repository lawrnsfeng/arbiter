---
id: R1
title: No magic literals: every meaningful value is a named constant
tier: ast+semantic
severity: should-fix
status: ok
refs: Fowler Refactoring catalog "Replace Magic Literal" (https://refactoring.com/catalog/replaceMagicLiteral.html), PEP 8 "Constants" (https://peps.python.org/pep-0008/#constants)
---
## Rule

- Constants live in the package's `constants.py` module. (C1)
- The program's own name is a constant in that constants module, never an inline literal. (C2)
- No inline service-name literals, including a service name bound to a local or module-level name in a non-constants module. (C3)
- No inline host literals, such as an IP address passed at a call site. (C4)
- No inline port literals. (C5)
- No inline filename literals. (C6)
- Call sites import the named constant from the package's constants module and pass it instead of the literal. (C7)
- The rule covers every magic literal, not only the categories above: business numbers (rates, caps, thresholds,
  limits, timeouts, sizes, intervals) are named constants, never inline. (C8, owner ruling)
- Meaningful strings used in logic (states, kinds, modes compared or dispatched on) are named constants, never
  inline. (C9, owner ruling)
- Neutral literals stay inline: `0`, `1`, `-1`, `""`, `True` / `False` / `None`, an index or slice bound, a `range`
  step of 1, and the value in the constant's own definition. (C10, owner ruling)
- Tests' expected values are exempt. (C11, owner ruling)
- The named constant lives where this rule, R36 and R38 put it: the package's constants module, or, for a constant
  used by one class only, an attribute of that class. (C12, owner ruling)

## Incorrect

- A module-level IP address constant defined in an ordinary module (model only).
- `argparse.ArgumentParser(prog="...")` with the program name inline.
- A socket connection to an inline IP address and port tuple.
- A client built with `host="..."` and `port=6379` keywords.
- A path built as `root / "readings.csv"` and a file opened as `open("stations.json")`.
- A feed (service) name defined locally and passed to a subscription call (model only).
- A threshold compared inline (`if gust_kmh > 90`) and a negative bound (`celsius < -40`).
- Business numbers passed as `timeout=15` and `max_retries=4` keywords.
- A state string compared inline (`if station.state == "offline"`) and an interval string `every="1h"` (model only).

## Correct

- Every host, port, file name, feed name and the program name imported from the package's constants module.
- Thresholds, timeouts, retry counts and state strings as named constants (a class attribute for one used by a single
  class).
- Look-alikes: a version string (a constant's own definition), neutral literals (`> 0`, `>= 1`, `[-3:]`), a dict key
  named `host`, a default parameter bound to a constant, an IP address as the default of a configuration dataclass
  field (a settings default, not a call-site literal), a test's expected value.

## Detection

`check.py` skips any module named `constants.py` and reports, once per literal node:
- a string literal that is an IPv4 address or `::1` passed at a call site, as an argument or inside a tuple / list /
  dict argument (C4, C7); a field or parameter default is not a call site;
- a string literal passed as a `host=` / `hostname=` keyword, an int literal passed as `port=` (C4, C5, C7);
- a string literal passed as `prog=` or click's program-name keyword (exactly those two keywords) (C2);
- a file-name literal (a name with a common data/config extension such as `.json`, `.csv`, `.toml`, `.log`) that is the right
  operand of `/`, an argument of `open`, `Path`, `PurePath`, `joinpath` or `os.path.join`, or a `filename=` / `file=` /
  `path=` keyword (C6, C7);
- inside a function, a numeric literal other than `0`, `1`, `-1` (and their float forms) that is an operand of an
  ordering comparison (`<`, `>`, `<=`, `>=`): an inline threshold (C8, C10);
- inside a function body, a numeric literal other than `0`, `1`, `-1` passed as a business keyword: `timeout`,
  `limit`, `ttl`, `delay`, `interval`, `threshold`, `rate`, `cap`, `retries`, `size`, `expires` / `expiry`, any
  `max_*` / `min_*`, and names ending `_timeout`, `_limit`, `_ttl`, `_interval`, `_threshold`, `_rate`, `_delay`,
  `_size`, `_seconds`, `_secs` (C8, C10). Declarative calls at class or module level and in decorators (field specs
  such as `CharField(max_length=64)`, `@task(max_retries=5)`) are left to the model.

Test code is skipped (C11): modules named `test_*.py` / `*_test.py` / `conftest.py`, modules under a `tests` /
`testutils` directory, and functions named `test_*`.

## LLM scan

- Find named constants (UPPER_CASE module-level values: service names, hosts, ports, file names, the program name) defined
  outside the package's constants module, including module-level IP addresses, and report the definition; the
  constants module is the only home (C1, C3). Configuration-class field defaults are not such constants.
- Find inline service, queue, feed, backend or database names passed as string literals at call sites, and hosts, ports
  or file names in shapes the detector misses (positional host/port tuples, URLs with a host and port, file names
  without a common extension) (C3, C4, C5, C6).
- Report call sites that redefine a value the constants module already exports instead of importing it (C7).
- Report every other magic literal (C8, C9): business numbers in arithmetic, `==` comparisons, positional arguments
  or returned values (rates, caps, sizes, durations such as `* 86400`), and meaningful strings used in logic (states,
  kinds, modes compared with `==` / `in`, used as dispatch keys or passed as mode arguments such as `every="1h"`).
  Include business numbers in declarative field specs and decorators (`CharField(max_length=64)`,
  `@task(max_retries=5)`), which the detector leaves out. Neutral literals stay inline (C10); do not flag test
  expectations (C11).
- When reporting, name the home of the constant: the constants module, or the attribute of the one class that uses it
  (C12, with R36 and R38).
- Do not flag literals inside the constants module itself, test fixture data that is the subject of the test, log or
  error message prose, or dictionary keys.
