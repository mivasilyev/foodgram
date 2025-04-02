from api.views import (AvatarAPIView, CustomUserViewSet, FavoriteAPIView,
                       IngredientViewSet, RecipeViewSet, ShoppingCartAPIView,
                       ShortLinkAPIView, TagViewSet)
from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter

router = SimpleRouter()

router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet)
router.register('users', CustomUserViewSet)

urlpatterns = [
    path('recipes/<int:id>/favorite/', FavoriteAPIView.as_view()),
    path('recipes/<int:id>/delete/', FavoriteAPIView.as_view()),
    path('recipes/<int:id>/shopping_cart/', ShoppingCartAPIView.as_view()),
    path('recipes/<int:id>/get-link/', ShortLinkAPIView.as_view()),

    path('users/me/avatar/', AvatarAPIView.as_view()),

    path('', include(router.urls)),
    path('', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
