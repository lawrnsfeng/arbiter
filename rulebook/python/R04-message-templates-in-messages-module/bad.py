from string import Template

MISSING_TEMPLATE = Template("recipe $name has no $part")  # expect: R4


class RecipeError(Exception):
    pass


class MissingStepError(RecipeError):
    def __init__(self, recipe, step):
        super().__init__(  # expect: R4
            f"recipe {recipe.title!r} is missing step {step}.\n"
            f"steps present: {recipe.steps}\n"
            "add the step or renumber the others"
        )


def scale(recipe, servings):
    if servings <= 0:
        lines = "\n".join([f"cannot scale {recipe.title}", f"servings: {servings}"])  # expect: R4
        raise RecipeError(lines)
    return recipe.scaled(servings)


def check_oven(temperature):
    if temperature > 300:
        raise RecipeError(  # expect: R4
            f"""oven too hot: {temperature}
            lower it below 300"""
        )


def explain_substitution(ingredient, swap):
    print(f"{ingredient} is unavailable.\nUse {swap} instead.\nAdjust the quantity.")  # expect-llm: R4
