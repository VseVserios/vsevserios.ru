from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import Http404, HttpResponse
from django.urls import include, path, re_path

from config.sitemaps import PublicProfilesSitemap, StaticViewSitemap
from matchmaking.views import landing, robots_txt


def yandex_webmaster_verification(request, hash: str):
    filename = f"yandex_{hash}.html"
    file_path = settings.BASE_DIR / filename
    if not file_path.exists():
        raise Http404
    content = file_path.read_text(encoding="utf-8")
    return HttpResponse(content, content_type="text/html; charset=utf-8")


def google_search_console_verification(request):
    content = (settings.BASE_DIR / "google05ced95716c6d480.html").read_text(encoding="utf-8")
    return HttpResponse(content, content_type="text/html; charset=utf-8")

sitemaps = {
    "static": StaticViewSitemap,
    "profiles": PublicProfilesSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("panel/", include("panel.urls")),
    re_path(
        r"^yandex_(?P<hash>[0-9a-f]{16})\.html$",
        yandex_webmaster_verification,
        name="yandex_webmaster_verification",
    ),
    path(
        "google05ced95716c6d480.html",
        google_search_console_verification,
        name="google_search_console_verification",
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
