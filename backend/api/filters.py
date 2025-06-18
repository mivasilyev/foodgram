from django_filters.rest_framework import (
    BooleanFilter, CharFilter, FilterSet, ModelMultipleChoiceFilter
)

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Фильтрация продуктов."""

    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name', ]


class RecipeFilter(FilterSet):
    """Фильтр рецептов."""

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = BooleanFilter(
        field_name='favorites__user',
        method='filter_is_favorited'
    )
    is_in_shopping_cart = BooleanFilter(
        field_name='shoppingcarts__user',
        method='filter_is_in_shopping_cart'
    )

    def filter_is_favorited(self, recipes, name, value):
        if value and self.request.user.is_authenticated:
            return recipes.filter(favorites__user=self.request.user)
        return recipes

    def filter_is_in_shopping_cart(self, recipes, name, value):
        if value and self.request.user.is_authenticated:
            return recipes.filter(shoppingcarts__user=self.request.user)
        return recipes

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']
