from django.contrib import admin
from django.urls import include, path

from api.utils import redirect_to_full_link

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('<str:short_link>', redirect_to_full_link),
]
