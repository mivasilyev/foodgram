import base64
import random

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from api.pagination import CustomRecipePagination
from recipes.models import (Ingredient, Recipe, Ingredients, User,
                            Tag)
from users.serializers import CustomUserSerializer

from constants import CHARACTERS, SHORT_LINK_LENGTH


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
        read_only_fields = ('name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('measurement_unit', 'name')


# class IngredientRecipeSerializer(serializers.ModelSerializer):
#     """Сериализатор для связи ингредиентов и рецептов."""

#     id = serializers.IntegerField(source='ingredient.id')
#     name = serializers.CharField(source='ingredient.name')
#     measurement_unit = serializers.CharField(
#         source='ingredient.measurement_unit'
#     )

#     class Meta:
#         model = Ingredients
#         fields = ('id', 'name', 'measurement_unit', 'amount')
#         read_only_fields = ('name', 'measurement_unit')


class IngredientsSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', required=False)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', required=False
    )

    class Meta:
        model = Ingredients
        fields = ('id', 'name', 'measurement_unit', 'amount')


class BaseRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time',)


class GetRecipeSerializer(serializers.ModelSerializer):

    # ingredients = IngredientRecipeSerializer(
    #     many=True, source='ingredientrecipe_set'
    # )
    ingredients = IngredientsSerializer(many=True)
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


class RecipeSerializer(serializers.ModelSerializer):

    ingredients = IngredientsSerializer(many=True)
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
                return obj in user.is_favorited.all()
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
            # ingredient = IngredientsSerializer()
            # ingredient.amount = amount
            # ingredient.ingredient = id
            # ingredient.recipe = recipe
            # ingredient.save()
            # recipe.ingredients.add(
            #     current_ingredient,
            #     through_defaults={'amount': amount}
            # )
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


# class FavoriteSerializer(serializers.ModelSerializer):
#     """Сериализатор для добавления в избранное."""

#     class Meta:
#         model = Favorite
#         fields = ('id', 'user', 'recipe')

#     def create(self, validated_data):

#         # favorite = Favorite(**validated_data)
#         # favorite.save()
#         # return d


class SubscribeUserSerializer(CustomUserSerializer):

    # recipes = BaseRecipeSerializer(many=True, source='author')
    # result_set = CourseComment.objects.all()
    # three_first = Comment(result_set[:3], many=True).data # serializer
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        # Вывод рецептов для пользователя делаем через кастомный пагинатор.
        recipes = obj.author.all()
        paginator = CustomRecipePagination()
        result_page = paginator.paginate_queryset(
            recipes, self.context['request']
        )
        serializer = BaseRecipeSerializer(
            result_page,
            many=True,
            context={'request': self.context['request']}
        )
        return serializer.data

# class EventSerializer(serializers.ModelSerializer):
#     messages = serializers.SerializerMethodField('event_messages')
#
#     def event_messages(self, obj):
#         messages = Message.objects.filter(event=obj)
#         paginator = pagination.PageNumberPagination()
#         page = paginator.paginate_queryset(messages, self.context['request'])
#         serializer = MessageSerializer(page, many=True, context={'request': self.context['request']})
#         return serializer.data

    def get_recipes_count(self, obj):
        return obj.author.count()

    def get_is_subscribed(self, obj):
        if self.context:
            user = self.context.get('request').user
            if user.is_authenticated:
                return obj in user.is_subscribed.all()
        return False
