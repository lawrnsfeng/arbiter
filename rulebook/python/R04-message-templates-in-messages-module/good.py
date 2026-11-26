"""Recipe errors: wording lives in recipebook.messages, constructors fill it."""

from recipebook.constants import MAX_OVEN_CELSIUS
from recipebook.messages import MISSING_STEP, OVEN_TOO_HOT


class RecipeError(Exception):
    pass


class MissingStepError(RecipeError):
    def __init__(self, recipe, step):
        super().__init__(MISSING_STEP.substitute(title=recipe.title, step=step, present=recipe.steps))


class OvenTooHotError(RecipeError):
    def __init__(self, temperature):
        super().__init__(OVEN_TOO_HOT.substitute(temperature=temperature))


def check_oven(temperature):
    if temperature > MAX_OVEN_CELSIUS:
        raise OvenTooHotError(temperature)


def render_card(recipe):
    """Render the card.

    One line per step.
    """
    return "\n".join([recipe.title, *recipe.steps])


def find_by_tag(cursor, tag):
    cursor.execute(
        """
        select title from recipes
        where tag = ?
        """,
        (tag,),
    )
    return cursor.fetchall()


def require_title(recipe):
    if not recipe.title:
        raise RecipeError("a recipe needs a title")
