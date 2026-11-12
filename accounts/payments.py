"""Пополнение кошелька через ЮKassa: создание платежа и безопасная (идемпотентная) обработка результата."""
from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction

from .models import YookassaPayment
from .wallet import topup_wallet
from .yookassa_service import YookassaService

logger = logging.getLogger(__name__)


class InvalidAmount(ValueError):
    pass


def parse_topup_amount(raw: str) -> Decimal:
    raw = (raw or "").strip().replace(",", ".").replace(" ", "")
    try:
        amount = Decimal(raw)
    except (InvalidOperation, ValueError):
        raise InvalidAmount("Введите корректную сумму пополнения.")

    if not amount.is_finite() or amount <= 0:
        raise InvalidAmount("Введите корректную сумму пополнения.")

    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount < settings.WALLET_TOPUP_MIN:
        raise InvalidAmount(f"Минимальная сумма пополнения — {settings.WALLET_TOPUP_MIN}₽.")
    if amount > settings.WALLET_TOPUP_MAX:
        raise InvalidAmount(f"Максимальная сумма пополнения — {settings.WALLET_TOPUP_MAX}₽.")
    return amount


def create_topup_payment(user, amount: Decimal, build_return_url) -> YookassaPayment:
    """Создаёт платёж в ЮKassa и локальную запись. build_return_url(public_id) -> абсолютный URL."""
    import uuid

    public_id = uuid.uuid4()
    description = f"Пополнение баланса на сайте «Всё Всерьёз» (аккаунт №{user.id})"

    remote = YookassaService().create_payment(
        amount=amount,
        description=description,
        return_url=build_return_url(public_id),
        user_id=user.id,
        idempotence_key=str(public_id),
        customer_email=user.email or "",
    )

    return YookassaPayment.objects.create(
        user=user,
        public_id=public_id,
        payment_id=remote.id,
        amount=amount,
        currency="RUB",
        description=description[:255],
        status=YookassaPayment.Status.PENDING,
        confirmation_url=remote.confirmation.confirmation_url,
    )


def _remote_matches_local(payment: YookassaPayment, remote) -> bool:
    try:
        remote_amount = Decimal(str(remote.amount.value))
        remote_currency = remote.amount.currency
    except (AttributeError, InvalidOperation, TypeError):
        return False

    if remote_amount != payment.amount or remote_currency != payment.currency:
        return False

    metadata = getattr(remote, "metadata", None) or {}
    remote_user_id = metadata.get("user_id") if hasattr(metadata, "get") else None
    return remote_user_id is None or str(remote_user_id) == str(payment.user_id)


def sync_payment(payment_id: str, remote) -> YookassaPayment | None:
    """Приводит локальный платёж в соответствие со статусом, полученным из API ЮKassa.

    Баланс пополняется ровно один раз: строка платежа блокируется, статус succeeded необратим.
    """
    with transaction.atomic():
        payment = (
            YookassaPayment.objects.select_for_update().filter(payment_id=payment_id).first()
        )
        if payment is None:
            return None

        if payment.status == YookassaPayment.Status.SUCCEEDED:
            return payment

        remote_status = getattr(remote, "status", "")

        if remote_status == "succeeded":
            if not _remote_matches_local(payment, remote):
                logger.error(
                    "YooKassa payment %s does not match local record; balance not credited", payment_id
                )
                payment.status = YookassaPayment.Status.FAILED
                payment.save(update_fields=["status", "updated_at"])
                return payment

            topup_wallet(
                payment.user,
                payment.amount,
                description=f"Пополнение через ЮKassa (платёж {payment_id})",
            )
            payment.status = YookassaPayment.Status.SUCCEEDED
            method = getattr(getattr(remote, "payment_method", None), "type", "") or ""
            payment.payment_method = method[:20]
            payment.save(update_fields=["status", "payment_method", "updated_at"])

        elif remote_status == "canceled" and payment.status == YookassaPayment.Status.PENDING:
            payment.status = YookassaPayment.Status.CANCELED
            payment.save(update_fields=["status", "updated_at"])

        return payment
