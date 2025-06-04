"""Команда загрузки ингредиентов."""

from constants import INGREDIENTS
from recipes.management.commands._load_data import CommonCommand
from recipes.models import Ingredient


class Command(CommonCommand):
    help = "Импортирует ингредиенты из CSV-файла в базу данных."
    file_name = INGREDIENTS
    model = Ingredient
