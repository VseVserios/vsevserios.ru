from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserNotification


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "event", "title", "is_read", "created_at")
    list_filter = ("event", "is_read", "created_at")
    search_fields = ("title", "body", "recipient__username", "recipient__email")
