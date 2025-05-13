import inspect
# import os

from django.db.models import F, Sum
# from django.contrib.sites.shortcuts import get_current_site
# from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action  # , api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (ExtendedUserSerializer, GetRecipeSerializer,
                             IngredientSerializer, RecipeSerializer,
                             ShortRecipeSerializer, SubscribeSerializer,
                             SubscribeUserSerializer, TagSerializer)
from api.service import shopping_list_render
from constants import DEFAULT_USER_AVATAR, SHOPPING_CART_FILENAME
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
            # if (
            #     author == user
            #     and author not in user.is_subscribed.all()
            # ):
            #     user.is_subscribed.add(author)
            return Response(
                SubscribeUserSerializer(
                    author,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
            # if author in user.is_subscribed.all():
                # serializer = SubscribeUserSerializer(
                #     author,
                #     context={'request': request}
                # )
            # return Response(status=status.HTTP_400_BAD_REQUEST)

        # elif request.method == 'DELETE':
        # Отписываемся от пользователя.
        # get_object_or_404 не подходит, т.к. надо возвращать код 400.
        if Subscribe.objects.filter(user=user, subscribed=author).exists():
            Subscribe.objects.filter(user=user, subscribed=author).delete()
        # if author in user.is_subscribed.all():
        #     user.is_subscribed.remove(author)
        #     if author not in user.is_subscribed.all():
            return Response(status=status.HTTP_204_NO_CONTENT)
        return HttpResponseBadRequest('Такой подписки не существует.')

    @action(["get"], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Список юзеров, на которых подписан автор запроса, (с рецептами)."""
        user = self.request.user
        # queryset = user.is_subscribed.all()
        queryset = User.objects.filter(follows__user=user)
        page = self.paginate_queryset(queryset)

        # if page is not None:
        # serializer = SubscribeUserSerializer(
        #     page, many=True, context={'request': request}
        # )
        return self.get_paginated_response(
            SubscribeUserSerializer(
                page, many=True, context={'request': request}
            ).data
        )

        # serializer = SubscribeUserSerializer(
        #     queryset, many=True, context={'request': request}
        # )
        # return Response(serializer.data)

    @action(["put", "delete"], detail=False, url_path=r'me/avatar')
    def avatar(self, request, *args, **kwargs):
        """Работа с аватаром."""
        if request.method == 'PUT':
            # Обновление аватара пользователя.
            if 'avatar' in request.data:
                user = self.request.user
                serializer = ExtendedUserSerializer(
                    user, data=request.data, partial=True)
                # if serializer.is_valid():
                serializer.is_valid(raise_exception=True)
                serializer.save()
                response = {'avatar': serializer.data['avatar']}
                return Response(response, status=status.HTTP_200_OK)
                # return Response(
                #     serializer.errors, status=status.HTTP_400_BAD_REQUEST
                # )
            return HttpResponseBadRequest('Нет аватара.')
            # Response(status=status.HTTP_400_BAD_REQUEST)

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

    # def get_queryset(self):
    #     # Добавляем фильтрацию по is_favorited, is_in_shopping_cart.
    #     queryset = Recipe.objects.all()
    #     user = self.request.user
    #     if user.is_authenticated:
    #         favorited = self.request.query_params.get('is_favorited')
    #         if favorited:
    #             return Recipe.objects.filter(favorites__user=user)
    #             # user.is_favorited.all()

    #         in_shopping_cart = self.request.query_params.get(
    #             'is_in_shopping_cart')
    #         if in_shopping_cart:
    #             return Recipe.objects.filter(shopping_ingredients__user=user)
    #             # user.is_in_shopping_cart.all()
    #     return queryset

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
        # instance_serializer = GetRecipeSerializer(instance)
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
        # instance_serializer = GetRecipeSerializer(instance)
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
        # user = self.request.user
        # recipe = get_object_or_404(Recipe, id=pk)
        # favorite, created = Favorite.objects.get_or_create(
        #     user=user, recipe=recipe
        # )
        # if not created:
        #     return HttpResponseBadRequest('Запрещено повторное добавление.')

        # # if recipe not in user.is_favorited.all():
        # #     recipe.is_favorited.add(user)
        # #     if recipe in user.is_favorited.all():
        #         # serializer = ShortRecipeSerializer(recipe)
        # return Response(
        #     ShortRecipeSerializer(recipe).data,
        #     status=status.HTTP_201_CREATED
        # )

    @action(methods=["delete"], detail=True)
    def delete(self, request, pk):
        """Удаляем рецепт из избранного."""

        return self.delete_recipe_mark(recipe_id=pk)
        # user = self.request.user
        # recipe = get_object_or_404(Recipe, id=pk)
        # if Favorite.objects.filter(user=user, recipe=recipe).exists():
        #     Favorite.objects.filter(user=user, recipe=recipe).delete()
        # # if recipe in user.is_favorited.all():
        #     # recipe.is_favorited.remove(user)
        #     # if recipe not in user.is_favorited.all():
        #     return Response(status=status.HTTP_204_NO_CONTENT)
        # return HttpResponseBadRequest('Рецепта нет в избранном.')

    @action(methods=["post", "delete"], detail=True)
    def shopping_cart(self, request, pk):
        """Работа с корзиной покупок."""
        # user = self.request.user
        # recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            return self.add_recipe_mark(recipe_id=pk)
            # shopping_cart_pos, created = ShoppingCart.objects.get_or_create(
            #     user=user, recipe=recipe
            # )
            # if not created:
            #     return HttpResponseBadRequest('Продукт уже есть в корзине.')

            # # if recipe not in user.is_in_shopping_cart.all():
            # #     recipe.is_in_shopping_cart.add(user)
            # #     if recipe in user.is_in_shopping_cart.all():
            # #         serializer = ShortRecipeSerializer(recipe)
            # return Response(
            #     data=ShortRecipeSerializer(recipe).data,
            #     status=status.HTTP_201_CREATED
            # )
            # # return Response(status=status.HTTP_400_BAD_REQUEST)

        # elif request.method == 'DELETE':
        return self.delete_recipe_mark(recipe_id=pk)
        # if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
        #     ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        #     return Response(status=status.HTTP_204_NO_CONTENT)
        # return HttpResponseBadRequest('Продукта нет в корзине.')
            # if recipe in user.is_in_shopping_cart.all():
            #     recipe.is_in_shopping_cart.remove(user)
            #     if recipe not in user.is_in_shopping_cart.all():
            #         return Response(status=status.HTTP_204_NO_CONTENT)
            # return Response(status=status.HTTP_400_BAD_REQUEST)
    # ========================================================

    @action(methods=["get"], detail=True, url_path="get-link",
            permission_classes=[AllowAny])
    def get_link(self, request, pk):
        """Получение короткой ссылки."""
        recipe = get_object_or_404(Recipe, id=pk)
        # domain = get_current_site(request).domain
        domain = request.META.get('HTTP_HOST')
        # short_link = f'{domain}/s/{recipe.short_link}/'
        #       request.path, request.build_absolute_uri, request.META,
        #       request.META.get('HTTP_HOST'))

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


# @api_view(['GET'])
# @permission_classes([AllowAny])
# def short_link_redirect(request, short_link):
#     """Редирект коротких ссылок на рецепт."""
#     recipe_id = int(short_link, 16)
#     recipe = get_object_or_404(Recipe, id=recipe_id)
#     redir_link = f'/recipes/{recipe.id}/'
#     full_link = request.build_absolute_uri(redir_link)
#     return HttpResponsePermanentRedirect(full_link)

# ============================================================================

# class GetShortLinkAPIView(APIView):
#     """Получение короткой ссылки."""

#     permission_classes = (AllowAny,)

#     def get(self, request, id):
#         recipe = get_object_or_404(Recipe, id=id)
#         domain = get_current_site(request).domain
#         # short_link = f'{domain}/s/{recipe.short_link}/'
#         short_link = f'{domain}/s/{hex(recipe.id)}'
#         response = {'short-link': short_link}
#         return Response(response, status=status.HTTP_200_OK)


# class ShoppingCartAPIView(APIView):
#     """Класс для добавления рецепта в корзину покупок и удаления."""

#     def post(self, request, id):
#         user = self.request.user
#         recipe = get_object_or_404(Recipe, id=id)
#         if recipe not in user.is_in_shopping_cart.all():
#             recipe.is_in_shopping_cart.add(user)
#             if recipe in user.is_in_shopping_cart.all():
#                 serializer = ShortRecipeSerializer(recipe)
#                 return Response(
#                     data=serializer.data,
#                     status=status.HTTP_201_CREATED
#                 )
#         return Response(status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, id):
#         user = self.request.user
#         recipe = get_object_or_404(Recipe, id=id)
#         if recipe in user.is_in_shopping_cart.all():
#             recipe.is_in_shopping_cart.remove(user)
#             if recipe not in user.is_in_shopping_cart.all():
#                 return Response(status=status.HTTP_204_NO_CONTENT)
#         return Response(status=status.HTTP_400_BAD_REQUEST)


# class DownloadShoppingCartView(APIView):
#     """Выгрузка корзины покупок файлом."""

#     def get(self, request):
#         user = self.request.user
#         queryset = user.is_in_shopping_cart.all()
#         shopping_dict = {}
#         for recipe in queryset:
#             recipe_serializer = GetRecipeSerializer(recipe)
#             for ingred in recipe_serializer.data['ingredients']:
#                 key = f"{ingred['name']} ({ingred['measurement_unit']})"
#                 value = ingred['amount']
#                 if key in shopping_dict:
#                     shopping_dict[key] += value
#                 else:
#                     shopping_dict[key] = value
#         response = HttpResponse(content_type='text/plain')
#         response.write('<p>Список покупок:</p><p></p>')
#         for position in shopping_dict:
#             response.write(f'<p>{position} - {shopping_dict[position]}</p>')
#         response['Content-Disposition'] = 'attachment; filename={0}'.format(
#             SHOPPING_CART_FILENAME
#         )
#         return response


# class AvatarAPIView(APIView):
#     """Работа с аватаром."""

#     def put(self, request):
#         """Обновление аватара пользователя."""
#         if 'avatar' in request.data:
#             user = self.request.user
#             serializer = ExtendedUserSerializer(
#                 user, data=request.data, partial=True)
#             if serializer.is_valid():
#                 serializer.save()
#                 response = {'avatar': serializer.data['avatar']}
#                 return Response(response, status=status.HTTP_200_OK)
#             return Response(
#                 serializer.errors, status=status.HTTP_400_BAD_REQUEST
#             )
#         return Response(status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request):
#         """Удаление аватара пользователя."""
#         user = self.request.user
#         serializer = ExtendedUserSerializer(
#             user, data={'avatar': None}, partial=True)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         return Response(
#             serializer.errors, status=status.HTTP_400_BAD_REQUEST)
