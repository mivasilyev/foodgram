import io
from datetime import datetime

from django.http import FileResponse

from constants import SHOPPING_CART_FILENAME


def shopping_list_render(recipe_qs, products_qs):
    """Получает сеты рецептов и продуктов и возвращает текстовый файл."""

    # Инициализируем буфер StringIO.
    buffer = io.StringIO()

    # Сохраняем данные списка покупок в буфер.
    buffer.write('СПИСОК ПОКУПОК\n')
    buffer.write(f'(составлен {datetime.now().date()})\n\n')
    pos_no = 1
    for position in products_qs:
        buffer.write(f'{pos_no}. {position["product"].capitalize()}, '
                     f'{position["unit"]} - {position["amount"]}\n')

        pos_no += 1

    # Сохраняем данные рецептов в буфер.
    buffer.write('\nРЕЦЕПТЫ\n')
    for recipe in recipe_qs:
        buffer.write(f'{recipe.name} от автора {recipe.author.username}\n')

    # Получаем буфер в переменную и закрываем.
    content = buffer.getvalue()
    buffer.close()

    # Отправляем файл пользователю.
    return FileResponse(
        content,
        as_attachment=True,
        filename=SHOPPING_CART_FILENAME
    )

    # # Reset the buffer's position to the beginning
    # buffer.seek(0)

    # # Read data from the buffer
    # print(buffer.read())

    # Предыдущий рабочий код.
    # response = HttpResponse(content_type='text/plain')
    # response.write('<p>Список покупок:</p><p></p>')
    # for position in products_qs:
    #     response.write(
    #         f'<p>{position["Продукт"]}, {position["мера"]} - '
    #         f'{position["Количество"]}</p>'
    #     )
    # response['Content-Disposition'] = 'attachment; filename={0}'.format(
    #     SHOPPING_CART_FILENAME
    # )
    # return response
