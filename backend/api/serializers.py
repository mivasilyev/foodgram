from itertools import groupby

from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from constants import MIN_COOKING_MINUTES, MIN_INGREDIENT_AMOUNT
from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Subscribe,
    Tag
)

User = get_user_model()


class ExtendedUserSerializer(UserSerializer):
    """Доработанный сериализатор djoser для пользователей."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (*UserSerializer.Meta.fields, 'is_subscribed', 'avatar')
        read_only_fields = fields

    def get_is_subscribed(self, author):
        return (
            self.context
            and self.context.get('request').user.is_authenticated
            # and self.context.get('request').user.follows.filter(
            #     subscribed=author).exists()
            and Subscribe.objects.filter(
                user=self.context.get('request').user,
                subscribed=author
            ).exists()
        )


class SubscribeUserSerializer(ExtendedUserSerializer):
    """Сериализатор для подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        fields = (
            *ExtendedUserSerializer.Meta.fields, 'recipes', 'recipes_count'
        )
        read_only_fields = fields

    def get_recipes(self, author):
        # recipes = author.recipes.all()
        # if self.context:
        #     recipes_limit = self.context.get('request').GET.get(
        #         'recipes_limit', 10**10
        #     )
        #     if recipes_limit:
        #         recipes = author.recipes.all()[:int(recipes_limit) - 1]
        return ShortRecipeSerializer(
            author.recipes.all()[:int(
                self.context.get('request').GET.get('recipes_limit', 10**10)
            )],
            many=True,
            context=self.context
        ).data


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

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    # id = serializers.IntegerField(
    #     source='ingredient.id',
    #     validators=[
    #         UniqueValidator(
    #             queryset=IngredientInRecipe.objects.all(),
    #             # lookup=
    #             message="Продукта с таким ID не существует."
    #         )
    #     ]
    # )
    amount = serializers.FloatField(
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)]
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount',)
        # read_only_fields = ('id',)  # без этой строки тоже работает.

    # def validate_id(self, value):
    #     try:
    #         Ingredient.objects.get(id=value)
    #     except Ingredient.DoesNotExist:
    #         raise ValidationError(f'Продукта {value} нет в базе.')
    #     return value

    def to_representation(self, instance):
        # Читаем объект другим сериализатором.
        return IngredientInRecipeSerializer(instance).to_representation(
            instance
        )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор чтения для модели связи рецептов и продуктов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        read_only_fields = fields


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для сокращенного отображения рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)
        read_only_fields = fields


class BaseRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор рецептов."""

    author = ExtendedUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'tags', 'author', 'name', 'image', 'text',
            'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        ]

    def get_mark(self, recipe, model):
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and model.objects.filter(
                user=request.user, recipe=recipe
            ).exists()
        )

    def get_is_favorited(self, recipe):
        return self.get_mark(recipe, Favorite)

    def get_is_in_shopping_cart(self, recipe):
        return self.get_mark(recipe, ShoppingCart)


class GetRecipeSerializer(BaseRecipeSerializer):
    """Сериализатор для полного отображения рецептов."""

    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='ingredients_in_recipe'
    )

    class Meta(BaseRecipeSerializer.Meta):
        # fields = BaseRecipeSerializer.Meta.fields + ['ingredients', ]
        fields = [*BaseRecipeSerializer.Meta.fields, 'ingredients', ]
        # read_only_fields = BaseRecipeSerializer.Meta.fields
        read_only_fields = fields


class RecipeSerializer(BaseRecipeSerializer):
    """Модификация сериализатора для сохранения рецептов."""

    ingredients = WriteIngredientInRecipeSerializer(
        many=True, source='ingredients_in_recipe'
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(MIN_COOKING_MINUTES)]
    )

    class Meta(BaseRecipeSerializer.Meta):
        fields = [*BaseRecipeSerializer.Meta.fields, 'ingredients', ]

    def check_data(self, data, name):
        print('checking_data', data)
        if not data:
            raise serializers.ValidationError(
                f'Рецепт должен содержать {name}.'
            )
        # Составляем список дублирующихся элементов в data.
        duplicates = [
            el for el, group in groupby(data) if len(list(group)) > 1
        ]
        if duplicates:
            raise serializers.ValidationError(
                f'В рецепте повторяются {name}: {duplicates}.'
            )
        # print('return')
        return data

    def validate_ingredients(self, ingredients):
        print('validation:', ingredients)
        return self.check_data(ingredients, 'продукты')
        # if not ingredients:
        #     print('not ingredients')
        #     raise serializers.ValidationError(
        #         'Рецепт должен содержать продукты.'
        #     )
        # duplicated_ingredients = self.find_duplicates(ingredients)
        # if duplicated_ingredients:
        #     raise serializers.ValidationError(
        #         'Продукты не должны повторяться. В рецепте повторяются '
        #         f'{duplicated_ingredients}.'
        #     )
        # return ingredients

    def validate_tags(self, tags):
        return self.check_data(tags, 'теги')
        # if not tags:
        #     raise serializers.ValidationError(
        #         'Рецепт должен иметь хотя бы один тег.'
        #     )
        # duplicated_tags = self.find_duplicates(tags)
        # if duplicated_tags:
        #     raise serializers.ValidationError(
        #         'Теги не должны повторяться. В рецепте повторяются '
        #         f'{duplicated_tags}'
        #     )
        # return tags

    def validate_image(self, value):
        if value is None:
            raise serializers.ValidationError(
                'В рецепте должна быть картинка.'
            )
        return value

    # def validate_cooking_time(self, value):
    #     if value < MIN_COOKING_MINUTES:
    #         raise serializers.ValidationError(
    #             'Время готовки должно быть больше.'
    #         )
    #     return value

    def validate(self, data):
        if 'image' not in data:
            raise serializers.ValidationError(
                'В рецепте должна быть картинка.'
            )
        if 'tags' not in data:
            raise serializers.ValidationError(
                'В рецепте должны быть теги.'
            )
        if 'ingredients_in_recipe' not in data:
            raise serializers.ValidationError(
                'В рецепте нужны продукты.'
            )
        return data

    def fill_ingredients(self, recipe, ingredients):
        """Заполняем ингредиенты в рецепт."""
        # Устанавливаем связи с продуктами.
        # for ingredient in ingredients:
        #     print(ingredient['id'])
        #     IngredientInRecipe.objects.create(
        #         recipe=recipe,
        #         ingredient=ingredient['id'],
        #         amount=ingredient['amount']
        #     )

        # ingredient_records = [
        #     IngredientInRecipe(
        #         recipe=recipe,
        #         ingredient_id=ingredient['ingredient']['id'],
        #         amount=ingredient['amount']
        #     ) for ingredient in ingredients
        # ]

        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    # ingredient_id=ingredient['ingredient']['id'],
                    amount=ingredient['amount']
                ) for ingredient in ingredients
            ]
        )
        # print('success')

    def create(self, validated_data):
        # print('---creation:', validated_data)
        # Создаем рецепт.
        ingredients = validated_data.pop('ingredients_in_recipe')
        # print('===ingredients', ingredients)
        tags = validated_data.pop('tags')
        recipe = super().create(validated_data)
        self.fill_ingredients(recipe, ingredients)
        # Устанавливаем связи с тегами.
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients_in_recipe')
        tags = validated_data.pop('tags')
        # Устанавливаем новые теги и перезаписываем продукты.
        instance.tags.set(tags)
        instance.ingredients_in_recipe.all().delete()
        self.fill_ingredients(recipe=instance, ingredients=ingredients)
        return super().update(
            instance=instance, validated_data=validated_data
        )

    def to_representation(self, instance):
        return GetRecipeSerializer(instance).to_representation(instance)

        # representation = super().to_representation(instance)
        # tags = representation['tags']
        # new_tags = []
        # for tag in tags:
        #     tag_object = Tag.objects.get(id=tag)
        #     new_tag = TagSerializer(tag_object).data
        #     new_tags.append(new_tag)
        # representation['tags'] = new_tags
        # return representation
