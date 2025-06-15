from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    """Редирект коротких ссылок на рецепт."""
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404(f'Рецепт {recipe_id} не найден')
        # raise ValidationError(f'Рецепт {recipe_id} не найден')
    return redirect(f'/recipes/{recipe_id}/')
