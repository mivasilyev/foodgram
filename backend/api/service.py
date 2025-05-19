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

# from django.http import FileResponse
# from constants import SHOPPING_CART_FILENAME

# def shopping_list_render(recipe_qs, products_qs):
#     """Получает сеты рецептов и продуктов и возвращает текстовый файл."""

#     # Инициализируем буфер StringIO.
#     buffer = io.StringIO()

#     # Сохраняем данные списка покупок в буфер.
#     buffer.write('СПИСОК ПОКУПОК\n')
#     buffer.write(f'(составлен {datetime.now().date()})\n\n')
#     pos_no = 1
#     for position in products_qs:
#         buffer.write(f'{pos_no}. {position["product"].capitalize()}, '
#                      f'{position["unit"]} - {position["amount"]}\n')
#         pos_no += 1
#     # Сохраняем данные рецептов в буфер.
#     buffer.write('\nРЕЦЕПТЫ\n')
#     for recipe in recipe_qs:
#         buffer.write(f'{recipe.name} от автора {recipe.author.username}\n')

#     # Получаем буфер в переменную и закрываем.
#     content = buffer.getvalue()
#     buffer.close()

#     # Отправляем файл пользователю.
#     return FileResponse(
#         content,
#         content_type='text/plain',
#         as_attachment=True,
#         filename=SHOPPING_CART_FILENAME
#     )
