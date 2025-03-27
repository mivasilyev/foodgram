from api.views import (AvatarAPIView, FavoriteAPIView, ShortLinkAPIView,
                       IngredientViewSet, RecipeViewSet, ShoppingCartAPIView,
                       TagViewSet, UserSubscriptionView)
from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter

router = SimpleRouter()

router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)
router.register('ingredients', IngredientViewSet)

urlpatterns = [
    path('recipes/<int:id>/favorite/', FavoriteAPIView.as_view()),
    path('recipes/<int:id>/delete/', FavoriteAPIView.as_view()),
    path('recipes/<int:id>/shopping_cart/', ShoppingCartAPIView.as_view()),
    path('recipes/<int:id>/get-link/', ShortLinkAPIView.as_view()),

    path('users/<int:id>/subscribe/', UserSubscriptionView.as_view()),
    path('users/me/avatar/', AvatarAPIView.as_view()),

    # path('recipes/', RecipeAPIView.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
