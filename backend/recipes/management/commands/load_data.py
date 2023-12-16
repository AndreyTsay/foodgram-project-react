import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('ingredients.json', 'rb') as f:
            data = json.load(f)
            for i in data:
                ingredient_name = i['name']
                measurement_unit = i['measurement_unit']

                existing_ingredient = Ingredient.objects.filter(
                    name=ingredient_name
                ).first()

                if existing_ingredient:
                    existing_ingredient.measurement_unit = measurement_unit
                    existing_ingredient.save()
                    print(f"Updated: {ingredient_name} - {measurement_unit}")
                else:
                    ingredient = Ingredient(
                        name=ingredient_name, measurement_unit=measurement_unit
                    )
                    ingredient.save()
                    print(f"Inserted: {ingredient_name} - {measurement_unit}")
