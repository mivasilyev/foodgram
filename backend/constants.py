from backend.settings import AVATARS_URL

# Максимальная длина поля.
TAG_MAX_LENGTH = 32
SHORT_MAX_LENGTH = 64
MID_MAX_LENGTH = 128
MAX_LENGTH = 150
LONG_MAX_LENGTH = 254

# Размеры картинки для админки.
ADMIN_PIC_DOTS = 50

# Список запрещенных имен пользователя.
# FORBIDDEN_NAMES = ['me', ]

# Допустимые паттерны.
USERNAME_PATTERN = r'^[\w.@+-]+\Z'
# TAG_PATTERN = r'^[-a-zA-Z0-9_]+$'
# Аватар пользователя по умолчанию.
# DEFAULT_USER_AVATAR = 'user_avatars/default_user_avatar.jpg'
DEFAULT_USER_AVATAR = f'{AVATARS_URL}/default_user_avatar.jpg'
# Минимальное время готовки.
MIN_COOKING_MINUTES = 1
# Минимальное количество ингредиента.
MIN_INGREDIENT_AMOUNT = 1
# Имя файла для выгрузки списка покупок продуктов.
SHOPPING_CART_FILENAME = 'shopping_cart.txt'

# Где лежат файлы с заполнением БД.
# STATIC_PATH = '/static/data/'

INGREDIENTS = 'ingredients.csv'
TAGS = 'tags.csv'

DATA_FILES_CSV = [
    INGREDIENTS,
    TAGS,
]
