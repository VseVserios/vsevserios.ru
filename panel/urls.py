from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="panel_dashboard"),

    path("home/", views.home_pages, name="panel_home_pages"),
    path("home/new/", views.home_page_create, name="panel_home_page_create"),
    path("home/<int:page_id>/", views.home_page_edit, name="panel_home_page_edit"),
    path(
        "home/<int:page_id>/blocks/new/",
        views.home_block_create,
        name="panel_home_block_create",
    ),
    path("home/blocks/<int:block_id>/", views.home_block_edit, name="panel_home_block_edit"),
    path(
        "home/blocks/<int:block_id>/delete/",
        views.home_block_delete,
        name="panel_home_block_delete",
    ),

    path("users/", views.users_list, name="panel_users"),
    path("users/<int:user_id>/", views.user_detail, name="panel_user_detail"),
    path(
        "users/<int:user_id>/compatibility/<int:other_user_id>/",
        views.user_compatibility_report,
        name="panel_user_compatibility_report",
    ),
    path("users/<int:user_id>/delete/", views.user_delete, name="panel_user_delete"),
    path(
        "users/<int:user_id>/recommendations/",
        views.user_recommendations,
        name="panel_user_recommendations",
    ),
    path(
        "users/<int:user_id>/recommendations/send/",
        views.user_recommend_send,
        name="panel_user_recommend_send",
    ),
    path(
        "users/<int:user_id>/ban/",
        views.user_ban,
        name="panel_user_ban",
    ),
    path(
        "users/<int:user_id>/password/",
        views.user_set_password,
        name="panel_user_set_password",
    ),
    path(
        "users/<int:user_id>/toggle-active/",
        views.user_toggle_active,
        name="panel_user_toggle_active",
    ),
    path("profiles/", views.profiles_list, name="panel_profiles"),
    path(
        "profiles/<int:profile_id>/",
        views.profile_detail,
        name="panel_profile_detail",
    ),

    path("questionnaire/sections/", views.questionnaire_sections, name="panel_questionnaire_sections"),
    path(
        "questionnaire/sections/new/",
        views.questionnaire_section_create,
        name="panel_questionnaire_section_create",
    ),
    path(
        "questionnaire/sections/<int:section_id>/",
        views.questionnaire_section_edit,
        name="panel_questionnaire_section_edit",
    ),
    path(
        "questionnaire/sections/<int:section_id>/delete/",
        views.questionnaire_section_delete,
        name="panel_questionnaire_section_delete",
    ),
    path(
        "questionnaire/sections/<int:section_id>/questions/new/",
        views.questionnaire_question_create,
        name="panel_questionnaire_question_create",
    ),
    path(
        "questionnaire/questions/<int:question_id>/",
        views.questionnaire_question_edit,
        name="panel_questionnaire_question_edit",
    ),
    path(
        "questionnaire/questions/<int:question_id>/delete/",
        views.questionnaire_question_delete,
        name="panel_questionnaire_question_delete",
    ),
    path(
        "questionnaire/questions/<int:question_id>/choices/new/",
        views.questionnaire_choice_create,
        name="panel_questionnaire_choice_create",
    ),
    path(
        "questionnaire/choices/<int:choice_id>/",
        views.questionnaire_choice_edit,
        name="panel_questionnaire_choice_edit",
    ),
    path(
        "questionnaire/choices/<int:choice_id>/delete/",
        views.questionnaire_choice_delete,
        name="panel_questionnaire_choice_delete",
    ),
    path("photos/", views.photos_list, name="panel_photos"),
    path("photos/<int:photo_id>/delete/", views.photo_delete, name="panel_photo_delete"),
    path("swipes/", views.swipes_list, name="panel_swipes"),
    path("swipes/<int:swipe_id>/delete/", views.swipe_delete, name="panel_swipe_delete"),
    path("matches/", views.matches_list, name="panel_matches"),
    path("matches/<int:match_id>/delete/", views.match_delete, name="panel_match_delete"),
    path("messages/", views.messages_list, name="panel_messages"),
    path(
        "messages/<int:message_id>/delete/",
        views.message_delete,
        name="panel_message_delete",
    ),

    path("reports/", views.reports_list, name="panel_reports"),
    path(
        "reports/<int:report_id>/resolve/",
        views.report_resolve,
        name="panel_report_resolve",
    ),
    path("blocks/", views.blocks_list, name="panel_blocks"),
    path(
        "blocks/<int:block_id>/delete/",
        views.block_delete,
        name="panel_block_delete",
    ),

    path("bans/", views.bans_list, name="panel_bans"),
    path("bans/new/", views.ban_create, name="panel_ban_create"),
    path(
        "bans/<int:ban_id>/revoke/",
        views.ban_revoke,
        name="panel_ban_revoke",
    ),
]
