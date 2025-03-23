from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Subscribe, MyUser


@admin.register(MyUser)
class MyUserAdmin(UserAdmin):
    """Админка для пользователей."""

    # fieldsets = UserAdmin.fieldsets + (
    #     ('Extra Fields', {'fields': ('avatar',)}),
    # )
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff'
    )  # , 'avatar'
    search_fields = ('email', 'username')
    list_filter = UserAdmin.list_filter + ('first_name',)


# @admin.register(Subscribe)
# class SubscribeAdmin(admin.ModelAdmin):
#     """Админка для подписок."""

#     list_display = ('user', 'following')
#     search_fields = ('user', 'following')
