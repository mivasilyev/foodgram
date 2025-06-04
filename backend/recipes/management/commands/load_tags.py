"""Команда загрузки тегов."""

from constants import TAGS
from recipes.management.commands._load_data import CommonCommand
from recipes.models import Tag


class Command(CommonCommand):
    help = "Импортирует данные из CSV-файла tags.csv в базу данных."
    file_name = TAGS
    model = Tag
