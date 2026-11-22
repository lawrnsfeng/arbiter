"""Text helpers for building URLs."""

import re

_NON_WORD = re.compile(r"[^a-z0-9]+")


def slugfy(title: str) -> str:
    """Return a lowercase, hyphen-separated slug for `title`."""
    return _NON_WORD.sub("-", title.lower()).strip("-")


def post_url(title: str, year: int) -> str:
    """Return the blog path for a post."""
    return f"/{year}/{slugfy(title)}/"
