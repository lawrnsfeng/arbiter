import fcntl
import json
from functools import cache
from pathlib import Path

UNITS_FILE = "units.json"
INVENTORY = Path("/srv/shared/inventory.json")


def load_inventory() -> dict[str, int]:
    return json.loads(INVENTORY.read_text())


def restock(item: str, amount: int) -> None:
    # Re-read under the lock: the read-modify-write must be atomic.
    with INVENTORY.open("r+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        stock = json.load(fh)
        stock[item] = stock.get(item, 0) + amount
        fh.seek(0)
        fh.truncate()
        json.dump(stock, fh)


def report() -> str:
    stock = load_inventory()
    return ", ".join(f"{k}={v}" for k, v in sorted(stock.items()))


# Look-alikes: a pure function and package data no other process writes.
@cache
def unit_factor(unit: str) -> float:
    return {"g": 1.0, "kg": 1000.0}[unit]


@cache
def unit_table() -> dict[str, float]:
    return json.loads((Path(__file__).parent / UNITS_FILE).read_text())
