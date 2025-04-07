from django.contrib.auth import get_user_model
from django.db import models
from django.utils.text import Truncator

from constants import MAX_LENGTH, SHORT_LINK_LENGTH, WORDS_TRUNCATE

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Тег', max_length=MAX_LENGTH, unique=True
    )
    slug = models.SlugField(
        verbose_name='Идентификатор', max_length=MAX_LENGTH, unique=True
    )

    class Meta:
        default_related_name = 'tags'
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return Truncator(self.name).words(WORDS_TRUNCATE)


class Ingredient(models.Model):
    """Ингредиенты."""

    name = models.CharField(
        max_length=64, verbose_name='Название', unique=True
    )
    measurement_unit = models.CharField(
        max_length=64, verbose_name='Единица измерения', blank=True
    )

    class Meta:
        default_related_name = 'ingredients'
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return Truncator(self.name).words(WORDS_TRUNCATE)


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        verbose_name='Автор'
    )
    name = models.CharField(max_length=150, verbose_name='Название')
    image = models.ImageField(
        blank=True, upload_to='recipe_images', verbose_name='Изображение'
    )
    text = models.TextField(verbose_name='Описание')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.SmallIntegerField(verbose_name='Время приготовления')
    is_favorited = models.ManyToManyField(
        User, through='Favorite', related_name='is_favorited', blank=True
    )
    is_in_shopping_cart = models.ManyToManyField(
        User, through='ShoppingCart', related_name='is_in_shopping_cart',
        blank=True
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name='Дата публикации'
    )
    short_link = models.CharField(
        max_length=SHORT_LINK_LENGTH,
        unique=True,
        verbose_name='Короткая ссылка'
    )

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return Truncator(self.name).words(WORDS_TRUNCATE)


class Ingredients(models.Model):
    """Ингредиенты в рецепте."""

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name='Ингредиент'
    )
    amount = models.FloatField(verbose_name='Количество')

    class Meta:
        verbose_name = 'ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        default_related_name = 'ingredients'
        constraints = [
            # Ингредиент входит в рецепт один раз.
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_in_recipe'
            )
        ]

    def __str__(self):
        return (f'{self.ingredient.name} - {self.amount} '
                f'{self.ingredient.measurement_unit}')


class Favorite(models.Model):
    """Добавление рецептов в избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Избранное'
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorite'
        constraints = [
            # Запрещено повторное добавление в избранное.
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingCart(models.Model):
    """Добавление рецептов в список покупок."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='cart', verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        related_name='cart', verbose_name='Корзина'
    )

    class Meta:
        verbose_name = 'корзина'
        verbose_name_plural = 'Корзины'
        default_related_name = 'shopping_cart'
        constraints = [
            # Запрещено повторное добавление в корзину.
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_in_cart'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.title}'
