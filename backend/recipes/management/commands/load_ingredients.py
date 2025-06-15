"""Команда загрузки ингредиентов."""

from recipes.management.commands._load_data import CommonCommand
from recipes.models import Ingredient


class Command(CommonCommand):
    model = Ingredient
