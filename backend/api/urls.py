from django.urls import include, path
from rest_framework.routers import SimpleRouter

from api.views import (ExtendedUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)

router = SimpleRouter()

router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet)
router.register('users', ExtendedUserViewSet)

urlpatterns = [
    path(r'auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
]
