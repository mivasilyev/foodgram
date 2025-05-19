from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from constants import MIN_COOKING_MINUTES
from recipes.models import (Ingredient, IngredientInRecipe, Recipe, Subscribe,
                            Tag)

User = get_user_model()


class ExtendedUserSerializer(UserSerializer):
    """Доработанный сериализатор djoser для пользователей."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (*UserSerializer.Meta.fields, 'is_subscribed', 'avatar')

    def get_is_subscribed(self, author):
        return (
            bool(self.context)
            and self.context.get('request').user.is_authenticated
            and self.context.get('request').user.follows.filter(
                subscribed=author).exists()
        )
        # if self.context:
        #     user = self.context.get('request').user
        #     if user.is_authenticated:
        #         return user.follows.filter(subscribed=author).exists()
        # return False


class SubscribeUserSerializer(ExtendedUserSerializer):
    """Сериализатор для подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    # recipes_count = serializers.SerializerMethodField(
    #     source='author.recipes.all()')

    class Meta:
        model = User
        fields = (*ExtendedUserSerializer.Meta.fields,
                  'recipes', 'recipes_count')

    def get_recipes(self, author):
        recipes = author.recipes.all()
        if self.context:
            # request = self.context.get('request')
            # recipes_limit = request.query_params.get('recipes_limit')
            recipes_limit = self.context.get('request').query_params.get(
                'recipes_limit')
            if recipes_limit:
                recipes = recipes[:int(recipes_limit) - 1]
        # serializer = ShortRecipeSerializer(
        #     recipes,
        #     many=True,
        #     context=self.context
        # )
        # return serializer.data
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context
        ).data

    def get_recipes_count(self, author):
        return author.recipes.count()

# Весь метод .get_recipes_count() лишний! В объявлении поля лучше указать
# через параметр source "как получить". Внутри этого параметра можно писать
# вызовы методов "без скобок" (такой язык уже был в подстановках в шаблонах).


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


class WriteIngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор записи для модели связи рецептов и продуктов."""

    id = serializers.IntegerField(source='ingredient.id')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)
        read_only_fields = ('id',)

    def validate_id(self, value):
        if not Ingredient.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                f'Продукта {value} нет в базе.'
            )
        return value


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор чтения для модели связи рецептов и продуктов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        read_only_fields = fields
        # read_only_fields = ('id', 'name', 'measurement_unit',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для сокращенного отображения рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = fields


class GetRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для полного отображения рецептов."""

    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(many=True)
    # image = Base64ImageField()
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

    ingredients = WriteIngredientInRecipeSerializer(many=True)
    image = Base64ImageField()
    # author = ExtendedUserSerializer(required=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'ingredients', 'name', 'image', 'text',  # 'author'
            'cooking_time'
        )
        # read_only_fields = ('author',)

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать продукты.'
            )
        duplicated_ingredients = []
        ingredient_ids = []
        for ingredient in ingredients:
            id = ingredient['ingredient']['id']
            # if not Ingredient.objects.filter(id=id).exists():
            #     raise serializers.ValidationError(
            #         f'Продукта {ingredient} нет в списке.'
            #     )
            if id in ingredient_ids:
                # duplicated_ingredient = Ingredient.objects.get(id=id)
                duplicated_ingredients.append(id)

            ingredient_ids.append(id)

        if duplicated_ingredients:
            raise serializers.ValidationError(
                'Продукты не должны повторяться. В рецепте повторяются '
                f'{duplicated_ingredients}.'
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
                f'{duplicated_tags}'
            )

        return tags

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError(
                'В рецепте должна быть картинка.'
            )
        return value

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_MINUTES:
            raise serializers.ValidationError(
                'Время готовки должно быть больше.'
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
        ingredient_records = [
            IngredientInRecipe(
                recipe=recipe,
                # ingredient=Ingredient.objects.get(
                #     id=ingredient['ingredient']['id']),
                ingredient_id=ingredient['ingredient']['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients]

        # ingredient_records = []
        # for ingredient in ingredients:
        #     ingredient_records.append(
        #         IngredientInRecipe(
        #             recipe=recipe,
        #             # ingredient=Ingredient.objects.get(
        #             #     id=ingredient['ingredient']['id']),
        #             ingredient_id=ingredient['ingredient']['id'],
        #             amount=ingredient['amount']
        #         )
        #     )
        IngredientInRecipe.objects.bulk_create(ingredient_records)

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
        # super().update(instance=instance, validated_data=validated_data)
        # Устанавливаем новые теги и перезаписываем продукты.
        instance.tags.set(tags)
        instance.ingredients.all().delete()
        self.fill_ingredients(recipe=instance, ingredients=ingredients)
        # return instance  # объединить
        return super().update(
            instance=instance, validated_data=validated_data)


# class SubscribeSerializer(serializers.ModelSerializer):
#     """Сериализатор для записи подписки."""

#     class Meta:
#         model = Subscribe
#         fields = '__all__'
#         validators = [
#             UniqueTogetherValidator(
#                 queryset=Subscribe.objects.all(),
#                 fields=['user', 'subscribed']
#             )
#         ]
