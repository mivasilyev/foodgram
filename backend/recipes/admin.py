from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from recipes.models import (Favorite, Ingredient, Ingredients, User, Recipe,
                            ShoppingCart, Subscribe, Tag)

admin.site.unregister(Group)

@admin.register(User)
class MyUserAdmin(UserAdmin):
    """Админка для пользователей."""

    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff', 'avatar'
    )
    search_fields = ('email', 'username')
    list_filter = UserAdmin.list_filter + ('first_name',)


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Админка для подписок."""

    list_display = ('user', 'subscribed')
    search_fields = ('user__username', 'subscribed__username')


class RecipeIngredientsInline(admin.StackedInline):
    model = Ingredients
    extra = 0
    verbose_name = 'ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = ('author', 'name')
    fields = (
        'name', 'favorited_count', 'author', 'image', 'text', 'tags',
        'cooking_time', 'pub_date',  # 'short_link'
    )
    readonly_fields = ('favorited_count', 'pub_date')
    search_fields = ('author__username', 'name',)
    list_filter = ('tags',)
    inlines = (RecipeIngredientsInline,)

    @admin.display(description='В избранном')
    def favorited_count(self, recipe):
        return recipe.favorite.all().count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ('name', 'measurement_unit',)
    list_display_links = ('name',)
    search_fields = ('name',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для корзины покупок."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
