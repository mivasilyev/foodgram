from backend.settings import AVATARS_URL

# Максимальная длина поля.
TAG_MAX_LENGTH = 32
SHORT_MAX_LENGTH = 64
MID_MAX_LENGTH = 128
MAX_LENGTH = 150
LONG_MAX_LENGTH = 254

# Размеры картинки для админки.
ADMIN_PIC_DOTS = 50

# Допустимые паттерны.
USERNAME_PATTERN = r'^[\w.@+-]+\Z'
# Аватар пользователя по умолчанию.
DEFAULT_USER_AVATAR = f'{AVATARS_URL}/default_user_avatar.jpg'
# Минимальное время готовки.
MIN_COOKING_MINUTES = 1
# Минимальное количество ингредиента.
MIN_INGREDIENT_AMOUNT = 1
# Имя файла для выгрузки списка покупок продуктов.
SHOPPING_CART_FILENAME = 'shopping_cart.txt'
