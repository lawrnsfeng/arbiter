from enum import StrEnum, auto


class BookFormat(StrEnum):
    HARDCOVER = auto()
    PAPERBACK = auto()
    EBOOK = auto()


class Medium(StrEnum):
    AUDIO = auto()
    PRINT = auto()


def shelf_for(medium: Medium) -> str:
    return "listening corner" if medium is Medium.AUDIO else "stacks"


# Look-alikes: single settings, and values that are not part of the name.
CACHE_DIR = "cache"
API_VERSION = "v2"
DEFAULT_FORMAT = "hardcover"
FALLBACK_FORMAT = "paperback"
