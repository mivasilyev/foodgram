from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from recipes.models import Tag, Recipe
from api.serializers import TagSerializer, RecipeSerializer  # , FavoriteSerializer


class TagViewSet(ReadOnlyModelViewSet):

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(ModelViewSet):

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class APIFavorite(APIView):
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