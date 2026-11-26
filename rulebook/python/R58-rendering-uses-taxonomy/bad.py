import click
from rich.console import Console

console = Console()


def render_recipe_card(recipe) -> str:  # expect: R58
    with console.capture() as captured:
        console.rule(recipe.title)
        console.print(recipe.summary)
    return captured.get()


def _render_shopping_list(items):  # expect: R58
    return "\n".join(f"- {item}" for item in items)


async def render(menu):  # expect: R58
    console.print(menu.days)


def ingredient_table(recipe) -> str:  # expect-llm: R58
    with console.capture() as captured:
        console.print(recipe.ingredients)
    return captured.get()


@click.command()
@click.argument("week")
def render_week(week: str) -> None:  # expect: R58
    for day in load_menu(week).days:
        console.print(day.title)
        console.print(day.dishes)


@click.command()
@click.argument("week")
def render_plan(week: str) -> None:  # expect: R58
    console.print("\n".join(f"{day.name}: {day.dish}" for day in load_menu(week).days))
