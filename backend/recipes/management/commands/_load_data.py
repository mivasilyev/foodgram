import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction


class CommonCommand(BaseCommand):
    """Скрипт для загрузки данных."""

    help = ('Импортирует данные из CSV-файлов в модель.')

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = f'{settings.BASE_DIR}/{self.file_name}'
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                self.model.objects.bulk_create(
                    [
                        self.model(
                            number, *position
                        ) for number, position in enumerate(
                            csv.reader(csvfile), start=1
                        )
                    ]
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Файл {self.file_name} загружен.')
                )
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'Ошибка {error} при загрузке файла {self.file_name}.'
                )
            )
