label = JarLabel(jar).text("plum jam").size(12).draw()

order = RecipeQuery(book).where("vegan", True).where("course", "dessert").sort("title").limit(10).offset(page * 10)

plan = (
    MealPlan(week)
    .add("monday", "slow-cooked lentil soup with smoked paprika and lemon")
    .add("tuesday", "roasted root vegetable stew with rosemary dumplings")
    .add("wednesday", "charred corn salad with lime and chilli dressing")
    .build()
)

# look-alike: the head call's arguments are exploded, but no segment starts a new line
recipes = Recipe.objects.filter(
    course="dessert",
    vegan=True,
).order_by("title")

# look-alike: a dotted name with one call is not a chain
book.index.rebuild(force=True)
