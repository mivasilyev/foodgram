from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from constants import ADMIN_PIC_DOTS
from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Subscribe,
    Tag, User
)

admin.site.unregister(Group)


class BaseFilter(admin.SimpleListFilter):
    """Базовый класс для фильтра рецептов и подписок."""

    selections = (
        ('0', 'Нет'),
        ('1', 'Есть'),
    )

    def lookups(self, request, model_admin):
        return self.selections

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(**self.filter_kwargs())
        if self.value() == '1':
            return queryset.exclude(**self.filter_kwargs())

    def filter_kwargs(self):
        return {f"{self.parameter_name}__exact": None}


class RecipeFilter(BaseFilter):

    title = 'Наличие рецептов'
    parameter_name = 'recipes'
    selections = (
        ('0', 'Нет рецептов'),
        ('1', 'Есть рецепты'),
    )


class FollowsFilter(BaseFilter):

    title = 'Пользователь подписан'
    parameter_name = 'follows'
    selections = (
        ('0', 'Нет подписок'),
        ('1', 'Есть подписки'),
    )


class IsFollowedFilter(BaseFilter):

    title = 'Есть подписчики'
    parameter_name = 'authors'
    selections = (
        ('0', 'Нет подписчиков'),
        ('1', 'Есть подписчики'),
    )


class RecipesCountMixin:
    """Подсчет количества рецептов, связанных с объектом смежной модели."""

    list_display = ['recipes_count', ]

    @admin.display(description='Рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()


@admin.register(User)
class FoodgramUserAdmin(UserAdmin, RecipesCountMixin):
    """Админка для пользователей."""

    list_display = [
        'avatar_preview', 'id', 'username', 'name', 'email', 'is_staff',
        *RecipesCountMixin.list_display,
        'subscribed_count', 'authors_count'
    ]
    list_display_links = ('username', )
    readonly_fields = ['avatar_preview']
    search_fields = ('email', 'username')
    list_filter = UserAdmin.list_filter + (
        RecipeFilter, FollowsFilter, IsFollowedFilter
    )

    @admin.display(description='ФИО')
    def name(self, user):
        return f'{user.first_name} {user.last_name}'

    @admin.display(description='Подписок')
    def subscribed_count(self, user):
        return user.follows.count()

    @admin.display(description='Подписчиков')
    def authors_count(self, user):
        return user.authors.count()

    @mark_safe
    @admin.display(description='Аватар')
    def avatar_preview(self, user):
        return (
            f'<img src="{user.avatar}" width="{ADMIN_PIC_DOTS}" '
            f'height="{ADMIN_PIC_DOTS}"/>'
        )


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    """Админка для подписок."""

    list_display = ('user', 'subscribed')
    search_fields = ('user__username', 'subscribed__username')


class RecipeIngredientsInline(admin.StackedInline):
    model = IngredientInRecipe
    extra = 0
    verbose_name = 'продукт'
    verbose_name_plural = 'Продукты'


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    """Админка для тегов."""

    list_display = ['name', 'slug', *RecipesCountMixin.list_display]
    search_fields = ('name', 'slug')
    counter_description = 'Рецептов с тегом'


class UsedIngredientFilter(admin.SimpleListFilter):
    title = 'Используются в рецептах'
    parameter_name = 'recipes_count'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Только используемые'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(recipes__exact=None)


@admin.register(Ingredient)
class IngredientAdmin(RecipesCountMixin, admin.ModelAdmin):
    """Админка для продуктов."""

    list_display = [
        'name', 'measurement_unit', *RecipesCountMixin.list_display
    ]
    list_display_links = ('name',)
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', UsedIngredientFilter)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = (
        'image_preview', 'id', 'name', 'cooking_time', 'author', 'view_tags',
        'favorited_count', 'view_ingredients'
    )
    fields = (
        'name', 'favorited_count', 'author', 'text', 'tags',
        'cooking_time', 'pub_date',
    )
    list_display_links = ('name', )
    readonly_fields = ('image_preview', 'favorited_count', 'pub_date')
    search_fields = ('author__username', 'name', 'tags__name')
    list_filter = ('tags', 'author')
    inlines = (RecipeIngredientsInline, )

    @admin.display(description='В избранном')
    def favorited_count(self, recipe):
        return recipe.favorites.count()

    @mark_safe
    @admin.display(description='Теги')
    def view_tags(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @mark_safe
    @admin.display(description='Продукты')
    def view_ingredients(self, recipe):
        return '<br>'.join(
            (
                f'{ingr.ingredient.name} {ingr.amount} '
                f'{ingr.ingredient.measurement_unit}'
            ) for ingr in recipe.ingredients_in_recipe.all()
        )

    @mark_safe
    @admin.display(description='Превью')
    def image_preview(self, recipe):
        return (
            f'<img src="{recipe.image}" width="{ADMIN_PIC_DOTS}" '
            f'height="{ADMIN_PIC_DOTS}"/>'
        )


@admin.register(Favorite, ShoppingCart)
class FavoriteShoppingCartAdmin(admin.ModelAdmin):
    """Админка для избранного."""

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
