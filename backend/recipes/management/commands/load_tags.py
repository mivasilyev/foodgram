"""Команда загрузки тегов."""

from recipes.management.commands._load_data import CommonCommand
from recipes.models import Tag


class Command(CommonCommand):
    model = Tag
