import functools
import json
from functools import lru_cache
from pathlib import Path

INVENTORY = Path("/srv/shared/inventory.json")
QUEUE = Path("/srv/shared/queue.txt")
_SNAPSHOT = None


@functools.cache
def inventory() -> dict[str, int]:  # expect: R21
    return json.loads(INVENTORY.read_text())


def current_stock() -> dict[str, int]:  # expect: R21
    global _SNAPSHOT
    if _SNAPSHOT is None:
        with open(INVENTORY) as fh:
            _SNAPSHOT = json.load(fh)
    return _SNAPSHOT


@lru_cache(maxsize=1)
def queue_depth() -> int:  # expect: R21
    with QUEUE.open() as fh:
        return len(fh.readlines())


ROSTER = json.loads(Path("/srv/shared/roster.json").read_text())  # expect-llm: R21


def on_duty(name: str) -> bool:
    return name in ROSTER


def low_stock(limit: int) -> list[str]:
    stock = json.loads(INVENTORY.read_text())
    total = sum(json.loads(INVENTORY.read_text()).values())  # expect-llm: R21
    return [item for item, count in stock.items() if count * 100 < total * limit]
