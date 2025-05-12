from django_filters.rest_framework import (CharFilter, FilterSet,
                                           ModelChoiceFilter,
                                           ModelMultipleChoiceFilter)

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """Фильтрация продуктов."""

    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name', ]


# def get_user_favorited_queryset(request):
#     favorited = request.query_params.get('is_favorited')
#     queryset = Recipe.objects.all()
#     if favorited and request.user.is_authenticated:
#         queryset = queryset.filter(favorites__user=request.user)
#     return queryset  # .objects.none()


# def get_is_in_shopping_cart_queryset(request):
#     in_shopping_cart = request.query_params.get('is_in_shopping_cart')
#     print('-----------------in_shopping_cart:', in_shopping_cart)
#     if in_shopping_cart and request.user.is_authenticated:
#         queryset = Recipe.objects.filter(
#             shopping_ingredients__user=request.user)
#         for i in queryset:
#             print(i)
#         return queryset
#     return Recipe.objects.all()


# def get_cart_queryset(request):
#     queryset = Recipe.objects.all()
#     favorited = request.query_params.get('is_favorited')
#     in_shopping_cart = request.query_params.get('is_in_shopping_cart')
#     if request.user.is_authenticated:
#         if favorited:
#             queryset = queryset.filter(favorites__user=request.user)
#         if in_shopping_cart:
#             queryset = queryset.filter(
#                 shopping_ingredients__user=request.user)
#     return queryset


class RecipeFilter(FilterSet):
    """Фильтр рецептов."""

    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    # is_favorited = ModelChoiceFilter(queryset=get_user_favorited_queryset)

    # is_in_shopping_cart = ModelChoiceFilter(
    #     queryset=get_is_in_shopping_cart_queryset)
    # is_in_shopping_cart = ModelChoiceFilter(
    #     queryset=get_is_in_shopping_cart_queryset
    # )

    class Meta:
        model = Recipe
        fields = ['author', 'tags',]  # 'is_favorited']
