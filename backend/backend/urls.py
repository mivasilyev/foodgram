from django.contrib import admin
from django.urls import include, path, re_path

from api.views import short_link_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('s/<str:short_link>/', short_link_redirect)
    # re_path(r'^s/(?P<short_link>[а-яёА-ЯЁ\-]+)/$', short_link_redirect),
    # re_path(r'^s/(?P<short_link>[a-zA-Z\-]+)/$', short_link_redirect),
]
