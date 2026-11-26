import functools
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreferenceRanker:
    prefs: object

    def score(self, book) -> int:
        return sum(self.prefs.weight(tag) for tag in book.tags)


def reading_list(books, prefs) -> list:
    return sorted(books, key=PreferenceRanker(prefs).score)


def format_reading(reading: float, unit: str) -> str:
    return f"{reading:.1f} {unit}"


def retry(times: int):
    """Retry the decorated callable on OSError.

    >>> retry(3)(print)  # doctest: +SKIP
    """

    def decorate(fn):
        """Captures `times`; the decorator protocol needs a callable, not an instance."""

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            """Captures `fn` and `times`; `functools.wraps` must wrap a plain function."""
            for _ in range(times - 1):
                try:
                    return fn(*args, **kwargs)
                except OSError:
                    continue
            return fn(*args, **kwargs)

        return wrapper

    return decorate


def shelves():
    class Shelf:
        def label(self) -> str:
            return "A"

    return Shelf
