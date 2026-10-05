from django.urls import path

from .views import (
    SignInView,
    SignOutView,
    accept_privacy,
    accept_terms,
    account_settings,
    consent_history,
    deactivate_account,
    delete_account,
    forgot_username,
    give_religious_consent,
    give_sexual_consent,
    give_special_category_consent,
    legal_photo_rules,
    legal_privacy,
    legal_site_rules,
    legal_special_category,
    legal_terms,
    notifications_open,
    notifications_list,
    notifications_mark_all_read,
    notifications_mark_read,
    password_reset_code,
    password_reset_done,
    password_reset_request,
    password_change,
    payment_page,
    payment_self_search_subscribe,
    payment_topup,
    register,
    resend_verification,
    revoke_special_category_consent,
    verify_email_view,
)

urlpatterns = [
    path("login/", SignInView.as_view(), name="login"),
    path("logout/", SignOutView.as_view(), name="logout"),
    path("register/", register, name="register"),

    path("legal/terms/", legal_terms, name="legal_terms"),
    path("legal/privacy/", legal_privacy, name="legal_privacy"),
    path("legal/photo-rules/", legal_photo_rules, name="legal_photo_rules"),
    path("legal/site-rules/", legal_site_rules, name="legal_site_rules"),
    path("legal/special-category/", legal_special_category,
         name="legal_special_category"),

    path("settings/consents/history/", consent_history, name="consent_history"),
    path(
        "settings/consents/special-category/revoke/",
        revoke_special_category_consent,
        name="revoke_special_category_consent",
    ),
    path(
        "settings/consents/special-category/give/",
        give_special_category_consent,
        name="give_special_category_consent",
    ),
    path(
        "settings/consents/sexual/give/",
        give_sexual_consent,
        name="give_sexual_consent",
    ),
    path(
        "settings/consents/religious/give/",
        give_religious_consent,
        name="give_religious_consent",
    ),
    path(
        "settings/consents/terms/accept/",
        accept_terms,
        name="accept_terms",
    ),
    path(
        "settings/consents/privacy/accept/",
        accept_privacy,
        name="accept_privacy",
    ),

    path("payment/", payment_page, name="payment"),
    path("payment/topup/", payment_topup, name="payment_topup"),
    path("payment/self-search/subscribe/",
         payment_self_search_subscribe, name="payment_self_search"),

    path("forgot-username/", forgot_username, name="forgot_username"),

    path("password-reset/", password_reset_request,
         name="password_reset_request"),
    path("password-reset/code/", password_reset_code, name="password_reset_code"),
    path("password-reset/done/", password_reset_done, name="password_reset_done"),

    path("settings/", account_settings, name="account_settings"),
    path("settings/password/", password_change, name="password_change"),
    path("settings/deactivate/", deactivate_account, name="account_deactivate"),
    path("settings/delete/", delete_account, name="account_delete"),

    path("notifications/", notifications_list, name="notifications"),
    path(
        "notifications/<int:notification_id>/open/",
        notifications_open,
        name="notifications_open",
    ),
    path("notifications/<int:notification_id>/read/",
         notifications_mark_read, name="notifications_mark_read"),
    path("notifications/mark-all-read/", notifications_mark_all_read,
         name="notifications_mark_all_read"),

    path("verify-email/", verify_email_view, name="verify_email"),
    path("verify-email/resend/", resend_verification, name="resend_verification"),
]
