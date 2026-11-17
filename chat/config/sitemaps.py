from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from profiles.models import Profile


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ["landing"]

    def location(self, item):
        return reverse(item)


class PublicProfilesSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return (
            Profile.objects.select_related("user")
            .filter(user__is_active=True)
            .order_by("-updated_at")
        )

    def location(self, obj: Profile):
        return reverse("public_profile", args=[obj.user_id])

    def lastmod(self, obj: Profile):
        return obj.updated_at
