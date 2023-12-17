import csv
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт данных из csv для модели Ingredients.'

    def handle(self, *args, **options):
        file_path = os.fspath('data/ingredients.csv')
        with open(file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            try:
                Ingredient.objects.bulk_create([Ingredient(
                    name=name, measurement_unit=measurement_unit)
                    for name, measurement_unit in reader])
            except Exception as error:
                print(f'Ошибка:{error}')
