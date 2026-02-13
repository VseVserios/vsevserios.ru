from django.contrib import admin

from .models import (
    HomeBlock,
    HomePage,
    Match,
    Swipe,
    UserBan,
    UserBlock,
    UserRecommendation,
    UserReport,
)


class HomeBlockInline(admin.TabularInline):
    model = HomeBlock
    extra = 0
    fields = (
        "order",
        "is_active",
        "type",
        "badge",
        "title",
        "subtitle",
        "primary_button_text",
        "primary_button_url",
        "secondary_button_text",
        "secondary_button_url",
        "image",
        "items",
        "extra",
    )
    ordering = ("order", "id")


@admin.register(HomePage)
class HomePageAdmin(admin.ModelAdmin):
    list_display = ("slug", "title", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("slug", "title")
    inlines = [HomeBlockInline]


@admin.register(Swipe)
class SwipeAdmin(admin.ModelAdmin):
    list_display = ("id", "from_user", "to_user", "value", "created_at")
    list_filter = ("value",)
    search_fields = ("from_user__username", "to_user__username")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "user1", "user2", "created_at")
    search_fields = ("user1__username", "user2__username")


@admin.register(UserBlock)
class UserBlockAdmin(admin.ModelAdmin):
    list_display = ("id", "blocker", "blocked", "created_at")
    search_fields = ("blocker__username", "blocked__username")


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "reported_user", "reason", "resolved", "created_at")
    list_filter = ("reason", "resolved")
    search_fields = ("reporter__username", "reported_user__username", "message")


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "reason",
        "created_at",
        "expires_at",
        "revoked_at",
    )
    list_filter = ("reason",)
    search_fields = ("user__username", "user__email", "note")


@admin.register(UserRecommendation)
class UserRecommendationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "to_user",
        "recommended_user",
        "score",
        "created_by",
        "created_at",
        "seen_at",
        "consumed_at",
    )
    search_fields = (
        "to_user__username",
        "recommended_user__username",
        "note",
    )
