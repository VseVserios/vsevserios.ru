from django.urls import path

from .views import (
    blocked_users,
    edit_profile,
    me,
    onboarding,
    photo_delete,
    photo_move,
    photos_manage,
    photo_set_avatar,
    public_profile,
    questionnaire,
    upload_photo,
)

urlpatterns = [
    path("onboarding/", onboarding, name="onboarding"),
    path("me/", me, name="me"),
    path("me/edit/", edit_profile, name="edit_profile"),
    path("me/questionnaire/<str:kind>/", questionnaire, name="questionnaire"),
    path("me/blocks/", blocked_users, name="blocked_users"),
    path("me/photos/upload/", upload_photo, name="upload_photo"),
    path("me/photos/", photos_manage, name="photos_manage"),
    path("me/photos/<int:photo_id>/delete/", photo_delete, name="photo_delete"),
    path("me/photos/<int:photo_id>/move/<str:direction>/", photo_move, name="photo_move"),
    path("me/photos/<int:photo_id>/set-avatar/", photo_set_avatar, name="photo_set_avatar"),
    path("<int:user_id>/", public_profile, name="public_profile"),
]
