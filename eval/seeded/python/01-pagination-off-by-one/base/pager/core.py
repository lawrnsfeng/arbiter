"""Helpers for splitting record lists into pages."""


def total_pages(count: int, per_page: int) -> int:
    """Return how many pages hold `count` items at `per_page` items per page."""
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    return (count + per_page - 1) // per_page
