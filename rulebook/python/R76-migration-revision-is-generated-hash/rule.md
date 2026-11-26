---
id: R76
title: A migration revision id is the tool-generated hash, never a hand-written mnemonic
tier: ast+semantic
severity: should-fix
status: ok
refs: Alembic tutorial (alembic.sqlalchemy.org/en/latest/tutorial.html), Alembic branches and heads (alembic.sqlalchemy.org/en/latest/branches.html), Flask-Migrate docs
---
## Rule

- A migration's `revision` is the 12-lowercase-hex identifier the migration tool generated (`alembic revision`, `flask db migrate`, the framework's own command), never a value a person typed. (C1)
- Every `down_revision` (each element of a merge tuple included) is likewise a tool-generated 12-hex identifier. (C2)
- A hand-written mnemonic id (anything that is not 12 lowercase hex characters) is a violation even though the version column accepts it. (C3)
- The migration file is named `<revision>_<slug>.py`: the filename prefix equals the revision hash. (C4)
- The docstring's `Revision ID:` line carries the same hash as the module's `revision` assignment. (C5)
- The docstring's `Revises:` line carries the same hash(es) as the module's `down_revision` assignment. (C6)
- A new migration's `down_revision` is read from the tool's `heads`, never assumed from the last filename in sort order. (C7)

## Incorrect

- A migration whose `revision` is a readable mnemonic and whose docstring repeats that mnemonic.
- A merge migration whose `down_revision` tuple holds one real hash and one mnemonic.
- A docstring `Revises:` line naming a different parent than the `down_revision` assignment.
- Not in `bad.py`: a file named `<prefix>_<slug>.py` whose prefix is not the module's `revision` (C4). Replay requires the
  example to be named `bad.py`, which has no `<prefix>_` part, so this branch of the detector runs only on real
  migration files.
- A new migration chained onto the alphabetically last file while another head exists (model only).

## Correct

- A migration with a generated 12-hex `revision`, a 12-hex `down_revision`, and docstring lines that agree.
- Look-alike: a function-local `revision = "draft-2"` that is not a migration header.

## Detection

Only modules that bind both `revision` and `down_revision` at module level (plain or annotated assignment) are
migrations. For those, `check.py` reports at the assignment line:

- `revision` not matching `^[0-9a-f]{12}$` (C1, C3);
- any string in `down_revision` (a string or a tuple/list of strings; `None` is a root) not matching it (C2, C3);
- the docstring's `Revision ID:` value differing from `revision` (C5), reported on the `revision` line;
- the docstring's `Revises:` values (comma-separated) differing from the `down_revision` strings (C6), reported on the `down_revision` line;
- a filename of the form `<prefix>_<slug>.py` whose prefix differs from `revision` (C4), reported on the `revision` line.

## LLM scan

- C7: when a change adds a migration, check its `down_revision` against the other migrations' revisions in the
  change and the repo: report it when another migration already names the same parent (two heads), or when the
  parent is not the current head but merely the last file in sort order. Quote both files.
- Do not flag Django migrations (`dependencies = [...]`), seed scripts, or non-migration modules that happen to use the
  word `revision`.
