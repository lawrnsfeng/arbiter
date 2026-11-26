from datetime import UTC, datetime


def _slug(title: str) -> str:
    """The title as a lowercase, hyphenated shelf key."""
    return title.strip().lower().replace(" ", "-")


def shelf_key(recipe, by_author: bool) -> str:
    if by_author:
        return recipe.author + "/" + _slug(recipe.title)
    return _slug(recipe.title)


def _lines(path) -> list[str]:
    """The recipe file's lines."""
    return path.read_text().splitlines()


def count_steps(path) -> int:
    return len(_lines(path))


def stamp(recipe) -> str:
    today = datetime.now(UTC).date()
    return f"{today}-{recipe.id}"


def headings(card) -> tuple[str, str]:
    return card.title.strip().lower(), card.title.strip().upper()
