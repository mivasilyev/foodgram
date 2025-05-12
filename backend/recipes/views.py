from django.http import HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from recipes.models import Recipe


@api_view(['GET'])
@permission_classes([AllowAny])
def short_link_redirect(request, short_link):
    """Редирект коротких ссылок на рецепт."""
    recipe_id = int(short_link, 16)
    # recipe = get_object_or_404(Recipe, id=recipe_id)
    if Recipe.objects.filter(id=recipe_id).exists():
        # redir_link = f'/recipes/{recipe.id}/'
        # full_link = request.build_absolute_uri(redir_link)
        # return HttpResponsePermanentRedirect(full_link)
        return redirect(f'/recipes/{recipe_id}/')
