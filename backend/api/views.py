from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
# from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
# from rest_framework.filters import SearchFilter
# from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.serializers import GetRecipeSerializer  # ShortLinkSerializer,
from api.serializers import (IngredientSerializer, RecipeSerializer,
                             SubscribeUserSerializer, TagSerializer)
from constants import SHORT_LINK_PREFIX
from recipes.models import Ingredient, Recipe, Tag, User
from users.permissions import IsAuthorOrReadOnly
from users.serializers import CustomUserSerializer


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
    filterset_fields = ('name',)  # 'slug')


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', 'tags__name', 'tags__slug')

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
        print(response)
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
        recipe = get_object_or_404(Recipe, id=id)
        recipe.is_favorited.add(self.request.user)
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        recipe.is_favorited.remove(self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartAPIView(APIView):
    """Класс для сохранения и удаления рецепта в корзину."""

    def post(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        recipe.is_in_shopping_cart.add(self.request.user)
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        recipe = get_object_or_404(Recipe, id=id)
        recipe.is_in_shopping_cart.remove(self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserSubscriptionView(APIView):
    """Подписки пользователей."""

    # def get():
    #     """
    #     Возвращает пользователей, на которых подписан текущий пользователь.
    #     В выдачу добавляются рецепты.
    #     """
    #     pass

    def post(self, request, id):
        """Подписаться на пользователя."""
        user = self.request.user
        subscribe = get_object_or_404(User, id=id)
        user.is_subscribed.add(subscribe)
        serializer = SubscribeUserSerializer(
            subscribe,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, id):
        """Удалить подписку на пользователя."""
        user = self.request.user
        unsubscribe = get_object_or_404(User, id=id)
        user.is_subscribed.remove(unsubscribe)
        if unsubscribe not in user.is_subscribed.all():
            return Response(status=status.HTTP_204_NO_CONTENT)


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
