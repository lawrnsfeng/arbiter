import typing
import typing as t
from typing import Any
from typing import Any as Anything
from typing import cast

Row = dict[str, Any]  # expect: R11


def parse_recipe(blob: Any) -> Any:  # expect: R11
    return blob


def cook(recipe: typing.Any) -> None:  # expect: R11
    recipe.bake()


def scale(amounts: Anything, factor: float) -> list[float]:  # expect: R11
    return [a * factor for a in amounts]


pantry: dict[str, list[t.Any]] = {}  # expect: R11
steps = cast(Any, load_steps())  # expect: R11
