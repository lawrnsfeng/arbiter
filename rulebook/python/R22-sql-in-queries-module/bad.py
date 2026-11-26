from psycopg import sql

OVERDUE_SQL = "SELECT title FROM loans WHERE due < now()"  # expect: R22


def refresh_popular(cur) -> None:
    cur.execute(sql.SQL("REFRESH MATERIALIZED VIEW popular_titles"))  # expect: R22


def titles_for(cur, member: str) -> list[str]:
    cur.execute("SELECT title FROM loans WHERE member = %s", (member,))  # expect: R22
    return [row[0] for row in cur.fetchall()]


def extend(cur, loan_id: int, days: int) -> None:
    cur.execute(f"UPDATE loans SET due = due + {days} WHERE id = %s", (loan_id,))  # expect: R22


def drop_holds(cur, member: str) -> None:
    query = """
        DELETE FROM holds
        WHERE member = %s
    """
    cur.execute(query, (member,))  # expect: R22


def overdue_clause(days: int) -> str:
    return "due < now() - interval '%s days'" % days  # expect-llm: R22
