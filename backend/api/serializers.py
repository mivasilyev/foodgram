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


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


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

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'ingredients', 'cooking_time')

    def create(self, validated_data):

        ingredients = validated_data.pop('ingredients')
        ingredients_init = self.initial_data['ingredients']
        recipe = Recipe.objects.create(**validated_data)
        for ingredient in ingredients_init:
            id = ingredient['id']
            amount = ingredient['amount']
            current_ingredient = get_object_or_404(Ingredient, id=id)
            IngredientRecipe.objects.create(
                ingredient=current_ingredient,
                recipe=recipe,
                amount=amount
            )
        return recipe

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
