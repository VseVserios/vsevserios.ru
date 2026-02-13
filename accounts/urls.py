from django.urls import path

from .views import (
    SignInView,
    SignOutView,
    account_settings,
    deactivate_account,
    delete_account,
    notifications_list,
    notifications_mark_all_read,
    notifications_mark_read,
    password_reset_code,
    password_reset_done,
    password_reset_request,
    password_change,
    register,
    resend_verification,
    verify_email_view,
)

urlpatterns = [
    path("login/", SignInView.as_view(), name="login"),
    path("logout/", SignOutView.as_view(), name="logout"),
    path("register/", register, name="register"),

    path("password-reset/", password_reset_request, name="password_reset_request"),
    path("password-reset/code/", password_reset_code, name="password_reset_code"),
    path("password-reset/done/", password_reset_done, name="password_reset_done"),

    path("settings/", account_settings, name="account_settings"),
    path("settings/password/", password_change, name="password_change"),
    path("settings/deactivate/", deactivate_account, name="account_deactivate"),
    path("settings/delete/", delete_account, name="account_delete"),

    path("notifications/", notifications_list, name="notifications"),
    path("notifications/<int:notification_id>/read/", notifications_mark_read, name="notifications_mark_read"),
    path("notifications/mark-all-read/", notifications_mark_all_read, name="notifications_mark_all_read"),

    path("verify-email/", verify_email_view, name="verify_email"),
    path("verify-email/resend/", resend_verification, name="resend_verification"),
]
