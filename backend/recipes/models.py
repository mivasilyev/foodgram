from django.contrib.auth import get_user_model
# from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
# from django.utils.text import Truncator

User = get_user_model()


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(verbose_name='Тег', max_length=150, unique=True)
    slug = models.SlugField(
        verbose_name='Идентификатор', max_length=100, unique=True
    )

    class Meta:
        default_related_name = 'tags'
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


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
        return self.name


class Recipe(models.Model):
    """Модель рецепта."""

    author = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name='author',
        verbose_name='Автор'
    )
    name = models.CharField(max_length=150, verbose_name='Название')
    image = models.ImageField(
        blank=True, upload_to='recipe_images', verbose_name='Изображение'
    )
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe'
        # through_fields=('ingredient', 'recipe'),
    )
    tags = models.ManyToManyField(Tag)
    cooking_time = models.SmallIntegerField(verbose_name='Время приготовления')
    favorite = models.ManyToManyField(User, related_name='favorite')

    class Meta:
        default_related_name = 'recipes'
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Ингредиенты в рецепте."""

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    amount = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name = 'ингредиенты в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            # Ингредиент входит в рецепт один раз.
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_in_recipe'
            )
        ]

    def __str__(self):
        return self.amount


# class TagRecipe(models.Model):
#     """Связь рецептов и тегов."""

#     recipe = models.ForeignKey(
#         Recipe, on_delete=models.CASCADE, verbose_name='Рецепт'
#     )
#     tag = models.ForeignKey(
#         Tag, on_delete=models.CASCADE, verbose_name='Тег'
#     )

#     class Meta:
#         verbose_name = 'рецепт - тег'
#         verbose_name_plural = 'Рецепты - теги'
#         default_related_name = 'recipes_tags'

#     def __str__(self):
#         return f'{self.recipe.title} - {self.tag.name}'


# class Favorite(models.Model):
#     """Добавление рецептов в избранное."""

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         verbose_name='Пользователь'
#     )
#     recipe = models.ForeignKey(
#         Recipe,
#         on_delete=models.CASCADE,
#         verbose_name='Избранное'
#     )

#     class Meta:
#         verbose_name = 'избранное'
#         verbose_name_plural = 'Избранное'
#         default_related_name = 'favorite'
#         constraints = [
#             # Запрещено повторное добавление в избранное.
#             models.UniqueConstraint(
#                 fields=['user', 'recipe'],
#                 name='unique_favorite'
#             )
#         ]

#     def __str__(self):
#         return f'{self.user.username} - {self.recipe.title}'


# class ShoppingCart(models.Model):
#     """Добавление рецептов в список покупок."""

#     user = models.ForeignKey(
#         User, on_delete=models.CASCADE,
#         related_name='cart', verbose_name='Пользователь')
#     in_cart = models.ForeignKey(
#         Recipe, on_delete=models.CASCADE,
#         related_name='cart', verbose_name='Корзина'
#     )

#     class Meta:
#         verbose_name = 'корзина'
#         verbose_name_plural = 'Корзины'
#         default_related_name = 'in_cart'
#         constraints = [
#             # Запрещено повторное добавление в корзину.
#             models.UniqueConstraint(
#                 fields=['user', 'in_cart'],
#                 name='unique_in_cart'
#             )
#         ]

#     def __str__(self):
#         return f'{self.user.username} - {self.in_cart.title}'
