from dataclasses import dataclass


@dataclass
class Recipe:
    title: str
    ingredients: list[str]
    garnish: list[str]
    servings: int


@dataclass(frozen=True)
class Shelf:
    label: str
    capacity: int


def _all_items(recipe):  # expect: R78
    return [*recipe.ingredients, *recipe.garnish]


def _scaled_servings(recipe: Recipe, factor: float) -> int:  # expect: R78
    return round(recipe.servings * factor)


def _shopping_cost(recipe: Recipe, prices: dict[str, float]) -> float:  # expect: R78
    return sum(prices.get(item, 0.0) for item in recipe.ingredients)


def _shelf_from_row(row: dict) -> Shelf:  # expect: R78
    if "cap" in row:
        return Shelf(row["name"], int(row["cap"]))
    return Shelf(row["name"], 10)


def _slug(text: str) -> str:  # expect: R78
    return "-".join(text.lower().split())


class Cookbook:
    def __init__(self, recipes: list[Recipe]) -> None:
        self.recipes = recipes

    def anchors(self) -> list[str]:
        return [_slug(r.title) for r in self.recipes]


def _card_header(title: str) -> str:  # expect-llm: R78
    return f"== {title.upper()} =="


def _card_line(item: str, qty: str) -> str:  # expect-llm: R78
    return f"  {qty:>6}  {item}"


def _is_metric(unit: str) -> bool:  # expect-llm: R78
    return unit in {"g", "kg", "ml", "l"}


# one return builds Shelf, the other delegates: not tell (c), but still no stated reason
def _shelf_or_default(row: dict | None) -> Shelf:  # expect-llm: R78
    if row is None:
        return default_shelf()
    return Shelf(row["name"], 10)


def build(rows: list[dict], recipe: Recipe) -> tuple[list[Shelf], list[str]]:
    return [_shelf_from_row(r) for r in rows], _all_items(recipe)
