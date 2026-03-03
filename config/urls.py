from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from matchmaking.views import landing, robots_txt, sitemap_xml

urlpatterns = [
    path("admin/", admin.site.urls),
    path("panel/", include("panel.urls")),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_xml, name="sitemap_xml"),
    path("", landing, name="landing"),
    path("accounts/", include("accounts.urls")),
    path("profiles/", include("profiles.urls")),
    path("", include("matchmaking.urls")),
    path("chat/", include("chat.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
