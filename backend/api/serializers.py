import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import (Ingredient, Recipe, IngredientRecipe,
                            Tag)
from users.serializers import CustomUserSerializer


class Base64ImageField(serializers.ImageField):
    """Обработка избображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')

    # def to_representation(self, instance):
    #     print('----------to_representation, instance:', instance)
    #     return super().to_representation(instance)

    # def to_internal_value(self, data):
    #     print('----------to_internal_value, data:', data)
    #     ret = get_object_or_404(Tag, id=data)
    #     # return super().to_internal_value(data)
    #     return super().to_internal_value(ret)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('name', 'measurement_unit')


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для связи ингредиентов и рецептов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class GetRecipeSerializer(serializers.ModelSerializer):

    ingredients = IngredientRecipeSerializer(
        many=True, source='ingredientrecipe_set'  # .all
    )
    image = Base64ImageField(required=False, allow_null=True)
    author = CustomUserSerializer(required=False)
    tags = TagSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image',
            'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart',
        )
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return True if obj in user.is_favorited.all() else False
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return True if obj in user.is_in_shopping_cart.all() else False
        return False


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

    # def to_representation(self, instance):
    #     ret = super().to_representation(instance)
    #     return ret['ingredient']


class RecipeSerializer(serializers.ModelSerializer):

    # ingredients = IngredientSerializer(many=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source='ingredientrecipe_set', read_only=True  # .all
    )
    image = Base64ImageField(required=False, allow_null=True)
    author = CustomUserSerializer(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'name', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return True if obj in user.is_favorited.all() else False
        return False

    def get_is_in_shopping_cart(self, obj):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return True if obj in user.is_in_shopping_cart.all() else False
        return False

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать ингредиенты.'
            )
        # ingredient_ids = []
        # for ingredient in value:
        #     print(ingredient)
        #     if ingredient not in Ingredient.objects.all():
        #         # filter(id=ingredient).exists():
        #         raise serializers.ValidationError(
        #             f'Ингредиента {ingredient} нет в списке.'
        #         )
        #     if ingredient.id in ingredient_ids:
        #         raise serializers.ValidationError(
        #             'Ингредиенты не должны повторяться.'
        #         )
        #     ingredient_ids.append(ingredient.id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен иметь хотя бы один тег.'
            )
        tag_ids = []
        for tag in value:
            if tag.id in tag_ids:
                raise serializers.ValidationError(
                    'Теги не должны повторяться.'
                )
            tag_ids.append(tag.id)
        return value

    def validate_cooking_time(self, value):
        if not value or value < 1:
            raise serializers.ValidationError(
                'Должно быть указано время приготовления блюда.'
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
        return data

    def create(self, validated_data):
        # Создаем рецепт.
        print('validated_data:', validated_data)
        # ingredients = validated_data.pop('ingredients')
        ingredients_init = self.initial_data['ingredients']
        # print('ingredients:', ingredients)
        tags = validated_data.pop('tags')
        # print('tags:', tags)
        recipe = Recipe(**validated_data)
        recipe.save()
        # Устанавливаем связи с ингредиентами.
        for ingredient in ingredients_init:
            id = ingredient['id']
            current_ingredient = get_object_or_404(Ingredient, id=id)
            recipe.ingredients.add(
                current_ingredient,
                through_defaults={'amount': ingredient['amount']}
            )
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

# Формат ответа при создании рецепта.
# {
#   "id": 0,
#   "tags": [
#     {
#       "id": 0,
#       "name": "Завтрак",
#       "slug": "breakfast"
#     }
#   ],
#   "author": {
#     "email": "user@example.com",
#     "id": 0,
#     "username": "string",
#     "first_name": "Вася",
#     "last_name": "Иванов",
#     "is_subscribed": false,
#     "avatar": "http://foodgram.example.org/media/users/image.png"
#   },
#   "ingredients": [
#     {
#       "id": 0,
#       "name": "Картофель отварной",
#       "measurement_unit": "г",
#       "amount": 1
#     }
#   ],
#   "is_favorited": true,
#   "is_in_shopping_cart": true,
#   "name": "string",
#   "image": "http://foodgram.example.org/media/recipes/images/image.png",
#   "text": "string",
#   "cooking_time": 1
# }



# class FavoriteSerializer(serializers.ModelSerializer):
#     """Сериализатор для добавления в избранное."""

#     class Meta:
#         model = Favorite
#         fields = ('id', 'user', 'recipe')

#     def create(self, validated_data):
#         print(validated_data)

#         # favorite = Favorite(**validated_data)
#         # favorite.save()
#         # return d
