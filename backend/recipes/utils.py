from .models import IngredientsForRecipe


def bulk_create_ingredients_for_recipe(recipe, ingredients_data):
    ingredients_for_recipe_objects = [
        IngredientsForRecipe(
            ingredient_id=ingredient['id'],
            recipe=recipe,
            amount=ingredient['amount']
        )
        for ingredient in ingredients_data
    ]

    IngredientsForRecipe.objects.bulk_create(ingredients_for_recipe_objects)
