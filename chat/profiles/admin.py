from django.contrib import admin

from .models import Profile, ProfilePhoto


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "display_name", "city", "gender", "looking_for")
    search_fields = ("user__username", "display_name", "city")


@admin.register(ProfilePhoto)
class ProfilePhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "order", "created_at")
