from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from matchmaking.views import landing

urlpatterns = [
    path("admin/", admin.site.urls),
    path("panel/", include("panel.urls")),
    path("", landing, name="landing"),
    path("accounts/", include("accounts.urls")),
    path("profiles/", include("profiles.urls")),
    path("", include("matchmaking.urls")),
    path("chat/", include("chat.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
