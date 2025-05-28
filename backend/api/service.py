from datetime import datetime


def shopping_list_render(recipe_qs, products_qs):
    """Получает сеты рецептов и продуктов и возвращает список покупок."""

    products = [
        (f'{number}. {position["product"].capitalize()} ({position["unit"]}) '
         f'- {position["amount"]}') for number, position in enumerate(
             products_qs, start=1)
    ]
    recipes = [
        (f'{recipe.name} от автора {recipe.author.username}'
         ) for recipe in recipe_qs
    ]

    return '\n'.join([
        'СПИСОК ПОКУПОК',
        f'(составлен {datetime.now().date()})',
        '\n',
        'ПРОДУКТЫ:',
        *products,
        '\n',
        'ДЛЯ РЕЦЕПТОВ:',
        *recipes,
    ])
