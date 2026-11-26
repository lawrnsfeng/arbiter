import json
from pathlib import Path


def ledger_size(path: str) -> int:
    with open(path) as fh:
        ledger = json.load(fh)
    return len(ledger)


def card_title(card: Path) -> str:
    card_text = card.read_text()
    return card_text.splitlines()[0]


class Pantry:
    ingredients: list[str]
    metadata: dict[str, str]
    table_of_contents: list[str]

    def __init__(self) -> None:
        self.stock: dict[str, int] = {}


# Look-alikes: a keyword argument and an attribute read are not bindings.
def upload(client, recipe: dict[str, str]) -> int:
    response = client.post("/recipes", data=recipe)
    return len(response.data)
