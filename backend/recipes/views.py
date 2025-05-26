from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from recipes.models import Recipe


@api_view(['GET'])
@permission_classes([AllowAny])
def short_link_redirect(request, recipe_id):
    """Редирект коротких ссылок на рецепт."""
    # recipe_id = int(short_link, 16)
    if Recipe.objects.filter(id=recipe_id).exists():
        return redirect(f'/recipes/{recipe_id}/')
    return HttpResponseNotFound
