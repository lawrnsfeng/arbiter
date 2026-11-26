---
id: R22
title: SQL statements live in one queries module per subsystem
tier: ast+semantic
severity: should-fix
status: ok
refs: owner convention, Fowler: Move Function, psycopg docs: psycopg.sql (composing SQL), SQLAlchemy docs: text()
---
## Rule

- SQL statements live in one queries module per subsystem (e.g. `<package>/db/queries.py`). (C1)
- No SQL literal (a string, an f-string or a `sql.SQL("...")` / `text("...")` wrapper) inline next to or inside a cursor's `execute` call anywhere else. (C2)
- Other modules call the queries module's named functions (e.g. `queries.titles_for(member)`), not raw statements. (C3)

## Incorrect

- `cur.execute(sql.SQL("REFRESH MATERIALIZED VIEW popular_titles"))` inside a domain function.
- `cur.execute("SELECT title FROM loans WHERE member = %s", ...)` and an f-string `UPDATE` passed to `execute`.
- `query = "DELETE FROM holds WHERE ..."` in a function, then `cur.execute(query)`.
- A module-level `OVERDUE_SQL = "SELECT ..."` constant in a non-queries module.
- A function outside the queries module that builds and returns SQL text for others to run (model only).

## Correct

- `library/db/queries.py` defines `titles_for(member)` / `refresh_popular_titles()` returning composed statements;
  the domain module calls `cur.execute(*queries.titles_for(member))`.
- Look-alikes: `execute()` on a non-SQL object with a non-SQL string; an "Update the shelf from ..." message string.

## Detection

`check.py` skips any module named `queries.py` or inside a `queries` or `migrations` package, and reports, elsewhere:

- each `.execute` / `.executemany` / `.executescript` / `.mogrify` call whose first argument is SQL text: a string,
  f-string, `%`/`+` expression or `.format()` call over a string that starts with an SQL verb and contains an SQL
  clause word; or any `SQL(...)` / `text(...)` wrapper call; or a local name assigned such a value in the same
  function (one hit at the `execute` line) (C2);
- each module-level or class-level assignment of a SQL wrapper call, or of an upper-case SQL string literal, in a
  non-queries module (C1).

## LLM scan

Find SQL that the detector cannot recognise as SQL: statements assembled in helper functions outside the queries
module, SQL passed through variables across functions, lower-case or unusual SQL strings, ORM raw-SQL calls
(`.raw(...)`, `.extra(...)`, `connection.exec_driver_sql`). Flag them (C1, C2) and propose a named function in the
subsystem's queries module that callers use (C3). Also flag a subsystem with more than one module holding its SQL
(C1). Do not flag the queries module itself, migrations whose framework requires inline SQL, or test fixtures that
deliberately run ad-hoc SQL.
