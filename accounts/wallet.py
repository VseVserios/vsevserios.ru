"""Простые операции с внутренним балансом пользователя (Кошелёк).

Реальная платёжная система не подключена (см. Пользовательское соглашение, п. 4.6-4.9:
внутренний баланс используется только для оплаты услуг Сайта). Пополнение баланса
на данном этапе имитируется — оплата картой не производится.
"""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from .models import User, WalletTransaction


class InsufficientFunds(Exception):
    """Недостаточно средств на балансе для списания."""


@transaction.atomic
def topup_wallet(user: User, amount: Decimal, *, description: str = "") -> WalletTransaction:
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Сумма пополнения должна быть положительной")

    locked_user = User.objects.select_for_update().get(pk=user.pk)
    locked_user.wallet_balance = locked_user.wallet_balance + amount
    locked_user.save(update_fields=["wallet_balance"])
    user.wallet_balance = locked_user.wallet_balance

    return WalletTransaction.objects.create(
        user=locked_user,
        amount=amount,
        reason=WalletTransaction.Reason.TOPUP,
        balance_after=locked_user.wallet_balance,
        description=description,
    )


@transaction.atomic
def charge_wallet(
    user: User,
    amount: Decimal,
    *,
    reason: str,
    description: str = "",
    allow_negative: bool = False,
) -> WalletTransaction:
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Сумма списания должна быть положительной")

    locked_user = User.objects.select_for_update().get(pk=user.pk)
    if not allow_negative and locked_user.wallet_balance < amount:
        raise InsufficientFunds("Недостаточно средств на балансе")

    locked_user.wallet_balance = locked_user.wallet_balance - amount
    locked_user.save(update_fields=["wallet_balance"])
    user.wallet_balance = locked_user.wallet_balance

    return WalletTransaction.objects.create(
        user=locked_user,
        amount=-amount,
        reason=reason,
        balance_after=locked_user.wallet_balance,
        description=description,
    )


@transaction.atomic
def refund_wallet(user: User, amount: Decimal, *, description: str = "") -> WalletTransaction:
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Сумма возврата должна быть положительной")

    locked_user = User.objects.select_for_update().get(pk=user.pk)
    locked_user.wallet_balance = locked_user.wallet_balance + amount
    locked_user.save(update_fields=["wallet_balance"])
    user.wallet_balance = locked_user.wallet_balance

    return WalletTransaction.objects.create(
        user=locked_user,
        amount=amount,
        reason=WalletTransaction.Reason.REFUND,
        balance_after=locked_user.wallet_balance,
        description=description,
    )
