# import inspect
# import re

from django.contrib.auth import get_user_model
# from django.core.exceptions import ValidationError
# from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer  # UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

# from api.pagination import RecipePagination
# from constants import FORBIDDEN_NAMES, MAX_LENGTH, USERNAME_PATTERN
from recipes.models import (Ingredient, IngredientInRecipe, Recipe,
                            Subscribe, Tag)

User = get_user_model()


# class AddValidationUserCreateSerializer(UserCreateSerializer):
#     """Доработанный сериализатор djoser для создания новых пользователей."""
#     # Исходный сериализатор не подходит, т.к. не обеспечивает требуемую
#     # валидацию на запрещенные имена.

#     class Meta:
#         model = User
#         fields = (
#             'email', 'id', 'username', 'first_name', 'last_name', 'password'
#         )

#     def validate_username(self, value):
#         if value in FORBIDDEN_NAMES:
#             raise ValidationError(
#                 f'Имя пользователя {value} не разрешено.'
#             )
#         if not re.fullmatch(USERNAME_PATTERN, value):
#             raise ValidationError(
#                 'Имя пользователя может содержать буквы, цифры и знаки '
#                 '@/./+/-/_.'
#             )
#         if len(value) > MAX_LENGTH:
#             raise ValidationError(
#                 'В имени пользователя должно быть не более '
#                 f'{MAX_LENGTH} символов.'
#             )
#         return value


class ExtendedUserSerializer(UserSerializer):
    """Доработанный сериализатор djoser для пользователей."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('is_subscribed', 'avatar')

    def get_is_subscribed(self, author):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return user.follows.filter(subscribed=author).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для продуктов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели связи рецептов и продуктов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', required=False)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', required=False
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        read_only_fields = ('id', 'name', 'measurement_unit',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для сокращенного отображения рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = ('id', 'name', 'image', 'cooking_time',)


class GetRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для полного отображения рецептов."""

    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField()
    author = ExtendedUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = fields

    def get_is_favorited(self, recipe):
        request = self.context.get('request')
        return (
            bool(request)
            and request.user.is_authenticated
            and recipe.favorites.filter(user=request.user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        request = self.context.get('request')
        return (
            bool(request)
            and request.user.is_authenticated
            and recipe.shopping_ingredients.filter(user=request.user).exists()
        )


class RecipeSerializer(serializers.ModelSerializer):
    """Модификация сериализатора для сохранения рецептов."""

    ingredients = IngredientInRecipeSerializer(many=True)
    image = Base64ImageField()
    author = ExtendedUserSerializer(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time'
        )
        read_only_fields = ('author',)

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать продукты.'
            )
        duplicated_ingredients = []
        ingredient_ids = []
        for ingredient in ingredients:
            id = ingredient['ingredient']['id']
            if not Ingredient.objects.filter(id=id).exists():
                raise serializers.ValidationError(
                    f'Продукта {ingredient} нет в списке.'
                )
            if id in ingredient_ids:
                duplicated_ingredient = Ingredient.objects.get(id=id)
                duplicated_ingredients.append(duplicated_ingredient.name)
            ingredient_ids.append(id)

        if duplicated_ingredients:
            raise serializers.ValidationError(
                'Продукты не должны повторяться. В рецепте повторяются '
                f'{", ".join(duplicated_ingredients)}.'
            )
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Рецепт должен иметь хотя бы один тег.'
            )

        duplicated_tags = []
        tag_ids = []
        for tag in tags:
            if tag.id in tag_ids:
                duplicated_tags.append(tag.name)
            tag_ids.append(tag.id)

        if duplicated_tags:
            raise serializers.ValidationError(
                'Теги не должны повторяться. В рецепте повторяются '
                f'{", ".join(duplicated_tags)}'
            )

        return tags

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError(
                'В рецепте должна быть картинка.'
            )
        return value

    def validate(self, data):
        if 'image' not in data:
            raise serializers.ValidationError(
                'В рецепте должна быть картинка.'
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                'В рецепте должны быть теги.'
            )
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                'В рецепте нужны продукты.'
            )
        return data

    def fill_ingredients(self, recipe, ingredients):
        """Заполняем ингредиенты в рецепт."""
        # Устанавливаем связи с продуктами.
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_list.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=Ingredient.objects.get(
                        id=ingredient['ingredient']['id']),
                    amount=ingredient['amount']
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredient_list)

    def create(self, validated_data):
        # Создаем рецепт.
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.fill_ingredients(recipe, ingredients)
        # Устанавливаем связи с тегами.
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        super().update(instance=instance, validated_data=validated_data)
        # Устанавливаем новые теги.
        instance.tags.set(tags)
        # Переформатируем новые продукты в словарь.
        new_ingredients = {}
        for ingr in ingredients:
            new_ingredients[ingr['ingredient']['id']] = ingr['amount']
        # Перезаписываем продукты, которые уже были в списке.
        instance.ingredients.all().delete()
        self.fill_ingredients(recipe=instance, ingredients=ingredients)
        return instance


class SubscribeUserSerializer(ExtendedUserSerializer):
    """Сериализатор для подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ExtendedUserSerializer.Meta.fields + (
            'recipes', 'recipes_count')

    def get_recipes(self, author):
        # Вывод рецептов для пользователя делаем через кастомный пагинатор
        # для ограничения количества рецептов в выдаче.
        # paginator = RecipePagination()
        # result_page = paginator.paginate_queryset(
        #     recipes, self.context['request']
        # )
        recipes = author.recipes.all()[:1]
        serializer = ShortRecipeSerializer(
            # result_page,
            recipes,
            many=True,
            context={'request': self.context['request']}
        )
        return serializer.data

    def get_recipes_count(self, author):
        return author.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор для записи подписки."""

    class Meta:
        model = Subscribe
        fields = '__all__'
        validators = [
            UniqueTogetherValidator(
                queryset=Subscribe.objects.all(),
                fields=['user', 'subscribed']
            )
        ]
