from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)

    wallet_balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0"))

    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)

    special_category_consent = models.BooleanField(default=False)
    special_category_consent_at = models.DateTimeField(null=True, blank=True)
    special_category_consent_revoked_at = models.DateTimeField(
        null=True, blank=True)

    def __str__(self) -> str:
        return self.get_username()


class ConsentEvent(models.Model):
    class Kind(models.TextChoices):
        TERMS = "terms", "Пользовательское соглашение — принято"
        PRIVACY = "privacy", "Политика обработки персональных данных — принята"
        SPECIAL_CATEGORY_GIVEN = "special_category_given", "Согласие на спецкатегории — дано"
        SPECIAL_CATEGORY_REVOKED = "special_category_revoked", "Согласие на спецкатегории — отозвано"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="consent_events",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ConsentEvent({self.user_id}:{self.kind})"


class WalletTransaction(models.Model):
    class Reason(models.TextChoices):
        TOPUP = "topup", "Пополнение баланса"
        SELF_SEARCH_SUBSCRIPTION = "self_search_subscription", "Подписка на самостоятельный поиск"
        ADMIN_SEARCH = "admin_search", "Оплата подбора администратором"
        REFUND = "refund", "Возврат средств"

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="wallet_transactions",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=32, choices=Reason.choices)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"WalletTransaction({self.user_id}:{self.amount})"


class EmailVerification(models.Model):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="email_verification",
    )
    code_hash = models.CharField(max_length=256, blank=True, default="")
    expires_at = models.DateTimeField(default=timezone.now)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    send_count = models.PositiveIntegerField(default=0)
    attempt_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"EmailVerification({self.user_id})"


class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="password_reset_codes",
    )
    code_hash = models.CharField(max_length=256, blank=True, default="")
    expires_at = models.DateTimeField(default=timezone.now)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    send_count = models.PositiveIntegerField(default=0)
    attempt_count = models.PositiveIntegerField(default=0)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"PasswordResetCode({self.user_id})"


class UserNotification(models.Model):
    class Event(models.TextChoices):
        NEW_MATCH = "new_match", "Новое совпадение"
        NEW_MESSAGE = "new_message", "Новое сообщение"

    recipient = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    event = models.CharField(max_length=64, choices=Event.choices)
    title = models.CharField(max_length=140)
    body = models.CharField(max_length=300, blank=True, default="")
    url = models.CharField(max_length=300, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read", "created_at"],
                name="acc_notif_rec_read_created_idx",
            ),
        ]

    def mark_read(self):
        if self.is_read:
            return
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=["is_read", "read_at"])
