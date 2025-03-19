from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin

from recipes.models import Ingredient, IngredientRecipe, Recipe, Tag

# @admin.register(MyUser)
# class UsersUserAdmin(UserAdmin):
#     """Админка для пользователей."""

#     fieldsets = UserAdmin.fieldsets + (
#         ('Extra Fields', {'fields': ('avatar',)}),
#     )
#     list_display = (
#         'username', 'email', 'first_name', 'last_name', 'is_staff', 'avatar')
#     search_fields = ('email', 'username')
#     list_filter = UserAdmin.list_filter + ('first_name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = ('author', 'name',)
    search_fields = ('author', 'name',)
    # list_filter = ('tag',)
# в списке рецептов вывести название и имя автора рецепта;
# добавить поиск по автору, названию рецепта, и фильтрацию по тегам;
# на странице рецепта вывести общее число добавлений этого рецепта в избранное.


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ('name', 'measurement_unit',)
    list_display_links = ('name',)
    search_fields = ('name',)

# для модели ингредиентов:
# в список вывести название ингредиента и единицы измерения;
# добавить поиск по названию.

# from django.db.models import Avg


# class GenreTitleInline(admin.StackedInline):
#     model = GenreTitle
#     extra = 1
#     verbose_name = 'жанр'
#     verbose_name_plural = 'Жанры'


# class TitleInline(admin.TabularInline):
#     model = Title
#     extra = 0
#     verbose_name = 'произведение'
#     verbose_name_plural = 'Произведения'


# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     """Админка для категорий."""

#     inlines = (TitleInline,)
#     list_display = ('name', 'slug', 'view_titles')
#     search_fields = ('name',)
#     list_filter = ('slug',)

#     @admin.display(description='Произведений')
#     def view_titles(self, obj):
#         return obj.titles.all().count()


# @admin.register(Genre)
# class GenreAdmin(admin.ModelAdmin):
#     """Админка для жанров."""

#     list_display = ('name', 'slug', 'view_titles')
#     search_fields = ('name',)
#     list_filter = ('slug',)

#     @admin.display(description='Произведений')
#     def view_titles(self, obj):
#         return obj.titles.all().count()


# @admin.register(Title)
# class TitleAdmin(admin.ModelAdmin):
#     """Админка для произведений."""

#     inlines = (GenreTitleInline,)
#     list_display = ('name', 'category', 'view_genres', 'view_reviews',
#                     'view_rating')
#     list_editable = ('category',)
#     search_fields = ('name',)
#     list_filter = ('category', 'genre')
#     list_display_links = ('name',)
#     empty_value_display = 'Не задано'

#     @admin.display(description='Жанры')
#     def view_genres(self, obj):
#         genres_qs = obj.title_genres.all()
#         genres = [genre.genre.name for genre in genres_qs]
#         return ', '.join(genres)

#     @admin.display(description='Отзывов')
#     def view_reviews(self, obj):
#         return obj.reviews.all().count()

#     @admin.display(description='Рейтинг')
#     def view_rating(self, obj):
#         rating = obj.reviews.aggregate(
#             Avg('score', default=None))['score__avg']
#         return round(rating) if rating is not None else rating


# @admin.register(Review)
# class ReviewAdmin(admin.ModelAdmin):
#     """Админка для отзывов."""

#     list_display = ('title', 'score', 'author', 'text', 'comments_count',
#                     'pub_date')
#     list_display_links = ('text',)
#     search_fields = ('title', 'author', 'score')
#     list_filter = ('title', 'author', 'score')

#     @admin.display(description='Комментариев')
#     def comments_count(self, obj):
#         comments = obj.comments.all().count()
#         return comments


# @admin.register(Comment)
# class CommentAdmin(admin.ModelAdmin):
#     """Админка для комментариев."""

#     list_display = ('review_id', 'author', 'text', 'pub_date')
#     list_display_links = ('text',)
#     list_filter = ('author',)
