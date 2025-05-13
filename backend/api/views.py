import inspect

from django.db.models import F, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (ExtendedUserSerializer, GetRecipeSerializer,
                             IngredientSerializer, RecipeSerializer,
                             ShortRecipeSerializer, SubscribeUserSerializer,
                             TagSerializer)
from api.service import shopping_list_render
from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Subscribe, Tag, User)


class ExtendedUserViewSet(UserViewSet):
    """Расширение вьюсета пользователя djoser для работы с подпиской."""

    @action(["post", "delete"], detail=True)
    def subscribe(self, request, *args, **kwargs):
        """Подписка и отписка от пользователя."""
        user = self.request.user
        author = get_object_or_404(User, id=kwargs.get('id'))

        if request.method == 'POST':
            # Подписываемся на пользователя.
            # Проверка на самоподписку и повторную подписку.
            if author == user:
                return HttpResponseBadRequest('Запрещена подписка на себя.')
            subscription, created = Subscribe.objects.get_or_create(
                user=user, subscribed=author
            )
            if not created:
                return HttpResponseBadRequest('Повторная подписка запрещена.')
            return Response(
                SubscribeUserSerializer(
                    author,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        # Отписываемся от пользователя.
        # get_object_or_404 не подходит, т.к. надо возвращать код 400.
        if Subscribe.objects.filter(user=user, subscribed=author).exists():
            Subscribe.objects.filter(user=user, subscribed=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return HttpResponseBadRequest('Такой подписки не существует.')

    @action(["get"], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Список юзеров, на которых подписан автор запроса, (с рецептами)."""
        user = self.request.user
        queryset = User.objects.filter(follows__user=user)
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

        elif request.method == 'DELETE':
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
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self, *args, **kwargs):
        # Для показа рецептов используем отдельный сериализатор.
        if self.action in ['list', 'retrieve']:
            return GetRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        # Метод переопределяем по рекомендации наставника чтобы после создания
        # рецепта вернуть его другим сериализатором.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        # После сохранения рецепта возвращаем объект другим сериализатором.
        return Response(
            GetRecipeSerializer(instance).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        # Метод переопределяем по рекомендации наставника чтобы после редакт-я
        # рецепта вернуть его другим сериализатором.
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # После сохранения рецепта возвращаем объект другим сериализатором.
        return Response(
            GetRecipeSerializer(instance).data,
            status=status.HTTP_200_OK
        )

    def add_recipe_mark(self, recipe_id):
        """Добавляем к рецепту отметку избранное/корзина."""
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        # Рабочую модель определяем по вызывающей функции, а ее по стеку.
        calling_func = inspect.stack()[1][3]
        model_choice = {
            'favorite': Favorite,
            'shopping_cart': ShoppingCart,
        }
        mark, created = model_choice[calling_func].objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            return HttpResponseBadRequest('Запрещено повторное добавление.')
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete_recipe_mark(self, recipe_id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        calling_func = inspect.stack()[1][3]
        model_choice = {
            'delete': Favorite,
            'shopping_cart': ShoppingCart,
        }
        model = model_choice[calling_func]
        if model.objects.filter(user=user, recipe=recipe).exists():
            model.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return HttpResponseBadRequest('Рецепта нет в модели.')

    @action(methods=["post"], detail=True)
    def favorite(self, request, pk):
        """Добавляем рецепт в избранное."""

        return self.add_recipe_mark(recipe_id=pk)

    @action(methods=["delete"], detail=True)
    def delete(self, request, pk):
        """Удаляем рецепт из избранного."""

        return self.delete_recipe_mark(recipe_id=pk)

    @action(methods=["post", "delete"], detail=True)
    def shopping_cart(self, request, pk):
        """Работа с корзиной покупок."""

        if request.method == 'POST':
            return self.add_recipe_mark(recipe_id=pk)

        return self.delete_recipe_mark(recipe_id=pk)

    @action(methods=["get"], detail=True, url_path="get-link",
            permission_classes=[AllowAny])
    def get_link(self, request, pk):
        """Получение короткой ссылки."""
        recipe = get_object_or_404(Recipe, id=pk)
        domain = request.META.get('HTTP_HOST')
        response = {'short-link': f'{domain}/s/{hex(recipe.id)}'}
        return Response(response, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False)
    def download_shopping_cart(self, request):
        """Выгрузка корзины покупок файлом."""
        user = self.request.user
        recipe_qs = Recipe.objects.filter(shopping_ingredients__user=user)
        product_qs = IngredientInRecipe.objects.filter(
            recipe__shopping_ingredients__user=user
        ).values(product=F('ingredient__name'),
                 unit=F('ingredient__measurement_unit')).annotate(
                     amount=Sum('amount'))
        return shopping_list_render(
            recipe_qs=recipe_qs, products_qs=product_qs
        )
