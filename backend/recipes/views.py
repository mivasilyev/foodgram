from django.http import Http404  # HttpResponseNotFound
from django.shortcuts import redirect
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny

from recipes.models import Recipe


# @api_view(['GET'])
# @permission_classes([AllowAny])
def short_link_redirect(request, recipe_id):
    """Редирект коротких ссылок на рецепт."""
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404(f'Рецепт {recipe_id} не найден')
    print('redirecting')
    return redirect(f'/recipes/{recipe_id}/')

    # if Recipe.objects.filter(id=recipe_id).exists():
    #     return redirect(f'/recipes/{recipe_id}/')
    # return HttpResponseNotFound
