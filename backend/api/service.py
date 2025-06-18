import locale
from datetime import datetime

from constants import header_layout, products_layout, recipes_layout


def shopping_list_render(recipes, products):
    """Получает сеты рецептов и продуктов и возвращает список покупок."""

    locale.setlocale(locale.LC_ALL, 'ru_RU.utf8')

    return '\n'.join([
        header_layout.format(datetime.now().date().strftime("%d %B %Y")),
        'ПРОДУКТЫ:',
        *[
            products_layout.format(
                number,
                position["product"].capitalize(),
                position["unit"],
                position["amount"]
            ) for number, position in enumerate(products, start=1)
        ],
        'ДЛЯ РЕЦЕПТОВ:',
        *[
            recipes_layout.format(
                recipe.name,
                recipe.author.username
            ) for recipe in recipes
        ],
    ])
