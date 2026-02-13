from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils import timezone

from .email_verification import send_verification_code, verify_code
from .forms import (
    AccountSettingsForm,
    EmailVerificationForm,
    LoginForm,
    PasswordConfirmForm,
    PasswordResetCodeConfirmForm,
    PasswordResetRequestForm,
    RegisterForm,
)
from .models import EmailVerification, UserNotification

from .password_reset import send_password_reset_code, verify_password_reset_code


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.user.is_authenticated and not getattr(self.request.user, "email_verified", False):
            next_url = self.get_success_url()
            if next_url and str(next_url).startswith("/"):
                self.request.session["post_verify_next"] = next_url
            messages.error(self.request, "Подтвердите email, чтобы продолжить.")
            return redirect("verify_email")
        return response


class SignOutView(LogoutView):
    next_page = reverse_lazy("landing")


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = (form.cleaned_data.get("email") or "").strip().lower()
            request.session["password_reset_email"] = email

            UserModel = get_user_model()
            user = UserModel.objects.filter(email__iexact=email, is_active=True).first()
            if user is not None:
                ok, reason = send_password_reset_code(user, force=False)
                if not ok:
                    if reason == "email_not_configured":
                        messages.error(request, "Email-отправка не настроена на сервере.")
                    elif reason == "cooldown":
                        messages.error(request, "Подождите немного перед повторной отправкой кода.")
                    elif reason == "max_sends":
                        messages.error(request, "Превышен лимит отправок. Попробуйте позже.")
                    elif reason == "spam_rejected":
                        messages.error(
                            request,
                            "Письмо отклонено почтовым сервером (подозрение на спам). Попробуйте позже.",
                        )
                    else:
                        messages.error(request, "Не удалось отправить код. Проверьте SMTP-настройки.")
                else:
                    messages.success(request, "Если email существует, мы отправили код восстановления.")
            else:
                messages.success(request, "Если email существует, мы отправили код восстановления.")

            return redirect("password_reset_code")
    else:
        form = PasswordResetRequestForm()

    return render(request, "accounts/password_reset_request.html", {"form": form})


def password_reset_code(request):
    email = (request.session.get("password_reset_email") or "").strip()
    if not email:
        return redirect("password_reset_request")

    if request.method == "POST":
        form = PasswordResetCodeConfirmForm(request.POST)
        if form.is_valid():
            UserModel = get_user_model()
            user = UserModel.objects.filter(email__iexact=email, is_active=True).first()
            if user is None:
                form.add_error("code", "Неверный код или он истёк.")
            else:
                ok, reason = verify_password_reset_code(user, form.cleaned_data["code"])
                if not ok:
                    if reason == "expired":
                        form.add_error("code", "Код истёк. Запросите новый.")
                    elif reason == "max_attempts":
                        form.add_error("code", "Слишком много попыток. Запросите новый код.")
                    else:
                        form.add_error("code", "Неверный код.")
                else:
                    user.set_password(form.cleaned_data["new_password1"])
                    user.save(update_fields=["password"])
                    request.session.pop("password_reset_email", None)
                    messages.success(request, "Пароль изменён. Теперь вы можете войти.")
                    return redirect("password_reset_done")
    else:
        form = PasswordResetCodeConfirmForm()

    masked = email
    if "@" in email:
        name, domain = email.split("@", 1)
        if len(name) > 2:
            masked = name[:2] + "***@" + domain

    return render(
        request,
        "accounts/password_reset_code.html",
        {
            "form": form,
            "email": masked,
        },
    )


def password_reset_done(request):
    return render(request, "accounts/password_reset_done.html")


@login_required
def account_settings(request):
    user = request.user
    profile = request.user.profile
    if request.method == "POST":
        kind = (request.POST.get("settings_kind") or "account").strip().lower()

        if kind == "account":
            form = AccountSettingsForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Настройки аккаунта сохранены.")
                return redirect("account_settings")

        elif kind == "theme":
            theme = (request.POST.get("ui_theme") or profile.ui_theme).strip() or profile.ui_theme
            profile.ui_theme = theme
            profile.save(update_fields=["ui_theme", "updated_at"])
            messages.success(request, "Тема применена.")
            return redirect("account_settings")

        elif kind == "notifications":
            profile.notify_email_matches = bool(request.POST.get("notify_email_matches"))
            profile.notify_email_messages = bool(request.POST.get("notify_email_messages"))
            profile.notify_email_marketing = bool(request.POST.get("notify_email_marketing"))
            profile.save(
                update_fields=[
                    "notify_email_matches",
                    "notify_email_messages",
                    "notify_email_marketing",
                    "updated_at",
                ]
            )
            messages.success(request, "Уведомления сохранены.")
            return redirect("account_settings")

        else:
            form = AccountSettingsForm(instance=user)
    else:
        form = AccountSettingsForm(instance=user)

    return render(
        request,
        "accounts/settings.html",
        {
            "form": form,
            "profile": profile,
        },
    )


@login_required
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Пароль изменён.")
            return redirect("account_settings")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "accounts/password_change.html", {"form": form})


@login_required
def notifications_list(request):
    qs = UserNotification.objects.filter(recipient=request.user).order_by("-created_at")
    return render(request, "accounts/notifications.html", {"notifications": qs[:200]})


@login_required
def notifications_mark_read(request, notification_id: int):
    if request.method != "POST":
        raise Http404

    n = UserNotification.objects.filter(id=notification_id, recipient=request.user).first()
    if n is not None:
        n.mark_read()
    return redirect("notifications")


@login_required
def notifications_mark_all_read(request):
    if request.method != "POST":
        raise Http404

    now = timezone.now()
    UserNotification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True,
        read_at=now,
    )
    messages.success(request, "Все уведомления отмечены прочитанными.")
    return redirect("notifications")


@login_required
def deactivate_account(request):
    if request.method != "POST":
        raise Http404

    form = PasswordConfirmForm(request.POST, user=request.user)
    if not form.is_valid():
        messages.error(request, "Не удалось подтвердить пароль.")
        return redirect("account_settings")

    user = request.user
    user.is_active = False
    user.save(update_fields=["is_active"])
    logout(request)
    messages.success(request, "Аккаунт деактивирован. Вы можете обратиться в поддержку для восстановления.")
    return redirect("landing")


@login_required
def delete_account(request):
    if request.method != "POST":
        raise Http404

    form = PasswordConfirmForm(request.POST, user=request.user)
    if not form.is_valid():
        messages.error(request, "Не удалось подтвердить пароль.")
        return redirect("account_settings")

    user = request.user
    logout(request)
    user.delete()
    messages.success(request, "Аккаунт удалён.")
    return redirect("landing")


def register(request):
    if request.user.is_authenticated:
        return redirect("feed")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            ok, reason = send_verification_code(user, force=False)
            if not ok:
                if reason == "email_not_configured":
                    messages.error(request, "Email-отправка не настроена на сервере.")
                elif reason == "spam_rejected":
                    messages.error(
                        request,
                        "Письмо отклонено почтовым сервером (подозрение на спам). Попробуйте позже.",
                    )
                elif reason == "send_failed":
                    messages.error(request, "Не удалось отправить письмо с кодом. Проверьте SMTP-настройки.")
                else:
                    messages.error(request, "Не удалось отправить код подтверждения.")
            return redirect("verify_email")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def verify_email_view(request):
    if request.user.email_verified:
        next_url = request.session.pop("post_verify_next", None)
        if next_url and str(next_url).startswith("/"):
            return redirect(next_url)
        return redirect("onboarding")

    if request.method == "POST":
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            ok, reason = verify_code(request.user, form.cleaned_data["code"])
            if ok:
                messages.success(request, "Email подтверждён.")
                next_url = request.session.pop("post_verify_next", None)
                if next_url and str(next_url).startswith("/"):
                    return redirect(next_url)
                return redirect("onboarding")

            if reason == "expired":
                form.add_error("code", "Код истёк. Запросите новый.")
            elif reason == "max_attempts":
                form.add_error("code", "Слишком много попыток. Запросите новый код.")
            else:
                form.add_error("code", "Неверный код.")
    else:
        form = EmailVerificationForm()

    record, _ = EmailVerification.objects.get_or_create(user=request.user)
    now = timezone.now()
    should_send = (not record.code_hash) or (record.expires_at and now > record.expires_at)
    if should_send:
        ok, reason = send_verification_code(request.user, force=False)
        if not ok:
            if reason == "email_not_configured":
                messages.error(request, "Email-отправка не настроена на сервере.")
            elif reason == "spam_rejected":
                messages.error(
                    request,
                    "Письмо отклонено почтовым сервером (подозрение на спам). Попробуйте позже.",
                )
            elif reason == "send_failed":
                messages.error(request, "Не удалось отправить письмо с кодом. Попробуйте позже.")
            elif reason == "max_sends":
                messages.error(request, "Превышен лимит отправок кода. Попробуйте позже.")

    return render(request, "accounts/verify_email.html", {"form": form})


@login_required
def resend_verification(request):
    if request.method != "POST":
        raise Http404

    if request.user.email_verified:
        return redirect("onboarding")

    ok, reason = send_verification_code(request.user, force=False)
    if ok:
        messages.success(request, "Код отправлен.")
    else:
        if reason == "cooldown":
            messages.error(request, "Подождите немного перед повторной отправкой.")
        elif reason == "max_sends":
            messages.error(request, "Превышен лимит отправок кода. Попробуйте позже.")
        elif reason == "email_not_configured":
            messages.error(request, "Email-отправка не настроена на сервере.")
        elif reason == "spam_rejected":
            messages.error(
                request,
                "Письмо отклонено почтовым сервером (подозрение на спам). Попробуйте позже.",
            )
        elif reason == "send_failed":
            messages.error(request, "Не удалось отправить письмо с кодом. Попробуйте позже.")
        else:
            messages.error(request, "Не удалось отправить код.")

    return redirect("verify_email")
