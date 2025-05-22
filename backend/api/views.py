from django.db.models import F, Sum
from django.http import FileResponse, HttpResponseBadRequest
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
from api.serializers import (
    ExtendedUserSerializer, GetRecipeSerializer, IngredientSerializer,
    RecipeSerializer, ShortRecipeSerializer, SubscribeUserSerializer,
    TagSerializer  #  SubscribeSerializer,
)
from api.service import shopping_list_render
from constants import SHOPPING_CART_FILENAME
from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Subscribe,
    Tag, User
)
from rest_framework.settings import api_settings


class ExtendedUserViewSet(UserViewSet):
    """Расширение вьюсета пользователя djoser для работы с подпиской."""

    @action(["post", "delete"], detail=True)
    def subscribe(self, request, *args, **kwargs):
        """Подписка и отписка от пользователя."""
        user = self.request.user
        author = get_object_or_404(User, id=kwargs['id'])

        if request.method == 'POST':
            # Подписываемся на пользователя.
            # Проверка на самоподписку и повторную подписку.

            # print('==========', user, author)
            # print(SubscribeUserSerializer.Meta.fields)
            # serializer = SubscribeUserSerializer(
            #     data={'username': author.username, 'subscribed': author.id},
            #     context=self.get_serializer_context(),
            # )
            # print(serializer.is_valid(), serializer.errors)
            # serializer.is_valid(raise_exception=True)
            # serializer.save()
            # return Response(serializer.data, status=status.HTTP_201_CREATED)

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

        # elif request.method == 'DELETE':
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
    # pagination_class = LimitPageNumberPagination
    # search_fields = ('@name', '@author__username', '@tags__name')
    # http_method_names = ('get', 'patch', 'post', 'delete')

    def get_serializer_class(self, *args, **kwargs):
        # Для показа рецептов используем отдельный сериализатор.
        if self.action in ['list', 'retrieve']:
            return GetRecipeSerializer
        return RecipeSerializer

    # def get_serializer_class(self):
    #     if self.request.method in SAFE_METHODS:
    #         return RecipeReadSerializer
    #     return RecipeWriteSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    # def create(self, request, *args, **kwargs):
    #     # Метод переопределяем по рекомендации наставника чтобы после создания
    #     # рецепта вернуть его другим сериализатором.
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     instance = self.perform_create(serializer)
    #     # После сохранения рецепта возвращаем объект другим сериализатором.
    #     return Response(
    #         GetRecipeSerializer(instance).data,
    #         status=status.HTTP_201_CREATED
    #     )

    # def update(self, request, *args, **kwargs):
    #     # Метод переопределяем по рекомендации наставника чтобы после редакт-я
    #     # рецепта вернуть его другим сериализатором.
    #     partial = kwargs.pop('partial', False)
    #     instance = self.get_object()
    #     serializer = self.get_serializer(
    #         instance, data=request.data, partial=partial
    #     )
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_update(serializer)
    #     # После сохранения рецепта возвращаем объект другим сериализатором.
    #     return Response(
    #         GetRecipeSerializer(instance).data,
    #         status=status.HTTP_200_OK
    #     )

    def add_recipe_mark(self, recipe_id, model):
        """Добавляем к рецепту отметку избранное/корзина."""
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=recipe_id)
        # Рабочую модель определяем по вызывающей функции, а ее по стеку.
        # calling_func = inspect.stack()[1][3]
        # model_choice = {
        #     'favorite': Favorite,
        #     'shopping_cart': ShoppingCart,
        # }
        # mark, created = model_choice[calling_func].objects.get_or_create(
        #     user=user, recipe=recipe
        # )
        mark, created = model.objects.get_or_create(
            user=user, recipe=recipe
        )
        if not created:
            return HttpResponseBadRequest('Запрещено повторное добавление.')
        return Response(
            ShortRecipeSerializer(recipe).data,
            status=status.HTTP_201_CREATED
        )

    def delete_recipe_mark(self, recipe_id, model):
        user = self.request.user
        # Запрос нужен, чтобы получить 404, если нет такого рецепта в Recipe.
        # без него проваливаются тесты на попытку удалить несуществующий
        # рецепт из корзины/избранного.
        get_object_or_404(Recipe, id=recipe_id)
        # calling_func = inspect.stack()[1][3]
        # model_choice = {
        #     'delete': Favorite,
        #     'shopping_cart': ShoppingCart,
        # }
        # model = model_choice[calling_func]
        if model.objects.filter(user=user, recipe_id=recipe_id).exists():
            model.objects.filter(user=user, recipe_id=recipe_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return HttpResponseBadRequest('Нет такой отметки на рецепте.')

    @action(methods=["post"], detail=True)
    def favorite(self, request, pk):
        """Добавляем рецепт в избранное."""

        return self.add_recipe_mark(recipe_id=pk, model=Favorite)

    @action(methods=["delete"], detail=True)
    def delete(self, request, pk):
        """Удаляем рецепт из избранного."""

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
        # print(pk, type(pk))
        if Recipe.objects.filter(id=pk).exists():
            # recipe = get_object_or_404(Recipe, id=pk)
            domain = request.META.get('HTTP_HOST')
            response = {'short-link': f'{domain}/s/{hex(int(pk))}'}
            return Response(response, status=status.HTTP_200_OK)
        else:
            # если объекта нет ===============================================
            pass

    @action(methods=["get"], detail=False)
    def download_shopping_cart(self, request):
        """Выгрузка корзины покупок файлом."""
        user = self.request.user
        # recipe_qs = Recipe.objects.filter(shopping_ingredients__user=user)
        recipe_qs = Recipe.objects.filter(shoppingcarts__user=user)
        product_qs = IngredientInRecipe.objects.filter(
            recipe__shoppingcarts__user=user
            # recipe__shopping_ingredients__user=user
        ).values(product=F('ingredient__name'),
                 unit=F('ingredient__measurement_unit')).annotate(
                     amount=Sum('amount')).order_by('ingredient__name')
        return FileResponse(
            shopping_list_render(recipe_qs=recipe_qs, products_qs=product_qs),
            content_type='text/plain',
            as_attachment=True,
            filename=SHOPPING_CART_FILENAME
        )

# =======================================

#     def get_queryset(self):
#         ...


#     def delete_user_recipe(self, pk, model):
#         ...

#     @action(
#         detail=True, permission_classes=(IsAuthenticated,), methods=('POST',)
#     )
#     def favorite(self, request, pk):
#         ...

#     @favorite.mapping.delete
#     def delete_favorite(self, request, pk):
#         ...

#     @action(
#         detail=True, permission_classes=(IsAuthenticated,), methods=('POST',)
#     )
#     def shopping_cart(self, request, pk):
#         ...

#     @shopping_cart.mapping.delete
#     def delete_shopping_cart(self, request, pk):
#         ...

#     @action(detail=False, permission_classes=(IsAuthenticated,))
#     def download_shopping_cart(self, request):
#         ...


#     @staticmethod
#     def ingredients_to_text(ingredients):
#         ...

#     @action(detail=True, url_path='get-link')
#     def get_link(self, request, pk=None):
#         ...