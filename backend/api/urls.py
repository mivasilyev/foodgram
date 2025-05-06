from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter

from api.views import (CustomUserViewSet,
                    #    DownloadShoppingCartView, AvatarAPIView
                       IngredientViewSet, RecipeViewSet,
                       TagViewSet)  # ShoppingCartAPIView GetShortLinkAPIView

router = SimpleRouter()

router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet)
router.register('users', CustomUserViewSet)

# recipes_urls = [
#     # path('<int:id>/shopping_cart/', ShoppingCartAPIView.as_view()),
#     # path('<int:id>/get-link/', GetShortLinkAPIView.as_view()),
#     path('download_shopping_cart/', DownloadShoppingCartView.as_view()),
# ]

urlpatterns = [
    # path('recipes/', include(recipes_urls)),
    # path('users/me/avatar/', AvatarAPIView.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]
