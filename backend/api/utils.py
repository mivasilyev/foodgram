from django.shortcuts import get_object_or_404, redirect

# from constants import SHORT_LINK_PREFIX
from recipes.models import Recipe


def redirect_to_full_link(request, short_link):
    """По короткой ссылке находим рецепт и перенаправляем пользователя."""
    recipe = get_object_or_404(Recipe, short_link=short_link)
    # full_link = f'{SHORT_LINK_PREFIX}/api/recipes/{recipe.id}/'
    full_link = f'/api/recipes/{recipe.id}/'
    return redirect(full_link)
