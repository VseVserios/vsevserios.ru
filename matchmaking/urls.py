from django.urls import path

from .views import (
    block_user,
    feed,
    matches,
    recommendation_compatibility,
    recommendation_excel,
    report_user,
    swipe,
    unblock_user,
    undo_swipe,
)

urlpatterns = [
    path("feed/", feed, name="feed"),
    path("swipe/<int:user_id>/<str:value>/", swipe, name="swipe"),
    path("swipe/undo/", undo_swipe, name="swipe_undo"),
    path("matches/", matches, name="matches"),
    path(
        "recommendations/<int:user_id>/compatibility/",
        recommendation_compatibility,
        name="recommendation_compatibility",
    ),
    path(
        "recommendations/<int:user_id>/excel/",
        recommendation_excel,
        name="recommendation_excel",
    ),
    path("users/<int:user_id>/block/", block_user, name="block_user"),
    path("users/<int:user_id>/unblock/", unblock_user, name="unblock_user"),
    path("users/<int:user_id>/report/", report_user, name="report_user"),
]
