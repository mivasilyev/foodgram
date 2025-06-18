from django.db.models import F, Sum
from django.http import (
    FileResponse, HttpResponseBadRequest, HttpResponseNotFound
)
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    ExtendedUserSerializer, GetRecipeSerializer, IngredientSerializer,
    WriteRecipeSerializer, ShortRecipeSerializer, SubscribeUserSerializer,
    TagSerializer
)
from api.service import shopping_list_render
from constants import SHOPPING_CART_FILENAME
from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Subscribe,
    Tag, User
)


class ExtendedUserViewSet(UserViewSet):
    """Расширение вьюсета пользователя djoser для работы с подпиской."""

    permission_classes = [IsAuthorOrReadOnly]

    @action(["get", "put", "patch", "delete"], detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request):
        return super().me(request)

    @action(["post", "delete"], detail=True)
    def subscribe(self, request, *args, **kwargs):
        """Подписка и отписка от пользователя."""
        user = self.request.user

        if request.method != 'POST':
            # Отписываемся от пользователя.
            get_object_or_404(
                Subscribe, user=user, subscribed_id=kwargs['id']
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        # Подписываемся на пользователя.
        author = get_object_or_404(User, id=kwargs['id'])
        if author == user:
            return HttpResponseBadRequest('Запрещена подписка на себя.')
        _, created = Subscribe.objects.get_or_create(
            user=user, subscribed=author
        )
        if not created:
            return HttpResponseBadRequest(f'Подписка на {author} уже есть.')
        return Response(
            SubscribeUserSerializer(
                author,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @action(["get"], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Список юзеров, на которых подписан автор запроса, (с рецептами)."""
        queryset = User.objects.filter(authors__user=self.request.user)
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(
            SubscribeUserSerializer(
                page, many=True, context={'request': request}
            ).data
        )

    @action(["put", "delete"], detail=False, url_path=r'me/avatar')
    def avatar(self, request, *args, **kwargs):
        """Работа с аватаром."""
        if request.method == 'PUT':
            # Обновление аватара пользователя.
            if 'avatar' in request.data:
                user = self.request.user
                serializer = ExtendedUserSerializer(
                    user, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                response = {'avatar': serializer.data['avatar']}
                return Response(response, status=status.HTTP_200_OK)
            return HttpResponseBadRequest('Нет аватара.')
        # Удаление аватара пользователя.
        user = self.request.user
        serializer = ExtendedUserSerializer(
            user, data={'avatar': None}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Файл с диска удаляет django-cleanup.
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для получения тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для получения продуктов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self, *args, **kwargs):
        # Для показа рецептов используем отдельный сериализатор.
        if self.action in ['list', 'retrieve']:
            return GetRecipeSerializer
        return WriteRecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def add_recipe_mark(self, recipe_id, model):
        """Добавляем к рецепту отметку избранное/корзина."""
        recipe = get_object_or_404(Recipe, id=recipe_id)
        mark, created = model.objects.get_or_create(
            user=self.request.user, recipe=recipe
        )
        if not created:
            return HttpResponseBadRequest(
                f'Запрещено повторное добавление рецепта {recipe_id} в '
                f'{model._meta.verbose_name}.'
            )
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete_recipe_mark(self, recipe_id, model):
        get_object_or_404(
            model,
            user=self.request.user,
            recipe_id=recipe_id
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["post", "delete"], detail=True)
    def favorite(self, request, pk):
        if request.method == 'POST':
            """Добавляем рецепт в избранное."""
            return self.add_recipe_mark(recipe_id=pk, model=Favorite)
        return self.delete_recipe_mark(recipe_id=pk, model=Favorite)

    @action(methods=["post", "delete"], detail=True)
    def shopping_cart(self, request, pk):
        """Работа с корзиной покупок."""
        if request.method == 'POST':
            return self.add_recipe_mark(recipe_id=pk, model=ShoppingCart)
        return self.delete_recipe_mark(recipe_id=pk, model=ShoppingCart)

    @action(methods=["get"], detail=True, url_path="get-link",
            permission_classes=[AllowAny])
    def get_link(self, request, pk):
        """Получение короткой ссылки."""
        if Recipe.objects.filter(id=pk).exists():
            return Response(
                {'short-link': request.build_absolute_uri(
                    reverse('recipes:short_link', args=[pk])
                )},
                status=status.HTTP_200_OK
            )
        return HttpResponseNotFound(
            f'Запрошенного рецепта {pk} не существует.'
        )

    @action(methods=["get"], detail=False)
    def download_shopping_cart(self, request):
        """Выгрузка корзины покупок файлом."""
        user = self.request.user
        recipe_qs = Recipe.objects.filter(shoppingcarts__user=user)
        product_qs = IngredientInRecipe.objects.filter(
            recipe__shoppingcarts__user=user
        ).values(
            product=F('ingredient__name'),
            unit=F('ingredient__measurement_unit')
        ).annotate(
            amount=Sum('amount')
        ).order_by(
            'ingredient__name'
        )
        return FileResponse(
            shopping_list_render(recipes=recipe_qs, products=product_qs),
            content_type='text/plain',
            as_attachment=True,
            filename=SHOPPING_CART_FILENAME
        )
