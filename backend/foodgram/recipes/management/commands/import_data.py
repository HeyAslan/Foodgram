import csv
import os

from django.core.management.base import BaseCommand, CommandError
from recipes.models import Ingredient


class Command(BaseCommand):
    help = ('Import ingredients data from CSV file to DB')    

    def handle(self, *args, **options):
        file_path = 'recipes/data/ingredients.csv'

        try:
            with open(file_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    name, unit = row
                    Ingredient.objects.get_or_create(name=name, measurement_unit=unit)
        except FileNotFoundError:
            raise CommandError(f'{file_path} file does not exist')
        except Exception as e:
            raise CommandError(f'Data import failed: {e}')

        self.stdout.write(self.style.SUCCESS('Ingredients successfully imported.'))
