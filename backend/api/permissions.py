from rest_framework import permissions
from djoser.permissions import CurrentUserOrAdminOrReadOnly


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Изменение автором."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class UsersMeUserPermission(CurrentUserOrAdminOrReadOnly):
    """Ограничение доступа незарегистрированным пользователям к users/me/."""

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            and 'users/me/' not in request.path
            or request.user.is_authenticated
        )
