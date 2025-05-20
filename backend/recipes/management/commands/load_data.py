import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from constants import DATA_FILES_CSV, INGREDIENTS, TAGS
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Скрипт для загрузки данных."""

    help = ('Импортирует данные из CSV-файлов ingredients.csv, tags.csv в '
            'модель.')

    @transaction.atomic
    def handle(self, *args, **options):
        counter_models = 0
        for file_name in DATA_FILES_CSV:
            file_path = f'{settings.BASE_DIR}/{file_name}'
            counter_positiions = 0
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                csvreader = csv.reader(csvfile)
                for row in csvreader:
                    if file_name == INGREDIENTS:
                        name, measurement_unit = row
                        Ingredient.objects.update_or_create(
                            name=name, measurement_unit=measurement_unit
                        )
                    if file_name == TAGS:
                        name, slug = row
                        Tag.objects.update_or_create(
                            name=name, slug=slug
                        )
                    counter_positiions += 1
                counter_models += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Файл {file_name}. Загружено позиций:'
                                       f' {counter_positiions}.')
                )
        self.stdout.write(
            self.style.SUCCESS(
                f'Загрузка завершена. Файлов загружено: {counter_models}'
            )
        )
