from api.views import (AvatarAPIView, FavoriteAPIView, RecipeViewSet,
                       TagViewSet, UserSubscriptionView)
from django.urls import include, path, re_path
from rest_framework.routers import SimpleRouter

router = SimpleRouter()

router.register('tags', TagViewSet)
router.register('recipes', RecipeViewSet)

urlpatterns = [
    path('recipes/<int:id>/favorite/', FavoriteAPIView.as_view()),
    path('recipes/<int:id>/delete/', FavoriteAPIView.as_view()),
    path('users/<int:id>/subscribe/', UserSubscriptionView.as_view()),
    path('users/me/avatar/', AvatarAPIView.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
]

# Работает:
# POST   /api/users/  создать пользователя
# POST   /api/auth/token/login/  получить токен авторизации
# POST   /api/auth/token/logout/ удалить токен
# GET    /api/users/me/ профиль текущего пользователя
# POST   /api/users/set_password/ изменение пароля текущего пользователя

# Не работает:
# PUT    /api/users/me/avatar/ добавление аватара
# DELETE /api/users/me/avatar/ удаление аватара

# GET    /api/users/  список пользователей
# GET    /api/users/{id}/  профиль пользователя
