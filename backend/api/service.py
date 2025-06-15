from datetime import datetime


def shopping_list_render(recipes, products):
    """Получает сеты рецептов и продуктов и возвращает список покупок."""

    products = [
        (f'{number}. {position["product"].capitalize()} ({position["unit"]}) '
         f'- {position["amount"]}') for number, position in enumerate(
             products, start=1)
    ]
    recipes = [
        (f'{recipe.name} от автора {recipe.author.username}'
         ) for recipe in recipes
    ]

    return '\n'.join([
        f'СПИСОК ПОКУПОК (составлен {datetime.now().date()})',
        'ПРОДУКТЫ:',
        *products,
        'ДЛЯ РЕЦЕПТОВ:',
        *recipes,
    ])
