from typing import Protocol, overload


class Oven(Protocol):
    def preheat(self, celsius: int) -> None: ...  # expect: R49

    def bake(self, minutes: int) -> str:
        """Bake for the given time and report the crust colour."""
        ...  # expect: R49


@overload
def scale(recipe: str, factor: int) -> str: ...  # expect: R49
@overload
def scale(recipe: list[str], factor: int) -> list[str]: ...  # expect: R49
def scale(recipe, factor):
    return recipe


def plate(dish):
    if dish.is_dessert:
        ...  # expect: R49
    return dish


def season(dish, salt=...):  # expect: R49
    return dish


FALLBACK_GARNISH = ...  # expect: R49
