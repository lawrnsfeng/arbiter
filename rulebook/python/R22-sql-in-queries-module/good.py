from library.db import queries

SHELF_NOTE = "Update the shelf from the returns cart before closing"


def titles_for(cur, member: str) -> list[str]:
    cur.execute(*queries.titles_for(member))
    return [row[0] for row in cur.fetchall()]


def refresh_popular(cur) -> None:
    cur.execute(queries.refresh_popular_titles())


# Look-alike: execute() on a task runner with a non-SQL command name.
def run_nightly(runner) -> None:
    runner.execute("rebuild-index", retries=2)
    runner.execute("select the next shelf")
