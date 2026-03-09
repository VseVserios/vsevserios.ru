from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path

from config.sitemaps import PublicProfilesSitemap, StaticViewSitemap
from matchmaking.views import landing, robots_txt


def yandex_webmaster_verification(request):
    content = (settings.BASE_DIR / "yandex_9ea13c1b28a1285c.html").read_text(encoding="utf-8")
    return HttpResponse(content, content_type="text/html; charset=utf-8")

sitemaps = {
    "static": StaticViewSitemap,
    "profiles": PublicProfilesSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("panel/", include("panel.urls")),
    path(
        "yandex_9ea13c1b28a1285c.html",
        yandex_webmaster_verification,
        name="yandex_webmaster_verification",
    ),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap_xml"),
    path("", landing, name="landing"),
    path("accounts/", include("accounts.urls")),
    path("profiles/", include("profiles.urls")),
    path("", include("matchmaking.urls")),
    path("chat/", include("chat.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
