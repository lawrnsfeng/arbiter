FORMAT_HARDCOVER = "hardcover"  # expect: R23
FORMAT_PAPERBACK = "paperback"  # expect: R23
FORMAT_EBOOK = "ebook"  # expect: R23

DAILY_REPORT = "daily"  # expect: R23
WEEKLY_REPORT = "weekly"  # expect: R23

AUDIO_MEDIUM = "audio"  # expect-llm: R23


def shelf_for(medium: str) -> str:
    if medium == AUDIO_MEDIUM:
        return "listening corner"
    return "stacks"


def needs_fee(status: str) -> bool:
    return status == "lost" or status == "damaged"  # expect-llm: R23
