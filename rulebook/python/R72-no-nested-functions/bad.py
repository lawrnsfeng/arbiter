import functools
import logging

log = logging.getLogger(__name__)


def reading_list(books, prefs) -> list:
    def score(book) -> int:  # expect: R72
        return sum(prefs.weight(tag) for tag in book.tags)

    return sorted(books, key=score)


def stock_take(shelves) -> dict:
    @functools.lru_cache(maxsize=64)
    def count(code: str) -> int:  # expect: R72
        """Count copies on the captured shelves; cached because shelves repeat codes."""
        return sum(shelf.copies(code) for shelf in shelves)

    totals = dict(map(lambda code: (code, count(code)), shelves.codes))
    totals["missing"] = count("?")
    return totals


def audit(shelves, report) -> None:
    def missing(shelf) -> int:  # expect: R72
        """Copies missing on one shelf, captured `report` collects them."""
        return report.add(shelf.expected - shelf.found)

    report.register(missing)
    missing(shelves[0])
    missing(shelves[-1])


def station_report(readings: list[float]) -> list[str]:
    def fmt(reading: float) -> str:  # expect: R72
        """Format one reading."""
        return f"{reading:.1f} C"

    return [fmt(r) for r in readings]

def best_first(items, prefs) -> object:
    def key(item) -> int:  # expect: R72
        """Rank by the captured preferences; `list.sort` needs a callable."""
        return prefs.rank(item)

    items.sort(key=key)
    return key(items[0])



def shelve(books, shelf) -> None:
    def place(book) -> None:  # expect: R72
        """Place one book on the captured shelf."""
        shelf.add(book)

    place(books[0])
    place(books[-1])


def retry(times: int):
    def decorate(fn):  # expect: R72
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):  # expect: R72
            for _ in range(times - 1):
                try:
                    return fn(*args, **kwargs)
                except OSError:
                    continue
            return fn(*args, **kwargs)

        return wrapper

    return decorate


def mount(router, prefix: str) -> None:
    @router.get(prefix)
    async def recipes(request):  # expect-llm: R72
        """Serve recipes under the captured prefix; the router needs a bare callable."""
        return await request.app.recipes(prefix)
