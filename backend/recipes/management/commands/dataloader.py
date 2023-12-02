import csv

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

DATA = {Ingredient: 'ingredients.csv'}


class Command(BaseCommand):
    help = 'Import data from file to DB'

    def import_data_from_csv_file(self):
        for model, csv_file in DATA.items():
            with open(
                    f'{settings.BASE_DIR}/data/{csv_file}',
                    'r',
                    encoding='utf-8',
            ) as file:
                reader = csv.DictReader(file)
                objects_to_create = []
                for data in reader:
                    objects_to_create.append(
                        model(
                            name=data['name'],
                            measurement_unit=data['measurement_unit']
                        )
                    )
                model.objects.bulk_create(objects_to_create)
        self.stdout.write(self.style.SUCCESS('Successfully loaded data'))

    def handle(self, *args, **options):
        self.import_data_from_csv_file()
