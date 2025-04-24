import random

from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.pagination import CustomRecipePagination
from constants import CHARACTERS, SHORT_LINK_LENGTH
from recipes.models import Ingredient, Ingredients, Recipe, Tag, User
from recipes.serializers import CustomUserSerializer


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для модели связи рецептов и ингредиентов."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', required=False)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', required=False
    )

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = ('id', 'name', 'measurement_unit')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для сокращенного отображения рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class BaseRecipeSerializer(serializers.ModelSerializer):
    """Общая часть сериализаторов для чтения и записи рецептов."""

    ingredients = IngredientsSerializer(many=True)
    image = Base64ImageField()
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

    def get_is_favorited(self, recipe):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return recipe in user.is_favorited.all()
        return False

    def get_is_in_shopping_cart(self, recipe):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return recipe in user.is_in_shopping_cart.all()
        return False


class GetRecipeSerializer(BaseRecipeSerializer):
    """Модификация сериализатора для полного отображения рецептов."""

    tags = TagSerializer(many=True)


class RecipeSerializer(BaseRecipeSerializer):
    """Модификация сериализатора для сохранения рецептов."""

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать ингредиенты.'
            )
        ingredient_ids = []
        for ingredient in value:
            id = ingredient['ingredient']['id']
            amount = ingredient['amount']
            if not Ingredient.objects.filter(id=id).exists():
                raise serializers.ValidationError(
                    f'Ингредиента {ingredient} нет в списке.'
                )
            if amount < 1:
                raise serializers.ValidationError(
                    'Слишком мало ингредиента.'
                )
            if id in ingredient_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            ingredient_ids.append(id)
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
                'В рецепте нужны ингредиенты.'
            )
        return data

    def make_new_short_link(self):
        # Создание короткой ссылки.
        while True:
            short_link = ''.join(
                random.choices(CHARACTERS, k=SHORT_LINK_LENGTH)
            )
            if not Recipe.objects.filter(short_link=short_link).exists():
                break
        return short_link

    def create(self, validated_data):
        # Создаем рецепт.
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe(**validated_data)
        recipe.short_link = self.make_new_short_link()
        recipe.save()
        # Устанавливаем связи с ингредиентами.
        for ingredient in ingredients:
            current_ingredient = get_object_or_404(
                Ingredient,
                id=ingredient['ingredient']['id']
            )
            Ingredients.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient['amount']
            )
        # Устанавливаем связи с тегами.
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.image = validated_data.get('image', instance.image)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time
        )
        instance.save()
        # Устанавливаем новые теги.
        instance.tags.set(validated_data.get('tags'))
        # Переформатируем новые ингредиенты в словарь.
        new_ingredients = {}
        for ingr in validated_data.get('ingredients'):
            new_ingredients[ingr['ingredient']['id']] = ingr['amount']
        # Перезаписываем ингредиенты, которые уже были в списке.
        ingredients = instance.ingredients.all()
        for ingredient in ingredients:
            if ingredient.ingredient.id in new_ingredients:
                ingredient.amount = new_ingredients.pop(
                    ingredient.ingredient.id
                )
                ingredient.save()
            else:
                ingredient.delete()
        # Сохраняем новые ингредиенты.
        if new_ingredients:
            for ingredient in new_ingredients:
                Ingredients.objects.create(
                    recipe=instance,
                    ingredient=get_object_or_404(Ingredient, id=ingredient),
                    amount=new_ingredients[ingredient]
                )
        return instance


class SubscribeUserSerializer(CustomUserSerializer):
    """Сериализатор для подписки."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        )

    def get_recipes(self, to_user):
        # Вывод рецептов для пользователя делаем через кастомный пагинатор
        # для ограничения количества рецептов в выдаче.
        recipes = to_user.recipes.all()
        paginator = CustomRecipePagination()
        result_page = paginator.paginate_queryset(
            recipes, self.context['request']
        )
        serializer = ShortRecipeSerializer(
            result_page,
            many=True,
            context={'request': self.context['request']}
        )
        return serializer.data

    def get_recipes_count(self, to_user):
        return to_user.recipes.count()

    def get_is_subscribed(self, to_user):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return to_user in user.is_subscribed.all()
        return False
