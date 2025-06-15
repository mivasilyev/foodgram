# import csv
import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

# from recipes.models import Ingredient, Tag


class CommonCommand(BaseCommand):
    """Скрипт для загрузки данных."""

    @property
    def help(self):
        return ('Импортирует данные из JSON в модель '
                f'{self.model._meta.verbose_name_plural}.')


    @transaction.atomic
    def handle(self, *args, **options):
        file_name = f'{self.model.__name__.lower()}s.json'
        file_path = f'{settings.BASE_DIR}/{file_name}'
        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:  # csvfile
                data = json.load(jsonfile)
                self.model.objects.bulk_create(
                    (self.model(**item) for item in data),
                    ignore_conflicts=True
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Файл {file_name} загружен. '
                        f'Добавлено {len(data)} записей.'
                    )
                )
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка {error} при загрузке файла {file_name}.'
                )
            )

                # self.model.objects.bulk_create(
                #     [
                #         self.model(
                #             number, *position
                #         ) for number, position in enumerate(
                #             csv.reader(csvfile), start=1
                #         )
                #     ]
                # )