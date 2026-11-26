from dataclasses import dataclass
from typing import Self

import click

from jinja2 import Environment, PackageLoader

templates = Environment(loader=PackageLoader("cookbook"))
WEEKLY_MENU = templates.get_template("weekly_menu.html.j2")  # a long page a human edits: a template file


class RecipeCard(str):
    """A trivial rendering with a string result: a str subclass built from its ingredients.

    >>> RecipeCard.from_recipe("Lentil soup", 40)
    'Lentil soup (40 min)'
    """

    @classmethod
    def from_recipe(cls, title: str, minutes: int) -> Self:
        return cls(f"{title} ({minutes} min)")


class MenuRenderer:
    """Many things rendered with the same configuration."""

    def __init__(self, width: int) -> None:
        self.width = width

    def render(self, menu) -> str:  # a method, not a loose function
        return "\n".join(day.ljust(self.width) for day in menu.days)


@dataclass
class Ingredient:
    name: str
    grams: int

    @property
    def label(self) -> str:  # effectively this class's repr: a property of it
        return f"{self.grams} g {self.name}"


def renderable(menu) -> bool:  # `renderable`, not `render_`: a check, not a rendering
    return bool(menu.days)


@click.command()
@click.argument("week")
def render(week: str) -> None:  # a CLI entry point that only calls a renderer
    click.echo(MenuRenderer(width=20).render(load_menu(week)))


@click.command()
@click.argument("week")
@click.argument("margin", type=int)
def render_wide(week: str, margin: int) -> None:  # integer arithmetic in the hand-over is not text building
    click.echo(MenuRenderer(width=margin + 20).render(load_menu(week)))
