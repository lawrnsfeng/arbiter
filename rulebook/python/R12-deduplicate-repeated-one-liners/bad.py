from datetime import UTC, datetime


def shelf_key(recipe, by_author):
    if by_author:
        return recipe.author + "/" + recipe.title.strip().lower().replace(" ", "-")  # expect: R12
    return recipe.title.strip().lower().replace(" ", "-")  # expect: R12


def count_steps(path):
    return len(path.read_text().splitlines())  # expect: R12


def last_step(path):
    return path.read_text().splitlines()[-1]  # expect: R12


def stamp(recipe):
    return f"{datetime.now(UTC).date()}-{recipe.id}-{datetime.now(UTC).date()}"  # expect: R12


def tag_of(dish):
    return dish.label.strip().upper()  # expect-llm: R12


def tag_of_menu(menu):
    return menu.label.strip().upper()  # expect-llm: R12


def portions(recipe):
    per_serving = recipe.grams / recipe.serves  # expect-llm: R12
    return per_serving, recipe.grams / recipe.serves * 2  # expect-llm: R12
