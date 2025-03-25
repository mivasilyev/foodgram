from rest_framework import permissions
from djoser.permissions import CurrentUserOrAdminOrReadOnly


class CustomUserPermission(CurrentUserOrAdminOrReadOnly):

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            and 'users/me/' not in request.path
            or request.user.is_authenticated
        )

    # def has_object_permission(self, request, view, obj):
    #     return (
    #         request.method in permissions.SAFE_METHODS
    #         or obj.author == request.user
    #     )

    # def has_object_permission(self, request, view, obj):
    #     user = request.user
    #     if type(obj) == type(user) and obj == user:
    #         return True
    #     return request.method in SAFE_METHODS or user.is_staff