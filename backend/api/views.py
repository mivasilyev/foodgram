from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import (DjangoFilterBackend, FilterSet,
                                           ModelMultipleChoiceFilter,
                                           CharFilter, MultipleChoiceFilter)
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.serializers import (BaseRecipeSerializer, GetRecipeSerializer,
                             IngredientSerializer, RecipeSerializer,
                             SubscribeUserSerializer, TagSerializer)
from constants import SHOPPING_CART_FILENAME, SHORT_LINK_PREFIX
from recipes.models import Ingredient, Recipe, Tag, User
from users.permissions import IsAuthorOrReadOnly
from users.serializers import CustomUserSerializer


class CustomUserViewSet(UserViewSet):
    """Расширение вьюсета пользователя djoser для работы с подпиской."""

    @action(["post", "delete"], detail=True)
    def subscribe(self, request, *args, **kwargs):
        """Подписка и отписка от пользователя."""
        user = self.request.user
        to_user = get_object_or_404(User, id=kwargs.get('id'))

        if request.method == 'POST':
            # Подписываемся на пользователя.
            # Проверка на самоподписку и повторную подписку.
            if (
                to_user != user
                and to_user not in user.is_subscribed.all()
            ):
                user.is_subscribed.add(to_user)
                if to_user in user.is_subscribed.all():
                    serializer = SubscribeUserSerializer(
                        to_user,
                        context={'request': request}
                    )
                    return Response(
                        serializer.data,
                        status=status.HTTP_201_CREATED
                    )
            return Response(status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            # Отписываемся от пользователя.
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


class RecipeFilter(FilterSet):

    # tags = CharFilter(field_name='tags__slug')  # , method='search_filter')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        # lookup_type='in',
        queryset=Tag.objects.all(),
    )

    # tags = django_filters.ModelMultipleChoiceFilter(
    #     name='sitetags__name',
    #     to_field_name='name',
    #     lookup_type='in',
    #     queryset=SiteTag.objects.all()
    # )

    class Meta:
        model = Recipe
        fields = ['author', 'tags']
        # fields = {
        #     'author': ['exact'],  # , 'contains'
        #     'tags': ['exact'],
        # }

# from django_filters import Filter
# from django_filters.fields import Lookup
# from .models import Product
# class ListFilter(Filter):
#     def filter(self, qs, value):
#         value_list = value.split(u',')
#         return super(ListFilter, self).filter(qs, Lookup(value_list, 'in'))
# class ProductFilterSet(django_filters.FilterSet):
#     category = ListFilter(name='categories__slug')
#     class Meta:
#         model = Product
#         fields = ['category']


    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     tag_choices = self.data.getlist('tags')
    #     print(tag_choices)
        # print(args, kwargs)

        # self.extra['choices'] += [
        #     ('relevance', 'Relevance'),
        #     ('-relevance', 'Relevance (descending)'),
        # ]

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.data.getlist("type")


class RecipeViewSet(ModelViewSet):
    """Вьюсет рецептов."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        # Добавляем фильтрацию по is_favorited, is_in_shopping_cart.
        # print(self.request.query_params)
        queryset = Recipe.objects.all()
        user = self.request.user
        if user.is_authenticated:
            favorited = self.request.query_params.get('is_favorited')
            if favorited:
                return user.is_favorited.all()
            in_shopping_cart = self.request.query_params.get(
                'is_in_shopping_cart')
            if in_shopping_cart:
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
        response = {'short-link': f'{SHORT_LINK_PREFIX}{recipe.short_link}'}
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
            for ingred in recipe_serializer.data['ingredients']:
                key = f"{ingred['name']} ({ingred['measurement_unit']})"
                value = ingred['amount']
                if key in shopping_dict:
                    shopping_dict[key] += value
                else:
                    shopping_dict[key] = value
        response = HttpResponse(content_type='text/plain')
        response.write('<p>Список покупок:</p><p></p>')
        for position in shopping_dict:
            response.write(f'<p>{position} - {shopping_dict[position]}</p>')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(
            SHOPPING_CART_FILENAME
        )
        return response


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
        if 'avatar' in request.data:
            # return Response(status=status.HTTP_400_BAD_REQUEST)
            user = self.request.user
            serializer = CustomUserSerializer(
                user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response = {'avatar': serializer.data['avatar']}
                return Response(response, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Удаление аватара пользователя."""
        user = self.request.user
        serializer = CustomUserSerializer(
            user, data={'avatar': None}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
