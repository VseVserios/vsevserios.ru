import logging
import secrets
import smtplib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerification, User

logger = logging.getLogger("django")


def _mark_send_attempt(record: EmailVerification, *, now) -> None:
    record.last_sent_at = now
    record.send_count = record.send_count + 1
    record.save(update_fields=["last_sent_at", "send_count", "updated_at"])


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _get_or_create_record(user: User) -> EmailVerification:
    record, _ = EmailVerification.objects.get_or_create(user=user)
    return record


def send_verification_code(user: User, *, force: bool = False) -> tuple[bool, str]:
    if user.email_verified:
        return True, "already_verified"

    if not getattr(settings, "EMAIL_HOST_USER", None) or not getattr(settings, "EMAIL_HOST_PASSWORD", None):
        return False, "email_not_configured"

    record = _get_or_create_record(user)
    now = timezone.now()

    if not force:
        if record.send_count >= settings.EMAIL_VERIFICATION_MAX_SENDS:
            return False, "max_sends"

        if record.last_sent_at is not None:
            delta = (now - record.last_sent_at).total_seconds()
            if delta < settings.EMAIL_VERIFICATION_RESEND_COOLDOWN_SECONDS:
                return False, "cooldown"

    code = _generate_code()

    subject = "Код подтверждения"
    message = (
        f"Ваш код подтверждения: {code}\n\n"
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
            "SMTP rejected email verification message user_id=%s email=%s smtp_code=%s smtp_error=%s host=%s port=%s tls=%s ssl=%s backend=%s from_email=%s",
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
        _mark_send_attempt(record, now=now)
        if getattr(exc, "smtp_code", None) == 554:
            return False, "spam_rejected"
        return False, "send_failed"
    except Exception:
        logger.exception(
            "Failed to send email verification code user_id=%s email=%s host=%s port=%s tls=%s ssl=%s backend=%s from_email=%s",
            getattr(user, "id", None),
            getattr(user, "email", None),
            getattr(settings, "EMAIL_HOST", None),
            getattr(settings, "EMAIL_PORT", None),
            getattr(settings, "EMAIL_USE_TLS", None),
            getattr(settings, "EMAIL_USE_SSL", None),
            getattr(settings, "EMAIL_BACKEND", None),
            getattr(settings, "DEFAULT_FROM_EMAIL", None),
        )
        _mark_send_attempt(record, now=now)
        return False, "send_failed"

    record.code_hash = make_password(code)
    record.expires_at = now + timedelta(seconds=settings.EMAIL_VERIFICATION_CODE_TTL_SECONDS)
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


def verify_code(user: User, code: str) -> tuple[bool, str]:
    if user.email_verified:
        return True, "already_verified"

    record = _get_or_create_record(user)

    if record.attempt_count >= settings.EMAIL_VERIFICATION_MAX_ATTEMPTS:
        return False, "max_attempts"

    if not record.code_hash:
        return False, "no_code"

    now = timezone.now()
    if record.expires_at and now > record.expires_at:
        return False, "expired"

    record.attempt_count = record.attempt_count + 1

    if check_password(code, record.code_hash):
        user.email_verified = True
        user.save(update_fields=["email_verified"])

        record.code_hash = ""
        record.attempt_count = 0
        record.save(update_fields=["code_hash", "attempt_count", "updated_at"])
        return True, "verified"

    record.save(update_fields=["attempt_count", "updated_at"])
    return False, "invalid"
