# from django.db.models import Exists
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import status  # generics, mixins,
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny  #, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

# from api.pagination import CustomRecipePagination
from api.serializers import GetRecipeSerializer, BaseRecipeSerializer
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             SubscribeUserSerializer, TagSerializer)
from constants import SHORT_LINK_PREFIX, shopping_cart_filename
from recipes.models import Ingredient, Recipe, Tag, User
from users.permissions import IsAuthorOrReadOnly
from users.serializers import CustomUserSerializer


class CustomUserViewSet(UserViewSet):

    @action(["post", "delete"], detail=True)
    def subscribe(self, request, *args, **kwargs):
        user = self.request.user
        to_user = get_object_or_404(User, id=kwargs.get('id'))

        if request.method == 'POST':
            # Проверка на самоподписку и повторную подписку.
            if (
                to_user == user
                or to_user in user.is_subscribed.all()
            ):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            user.is_subscribed.add(to_user)
            serializer = SubscribeUserSerializer(
                to_user,
                context={'request': request}
            )
            if to_user in user.is_subscribed.all():
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
        elif request.method == 'DELETE':
            if to_user in user.is_subscribed.all():
                user.is_subscribed.remove(to_user)
                if to_user not in user.is_subscribed.all():
                    return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(["get"], detail=False)
    def subscriptions(self, request, *args, **kwargs):
        """Список юзеров, на которых подписан автор запроса, (с рецептами)."""
        user = self.request.user
        queryset = user.is_subscribed.all()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SubscribeUserSerializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = SubscribeUserSerializer(
            queryset, many=True, context={'request': request}
        )
        return Response(serializer.data)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для получения тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для получения ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', 'tags__slug',)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user
        if user.is_authenticated:
            is_favor = self.request.query_params.get('is_favorited')
            if is_favor:
                return user.is_favorited.all()
            is_in_sc = self.request.query_params.get(
                'is_in_shopping_cart')
            if is_in_sc:
                return user.is_in_shopping_cart.all()
        return queryset

    def get_serializer_class(self, *args, **kwargs):
        # Для показа рецептов используем отдельный сериализатор.
        if self.action in ['list', 'retrieve']:
            return GetRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        return serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        # После сохранения рецепта возвращаем объект другим сериализатором.
        instance_serializer = GetRecipeSerializer(instance)
        return Response(
            instance_serializer.data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # После сохранения рецепта возвращаем объект другим сериализатором.
        instance_serializer = GetRecipeSerializer(instance)
        return Response(
            instance_serializer.data,
            status=status.HTTP_200_OK
        )


class ShortLinkAPIView(APIView):
    """Получение короткой ссылки."""

    permission_classes = (AllowAny,)

    def get(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        # serializer = ShortLinkSerializer(recipe)
        # short_l = recipe.short_link  # serializer.data['short_link']
        response = {'short-link': f'{SHORT_LINK_PREFIX}{recipe.short_link}'}
        # print(response)
        return Response(response, status=status.HTTP_200_OK)


# class RecipeAPIView(APIView):
#     """Рецепты."""

#     permission_classes = (CustomUserPermission,)

#     def get(self, request):
#         """Получение рецептов."""
#         recipes = Recipe.objects.all()
#         paginator = LimitOffsetPagination()
#         result_page = paginator.paginate_queryset(recipes, request)
#         serializer = GetRecipeSerializer(
#             result_page, many=True, context={'request': request})
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     def post(self, request):
#         """Публикация рецепта."""
#         serializer = RecipeSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save(author=self.request.user)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# def get(self, request, pk, format=None):

#     #user = request.user
#     event = Event.objects.get(pk=pk)
#     news = event.get_news_items().all()
#     paginator = LimitOffsetPagination()
#     result_page = paginator.paginate_queryset(news, request)
#     serializer = NewsItemSerializer(result_page, many=True, context={'request':request})
#     response = Response(serializer.data, status=status.HTTP_200_OK)
#     return response


class FavoriteAPIView(APIView):
    """Класс для сохранения и удаления рецепта в избранное."""

    def post(self, request, id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=id)
        if recipe not in user.is_favorited.all():
            recipe.is_favorited.add(user)
            if recipe in user.is_favorited.all():
                serializer = BaseRecipeSerializer(recipe)
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED
                )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=id)
        if recipe in user.is_favorited.all():
            recipe.is_favorited.remove(self.request.user)
            if recipe not in user.is_favorited.all():
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartAPIView(APIView):
    """Класс для сохранения и удаления рецепта в корзину."""

    def post(self, request, id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=id)
        if recipe not in user.is_in_shopping_cart.all():
            recipe.is_in_shopping_cart.add(user)
            if recipe in user.is_in_shopping_cart.all():
                serializer = BaseRecipeSerializer(recipe)
                return Response(
                    data=serializer.data,
                    status=status.HTTP_201_CREATED
                )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=id)
        if recipe in user.is_in_shopping_cart.all():
            recipe.is_in_shopping_cart.remove(user)
            if recipe not in user.is_in_shopping_cart.all():
                return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class DownloadShoppingCartView(APIView):
    """Выгрузка корзины покупок файлом."""

    def get(self, request):
        user = self.request.user
        queryset = user.is_in_shopping_cart.all()
        shopping_dict = {}
        for recipe in queryset:
            recipe_serializer = GetRecipeSerializer(recipe)
            recipe_ingredients = recipe_serializer.data['ingredients']
            for ingredient in recipe_ingredients:
                key = f"{ingredient['name']} ({ingredient['measurement_unit']})"
                value = ingredient['amount']
                if key in shopping_dict:
                    shopping_dict[key] += value
                else:
                    shopping_dict[key] = value
        filename = shopping_cart_filename
        response = HttpResponse(content_type='text/plain')
        response.write('<p>Список покупок:</p><p></p>')
        for position in shopping_dict:
            response.write(f'<p>{position} - {shopping_dict[position]}</p>')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            filename)
        return response

# filename = "my-file.txt"
# content = 'any string generated by django'
# response = HttpResponse(content, content_type='text/plain')
# response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
# return response

# >>> response = HttpResponse(my_data, content_type='application/vnd.ms-excel')
# >>> response['Content-Disposition'] = 'attachment; filename="foo.xls"'

# response = HttpResponse(data, content_type='application/vnd.ms-excel')
# response['Content-Disposition'] = 'attachment; filename="lots.xlsx"'
# return response

# class UserSubscriptionViewSet(ModelViewSet):
#     """Подписки пользователей."""

#     queryset = User.objects.all()
#     serializer_class = SubscribeUserSerializer
#     permission_classes = (IsAuthenticatedOrReadOnly,)
#     http_method_names = ['get', 'post', 'delete']
#     # filter_backends = (DjangoFilterBackend,)
#     # filterset_fields = ('author', 'tags__slug')  # 'tags__name'

#     def perform_create(self, serializer):
#         print(self.request, serializer)
#         return super().perform_create(serializer)


# class UserSubscriptionViewSet(mixins.CreateModelMixin,
#                               #   mixins.ListModelMixin,
#                               #   mixins.DestroyModelMixin,
#                               #   mixins.RetrieveModelMixin,
#                               #   mixins.UpdateModelMixin,
#                               GenericViewSet):

#     queryset = User.objects.all()
#     serializer_class = SubscribeUserSerializer


#     def perform_create(self, serializer):
#         print('===perform_create')
#         return super().perform_create(serializer)


# class UserSubscriptionView(APIView):
#     """Подписки пользователей."""

#     # def get():
#     #     """
#     #     Возвращает пользователей, на которых подписан текущий пользователь.
#     #     В выдачу добавляются рецепты.
#     #     """
#     #     pass

#     def post(self, request, id):
#         """Подписаться на пользователя."""
#         user = self.request.user
#         subscribe = get_object_or_404(User, id=id)
#         user.is_subscribed.add(subscribe)
#         serializer = SubscribeUserSerializer(
#             subscribe,
#             context={'request': request}
#         )
#         return Response(
#             serializer.data,
#             status=status.HTTP_201_CREATED
#         )

#     def delete(self, request, id):
#         """Удалить подписку на пользователя."""
#         user = self.request.user
#         unsubscribe = get_object_or_404(User, id=id)
#         user.is_subscribed.remove(unsubscribe)
#         if unsubscribe not in user.is_subscribed.all():
#             return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarAPIView(APIView):
    """Работа с аватаром."""

    def put(self, request):
        """Обновление аватара пользователя."""
        if 'avatar' not in request.data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = self.request.user
        serializer = CustomUserSerializer(
            user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            response = {'avatar': serializer.data['avatar']}
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Удаление аватара пользователя."""
        user = self.request.user
        serializer = CustomUserSerializer(
            user, data={'avatar': None}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
