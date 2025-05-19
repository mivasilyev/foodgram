from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from constants import (
    DEFAULT_USER_AVATAR, LONG_MAX_LENGTH, MAX_LENGTH, MID_MAX_LENGTH,
    MIN_COOKING_MINUTES, MIN_INGREDIENT_AMOUNT, SHORT_MAX_LENGTH,
    TAG_MAX_LENGTH, USERNAME_PATTERN  # TAG_PATTERN
)
from backend.settings import AVATARS_URL


class User(AbstractUser):
    """Кастомная модель пользователя."""

    email = models.CharField(
        verbose_name='Адрес электронной почты',
        max_length=LONG_MAX_LENGTH,
        unique=True
    )
    username = models.CharField(
        verbose_name='Уникальный юзернейм',
        max_length=MAX_LENGTH,
        unique=True,
        validators=(RegexValidator(regex=USERNAME_PATTERN), )
    )
    first_name = models.CharField(verbose_name='Имя', max_length=MAX_LENGTH)
    last_name = models.CharField(verbose_name='Фамилия', max_length=MAX_LENGTH)
    avatar = models.ImageField(
        verbose_name='Ссылка на аватар',
        # upload_to='user_avatars',
        upload_to=AVATARS_URL,
        blank=True,
        default=DEFAULT_USER_AVATAR
    )
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name', ]
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username', )

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    """Модель подписки пользователей друг на друга."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follows',
        verbose_name='Пользователь'
    )
    subscribed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подписан на'
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            # Запрещена повторная подписка.
            models.UniqueConstraint(
                fields=['user', 'subscribed'],
                name='unique_subscription'
            ),
            # Запрещена подписка на себя.
            models.CheckConstraint(
                check=~models.Q(user=models.F('subscribed')),
                name='self_subscription'
            )
        ]

    def __str__(self):
        return f'{self.user} на {self.subscribed}'


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Уникальное название',
        max_length=TAG_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        verbose_name='Уникальный слаг',
        max_length=TAG_MAX_LENGTH,
        unique=True,
        # validators=(RegexValidator(regex=TAG_PATTERN), )
    )

    class Meta:
        default_related_name = 'tags'
        verbose_name = 'тег'
        verbose_name_plural = 'Список тегов'
        ordering = ('name', )

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Продукты."""

    name = models.CharField(
        max_length=MID_MAX_LENGTH, verbose_name='Название', unique=True
    )
    measurement_unit = models.CharField(
        max_length=SHORT_MAX_LENGTH, verbose_name='Мера', blank=True
    )

    class Meta:
        default_related_name = 'ingredient'
        verbose_name = 'продукт'
        verbose_name_plural = 'Список продуктов'
        ordering = ('name', )
        constraints = [
            # Ингредиент записан один раз.
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_in_ingredients'
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=LONG_MAX_LENGTH, verbose_name='Название'
    )
    image = models.ImageField(
        upload_to='recipe_images', verbose_name='Ссылка на картинку на сайте'
    )
    text = models.TextField(verbose_name='Описание')
    tags = models.ManyToManyField(Tag, verbose_name='Список тегов')
    cooking_time = models.SmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(MIN_COOKING_MINUTES)]
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Продукты в рецепте."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Продукт'
    )
    amount = models.FloatField(
        verbose_name='Мера',
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)]
    )

    class Meta:
        verbose_name = 'продукты в рецепте'
        verbose_name_plural = 'Продукты в рецепте'
        default_related_name = 'ingredients'
        ordering = ('ingredient__name', )
        constraints = [
            # Продукт входит в рецепт один раз.
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_in_recipe'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')


class BaseCart(models.Model):
    """Базовый класс для избранного и корзины."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [
            # Запрещено повторное добавление.
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_in_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class Favorite(BaseCart):
    """Добавление рецептов в избранное."""

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'


class ShoppingCart(BaseCart):
    """Добавление рецептов в список покупок."""

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'Корзины'
        default_related_name = 'shopping_ingredients'
