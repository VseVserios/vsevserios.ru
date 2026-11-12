"""Правила платного доступа: подписка на подробный анализ совместимости и исключения для администрации."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import WalletTransaction
from .wallet import charge_wallet

SUBSCRIPTION_PRICE = Decimal("500")
SUBSCRIPTION_DAYS = 30
TRIAL_DAYS = 30


def is_payment_exempt(user) -> bool:
    """Администраторы (staff/superuser) не платят и не видят платёжный функционал."""
    return bool(user and getattr(user, "is_authenticated", False) and (user.is_staff or user.is_superuser))


def get_subscription(user):
    from matchmaking.models import SelfSearchSubscription

    sub, _ = SelfSearchSubscription.objects.get_or_create(
        user=user,
        defaults={"trial_ends_at": timezone.now() + timedelta(days=TRIAL_DAYS)},
    )
    return sub


def has_paid_order_for(user, other_user) -> bool:
    """Анкета прислана администратором по заказу подбора клиента (заказ не отменён)."""
    from matchmaking.models import AdminSearchOrder, UserRecommendation

    return UserRecommendation.objects.filter(
        to_user=user,
        recommended_user=other_user,
        order__client=user,
        order__status__in=[AdminSearchOrder.Status.ACTIVE, AdminSearchOrder.Status.COMPLETED],
    ).exists()


def has_full_analysis_access(user, other_user=None) -> bool:
    """Доступ к графикам и развёрнутому анализу совместимости.

    Открыт: администрации, в пробный месяц, по оплаченной подписке,
    а также для анкет, присланных администратором по заказу подбора.
    """
    if is_payment_exempt(user):
        return True
    if get_subscription(user).has_full_access():
        return True
    return other_user is not None and has_paid_order_for(user, other_user)


@transaction.atomic
def purchase_subscription(user):
    """Списывает абонентскую плату с кошелька и продлевает подписку на месяц.

    Продление идёт после окончания текущего доступа (пробного или оплаченного).
    Бросает wallet.InsufficientFunds, если средств не хватает.
    """
    from matchmaking.models import SelfSearchSubscription

    sub = SelfSearchSubscription.objects.select_for_update().get(pk=get_subscription(user).pk)

    charge_wallet(
        user,
        SUBSCRIPTION_PRICE,
        reason=WalletTransaction.Reason.SELF_SEARCH_SUBSCRIPTION,
        description=f"Подписка на подробный анализ совместимости ({SUBSCRIPTION_DAYS} дней)",
    )

    now = timezone.now()
    start = max(now, sub.paid_until or now, sub.trial_ends_at or now)
    sub.paid_until = start + timedelta(days=SUBSCRIPTION_DAYS)
    sub.save(update_fields=["paid_until"])
    return sub
