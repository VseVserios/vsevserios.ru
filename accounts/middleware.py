from django.contrib import messages
from django.contrib.auth import logout
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from matchmaking.models import UserBan


class BannedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if UserBan.objects.active().filter(user=request.user).exists():
                logout(request)
                messages.error(request, "Доступ ограничен: ваш аккаунт заблокирован модерацией.")
                return redirect("login")

        return self.get_response(request)


class EmailVerificationRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "REQUIRE_EMAIL_VERIFICATION", True):
            return self.get_response(request)

        if request.user.is_authenticated and not getattr(request.user, "email_verified", False):
            path = request.path
            
            # Администраторы имеют доступ ко всем функциям, включая рассылку
            if request.user.is_superuser and path.startswith("/chat/newsletter/"):
                return self.get_response(request)

            def _safe_reverse(name: str):
                try:
                    return reverse(name)
                except NoReverseMatch:
                    return None

            allowed_prefixes = (
                _safe_reverse("verify_email"),
                _safe_reverse("resend_verification"),
                _safe_reverse("resend_verification_code"),
                _safe_reverse("password_reset_request"),
                _safe_reverse("password_reset_code"),
                _safe_reverse("password_reset_done"),
                _safe_reverse("logout"),
                "/accounts/verify-email/",
                "/accounts/verify-email/resend/",
                "/accounts/password-reset/",
                "/admin/",
                "/static/",
                "/media/",
            )

            allowed_prefixes = tuple(p for p in allowed_prefixes if p)

            if not any(path.startswith(p) for p in allowed_prefixes):
                if request.method == "GET":
                    next_url = request.get_full_path()
                    if next_url and str(next_url).startswith("/"):
                        request.session["post_verify_next"] = next_url
                messages.error(request, "Подтвердите email, чтобы продолжить.")
                return redirect("verify_email")

        return self.get_response(request)


class TermsAndPrivacyRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, "REQUIRE_TERMS_AND_PRIVACY", True):
            return self.get_response(request)

        if request.user.is_authenticated:
            user = request.user
            terms_accepted = bool(user.terms_accepted_at)
            privacy_accepted = bool(user.privacy_accepted_at)

            if not terms_accepted or not privacy_accepted:
                path = request.path

                def _safe_reverse(name: str):
                    try:
                        return reverse(name)
                    except NoReverseMatch:
                        return None

                allowed_prefixes = (
                    _safe_reverse("legal_terms"),
                    _safe_reverse("legal_privacy"),
                    _safe_reverse("account_settings"),
                    _safe_reverse("logout"),
                    "/accounts/legal/terms/",
                    "/accounts/legal/privacy/",
                    "/accounts/settings/",
                    "/accounts/logout/",
                    "/static/",
                    "/media/",
                )

                allowed_prefixes = tuple(p for p in allowed_prefixes if p)

                if not any(path.startswith(p) for p in allowed_prefixes):
                    if not terms_accepted and not privacy_accepted:
                        messages.error(
                            request,
                            "Для продолжения работы необходимо принять Пользовательское соглашение и Политику обработки персональных данных."
                        )
                    elif not terms_accepted:
                        messages.error(
                            request,
                            "Для продолжения работы необходимо принять Пользовательское соглашение."
                        )
                    elif not privacy_accepted:
                        messages.error(
                            request,
                            "Для продолжения работы необходимо принять Политику обработки персональных данных."
                        )
                    return redirect("account_settings")

        return self.get_response(request)
