from api.serializers import RecipeSerializer, TagSerializer
from django.shortcuts import get_object_or_404
from recipes.models import Recipe, Tag, User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from users.serializers import CustomUserSerializer


class TagViewSet(ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(ModelViewSet):

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FavoriteAPIView(APIView):
    """Класс для сохранения и удаления рецепта в избранное."""

    def post(self, request, id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=id)
        recipe.favorite.add(user)
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=id)
        recipe.favorite.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

        # serializer = FavoriteSerializer(data=request.data)
        # if serializer.is_valid():
        #     serializer.save(author=self.request.user)
        #     return Response(serializer.data, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def get(self, request):
    #     cats = Cat.objects.all()
    #     serializer = CatSerializer(cats, many=True)
    #     return Response(serializer.data)

# Получение рецепта:
# {
#   "id": 0,
#   "tags": [
#     {
#       "id": 0,
#       "name": "Завтрак",
#       "slug": "breakfast"
#     }
#   ],
#   "author": {
#     "email": "user@example.com",
#     "id": 0,
#     "username": "string",
#     "first_name": "Вася",
#     "last_name": "Иванов",
#     "is_subscribed": false,
#     "avatar": "http://foodgram.example.org/media/users/image.png"
#   },
#   "ingredients": [
#     {
#       "id": 0,
#       "name": "Картофель отварной",
#       "measurement_unit": "г",
#       "amount": 1
#     }
#   ],
#   "is_favorited": true,
#   "is_in_shopping_cart": true,
#   "name": "string",
#   "image": "http://foodgram.example.org/media/recipes/images/image.png",
#   "text": "string",
#   "cooking_time": 1
# }


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
        subscribed = True if subscribe in user.is_subscribed.all() else False
        data = {
            'email': subscribe.email,
            'id': subscribe.id,
            'username': subscribe.username,
            'first_name': subscribe.first_name,
            'last_name': subscribe.last_name,
            'is_subscribed': subscribed,
            'avatar': subscribe.avatar
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

# {
#   "email": "user@example.com",
#   "id": 0,
#   "username": "string",
#   "first_name": "Вася",
#   "last_name": "Иванов",
#   "is_subscribed": true,
#   "recipes": [
#     {
#       "id": 0,
#       "name": "string",
#       "image": "http://foodgram.example.org/media/recipes/images/image.png",
#       "cooking_time": 1
#     }
#   ],
#   "recipes_count": 0,
#   "avatar": "http://foodgram.example.org/media/users/image.png"
# }

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
