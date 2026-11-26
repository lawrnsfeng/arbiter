order = (
    RecipeQuery(book).where("vegan", True)  # expect: R37
    .sort("title")
    .limit(10)
)

plan = (
    MealPlan(week)  # expect: R37
    .add("monday", soup)
    .add("tuesday", stew).add("wednesday", salad)
    .build()
)

label = (
    JarLabel(jar)  # expect: R37
    .text("plum jam")
    .size(12)
    .draw()
)


def shopping(pantry):
    return (
        ShoppingList(pantry).missing()  # expect: R37
        .group_by("aisle")
        .lines
    )
