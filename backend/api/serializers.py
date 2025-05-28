from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from constants import MIN_COOKING_MINUTES
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag

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


class SubscribeUserSerializer(ExtendedUserSerializer):
    """Сериализатор для подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        fields = (
            *ExtendedUserSerializer.Meta.fields, 'recipes', 'recipes_count'
        )

    def get_recipes(self, author):
        recipes = author.recipes.all()
        if self.context:
            recipes_limit = self.context.get('request').query_params.get(
                'recipes_limit'
            )
            if recipes_limit:
                recipes = recipes[:int(recipes_limit) - 1]
        return ShortRecipeSerializer(
            recipes, many=True, context=self.context
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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['name'] = instance.ingredient.name
        representation[
            'measurement_unit'
        ] = instance.ingredient.measurement_unit
        return representation


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
            and recipe.shoppingcarts.filter(user=request.user).exists()
        )


class GetRecipeSerializer(BaseRecipeSerializer):
    """Сериализатор для полного отображения рецептов."""

    tags = TagSerializer(many=True)
    ingredients = IngredientInRecipeSerializer(
        many=True, source='ingredients_in_recipe'
    )

    class Meta(BaseRecipeSerializer.Meta):
        fields = BaseRecipeSerializer.Meta.fields + ['ingredients', ]
        read_only_fields = BaseRecipeSerializer.Meta.fields


class RecipeSerializer(BaseRecipeSerializer):
    """Модификация сериализатора для сохранения рецептов."""

    ingredients = WriteIngredientInRecipeSerializer(
        many=True, source='ingredients_in_recipe'
    )
    image = Base64ImageField()

    class Meta(BaseRecipeSerializer.Meta):
        fields = BaseRecipeSerializer.Meta.fields + ['ingredients', ]

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Рецепт должен содержать продукты.'
            )
        duplicated_ingredients = []
        ingredient_ids = []
        for ingredient in ingredients:
            id = ingredient['ingredient']['id']
            if id in ingredient_ids:
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
        if 'ingredients_in_recipe' not in data:
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
                ingredient_id=ingredient['ingredient']['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients]
        IngredientInRecipe.objects.bulk_create(ingredient_records)

    def create(self, validated_data):
        # Создаем рецепт.
        ingredients = validated_data.pop('ingredients_in_recipe')
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
        representation = super().to_representation(instance)
        tags = representation['tags']
        new_tags = []
        for tag in tags:
            tag_object = Tag.objects.get(id=tag)
            new_tag = TagSerializer(tag_object).data
            new_tags.append(new_tag)
        representation['tags'] = new_tags
        return representation
