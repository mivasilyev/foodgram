import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import (Ingredient, Recipe, IngredientRecipe,
                            Tag, User)


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор djoser для создания новых пользователей с доп. полями."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password')


class CustomUserSerializer(UserSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )


class Base64ImageField(serializers.ImageField):
    """Сериализатор для обработки избображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.Serializer):

    # id = serializers.IntegerField()

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug', 'recipes')


# class IngredientSerializer(serializers.ModelSerializer):
#     """Сериализатор для ингредиентов."""

#     class Meta:
#         model = Ingredient
#         fields = ('id', 'name', 'measurement_unit')


# class RecipeSerializer(serializers.ModelSerializer):
#     """Сериализатор для рецептов."""

#     ingredients = IngredientSerializer(read_only=True, many=True)

#     class Meta:
#         model = Recipe
#         fields = ('name', 'text', 'cooking_time', 'ingredients')

#     def create(self, validated_data):
#         print(validated_data)
#         ingredients = validated_data.pop('ingredients')
#         recipe = Recipe.objects.create(**validated_data)
#         for ingredient in ingredients:
#             current_ingredient = get_object_or_404(
#                 Ingredient, id=ingredient.id
#             )
#             RecipeIngredient.objects.create(
#                 ingredient=current_ingredient,
#                 recipe=recipe,
#                 amount=ingredient.amount
#             )
#         return recipe


# class IngredientRecipeSerializer(serializers.ModelSerializer):
#     """Сериализатор для связи ингредиентов и рецептов."""

#     # amount = serializers.FloatField()

#     class Meta:
#         model = IngredientRecipe
#         fields = ('amount',)


class IngredientSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    name = serializers.CharField(max_length=256, required=False)
    # amount = IngredientRecipeSerializer()


class RecipeSerializer(serializers.ModelSerializer):

    ingredients = IngredientSerializer(many=True)
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'ingredients', 'image', 'cooking_time',
            'tags')

    def create(self, validated_data):
        # Создаем рецепт.
        ingredients = validated_data.pop('ingredients')
        ingredients_init = self.initial_data['ingredients']
        print('ingredients:', ingredients)
        tags = validated_data.pop('tags')
        recipe = Recipe(**validated_data)
        recipe.save()
        # Устанавливаем связи с ингредиентами.
        for ingredient in ingredients_init:
            id = ingredient['id']
            current_ingredient = get_object_or_404(Ingredient, id=id)
            recipe.ingredients.add(current_ingredient)
            # Сохраняем количество.
            ingredient_recipe = IngredientRecipe.objects.get(
                ingredient=id, recipe=recipe)
            ingredient_recipe.amount = ingredient['amount']
            ingredient_recipe.save()
        # Устанавливаем связи с тегами.
        for tag in tags:
            recipe.tags.add(tag)
        return recipe

    # def update(self, instance, validated_data):
    #     instance.name = validated_data.get('name', instance.name)
    #     instance.color = validated_data.get('color', instance.color)
    #     instance.birth_year = validated_data.get(
    #         'birth_year', instance.birth_year
    #         )
    #     instance.image = validated_data.get('image', instance.image)
    #     if 'achievements' in validated_data:
    #         achievements_data = validated_data.pop('achievements')
    #         lst = []
    #         for achievement in achievements_data:
    #             current_achievement, status = Achievement.objects.get_or_create(
    #                 **achievement
    #                 )
    #             lst.append(current_achievement)
    #         instance.achievements.set(lst)
    #     instance.save()
    #     return instance



# {
#   "ingredients": [
#     {
#       "id": 1123,
#       "amount": 10
#     }
#   ],
#   "tags": [
#     1,
#     2
#   ],
#   "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
#   "name": "string",
#   "text": "string",
#   "cooking_time": 1
# }
