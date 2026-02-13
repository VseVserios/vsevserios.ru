import logging
import secrets
import smtplib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import PasswordResetCode, User

logger = logging.getLogger("django")


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _settings(name: str, default):
    return getattr(settings, name, default)


def _can_send(record: PasswordResetCode, now) -> tuple[bool, str]:
    max_sends = int(_settings("PASSWORD_RESET_MAX_SENDS", 10))
    cooldown = int(_settings("PASSWORD_RESET_RESEND_COOLDOWN_SECONDS", 60))

    if record.send_count >= max_sends:
        return False, "max_sends"

    if record.last_sent_at is not None:
        delta = (now - record.last_sent_at).total_seconds()
        if delta < cooldown:
            return False, "cooldown"

    return True, "ok"


def send_password_reset_code(user: User, *, force: bool = False) -> tuple[bool, str]:
    if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(settings, "EMAIL_HOST_PASSWORD", None):
        return False, "email_not_configured"

    now = timezone.now()

    record = (
        PasswordResetCode.objects.filter(user=user, used_at__isnull=True)
        .order_by("-created_at", "-id")
        .first()
    )
    if record is None:
        record = PasswordResetCode.objects.create(user=user)

    if not force:
        ok, reason = _can_send(record, now)
        if not ok:
            return False, reason

    ttl = int(_settings("PASSWORD_RESET_CODE_TTL_SECONDS", 600))
    code = _generate_code()

    subject = "Код восстановления пароля"
    message = (
        f"Ваш код восстановления: {code}\n\n"
        "Код действует ограниченное время. Если это были не вы — просто проигнорируйте письмо."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except smtplib.SMTPDataError as exc:
        logger.exception(
            "SMTP rejected password reset code user_id=%s email=%s smtp_code=%s smtp_error=%s host=%s port=%s tls=%s ssl=%s backend=%s from_email=%s",
            getattr(user, "id", None),
            getattr(user, "email", None),
            getattr(exc, "smtp_code", None),
            getattr(exc, "smtp_error", None),
            getattr(settings, "EMAIL_HOST", None),
            getattr(settings, "EMAIL_PORT", None),
            getattr(settings, "EMAIL_USE_TLS", None),
            getattr(settings, "EMAIL_USE_SSL", None),
            getattr(settings, "EMAIL_BACKEND", None),
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
        )
        record.last_sent_at = now
        record.send_count = record.send_count + 1
        record.save(update_fields=["last_sent_at", "send_count", "updated_at"])
        if getattr(exc, "smtp_code", None) == 554:
            return False, "spam_rejected"
        return False, "send_failed"
    except Exception:
        logger.exception(
            "Failed to send password reset code user_id=%s email=%s host=%s port=%s tls=%s ssl=%s backend=%s from_email=%s",
            getattr(user, "id", None),
            getattr(user, "email", None),
            getattr(settings, "EMAIL_HOST", None),
            getattr(settings, "EMAIL_PORT", None),
            getattr(settings, "EMAIL_USE_TLS", None),
            getattr(settings, "EMAIL_USE_SSL", None),
            getattr(settings, "EMAIL_BACKEND", None),
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
        )
        record.last_sent_at = now
        record.send_count = record.send_count + 1
        record.save(update_fields=["last_sent_at", "send_count", "updated_at"])
        return False, "send_failed"

    record.code_hash = make_password(code)
    record.expires_at = now + timedelta(seconds=ttl)
    record.last_sent_at = now
    record.send_count = record.send_count + 1
    record.attempt_count = 0
    record.save(
        update_fields=[
            "code_hash",
            "expires_at",
            "last_sent_at",
            "send_count",
            "attempt_count",
            "updated_at",
        ]
    )

    return True, "sent"


def verify_password_reset_code(user: User, code: str) -> tuple[bool, str]:
    record = (
        PasswordResetCode.objects.filter(user=user, used_at__isnull=True)
        .order_by("-created_at", "-id")
        .first()
    )
    if record is None or not record.code_hash:
        return False, "no_code"

    max_attempts = int(_settings("PASSWORD_RESET_MAX_ATTEMPTS", 10))
    if record.attempt_count >= max_attempts:
        return False, "max_attempts"

    now = timezone.now()
    if record.expires_at and now > record.expires_at:
        return False, "expired"

    record.attempt_count = record.attempt_count + 1

    if check_password(code, record.code_hash):
        record.used_at = now
        record.code_hash = ""
        record.attempt_count = 0
        record.save(update_fields=["used_at", "code_hash", "attempt_count", "updated_at"])
        return True, "verified"

    record.save(update_fields=["attempt_count", "updated_at"])
    return False, "invalid"
