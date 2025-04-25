from django.urls import path

from api.views import short_link_redirect

urlpatterns = [
    path('<slug:short_link>', short_link_redirect),
]
