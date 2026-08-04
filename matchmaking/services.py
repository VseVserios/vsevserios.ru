from django.db import transaction
from django.db.models import Q

from .models import Match, Swipe, UserBan, UserBlock, UserRecommendation


@transaction.atomic
def record_swipe(*, from_user, to_user, value: str):
    Swipe.objects.filter(from_user=from_user, to_user=to_user).delete()
    swipe = Swipe.objects.create(
        from_user=from_user, to_user=to_user, value=value)

    created_match = None
    if value == Swipe.Value.LIKE:
        if Swipe.objects.filter(
            from_user=to_user,
            to_user=from_user,
            value=Swipe.Value.LIKE,
        ).exists():
            created_match, _ = Match.get_or_create_for_users(
                from_user, to_user)

    if created_match is not None:
        from accounts.models import UserNotification
        from accounts.notifications import create_user_notification

        other_for_from = getattr(to_user, "profile", None)
        other_name_for_from = None
        if other_for_from is not None:
            other_name_for_from = other_for_from.display_name
        if not other_name_for_from:
            other_name_for_from = to_user.get_username()

        other_for_to = getattr(from_user, "profile", None)
        other_name_for_to = None
        if other_for_to is not None:
            other_name_for_to = other_for_to.display_name
        if not other_name_for_to:
            other_name_for_to = from_user.get_username()

        chat_url = f"/chat/{created_match.id}/"

        create_user_notification(
            recipient=from_user,
            event=UserNotification.Event.NEW_MATCH,
            title="Новое совпадение",
            body=f"У вас совпадение с {other_name_for_from}.",
            url=chat_url,
        )
        create_user_notification(
            recipient=to_user,
            event=UserNotification.Event.NEW_MATCH,
            title="Новое совпадение",
            body=f"У вас совпадение с {other_name_for_to}.",
            url=chat_url,
        )

    _apply_admin_search_order_billing(
        from_user=from_user, to_user=to_user, value=value, created_match=created_match)

    return swipe, created_match


def _apply_admin_search_order_billing(*, from_user, to_user, value: str, created_match) -> None:
    """Списание с кошелька клиента по платному заказу подбора администратора.

    За взаимную симпатию по рекомендации из заказа — оплата тарифа заказа.
    После 5 отклонений подряд рекомендаций из заказа — компенсация работы админа
    в размере тарифа, счётчик отклонений сбрасывается.
    """
    rec = (
        UserRecommendation.objects.filter(
            to_user=from_user, recommended_user=to_user, order__isnull=False
        )
        .select_related("order")
        .order_by("-created_at")
        .first()
    )
    if rec is None or rec.order_id is None:
        return

    from accounts.models import WalletTransaction
    from accounts.wallet import charge_wallet

    order = rec.order

    if value == Swipe.Value.LIKE:
        if created_match is not None:
            charge_wallet(
                order.client,
                order.price,
                reason=WalletTransaction.Reason.ADMIN_SEARCH,
                description=f"Взаимная симпатия по заказу подбора №{order.id}",
                allow_negative=True,
            )
            order.rejected_streak = 0
            order.save(update_fields=["rejected_streak"])
    else:
        order.rejected_streak += 1
        if order.rejected_streak >= 5:
            charge_wallet(
                order.client,
                order.price,
                reason=WalletTransaction.Reason.ADMIN_SEARCH,
                description=f"Компенсация за работу по заказу подбора №{order.id} (5 отклонений подряд)",
                allow_negative=True,
            )
            order.rejected_streak = 0
        order.save(update_fields=["rejected_streak"])


def run_self_search(user, *, min_compatibility_percent: int, limit: int = 20) -> int:
    """Подобрать кандидатов выше порога совместимости и создать рекомендации.

    Возвращает количество новых рекомендаций.
    """
    from profiles.models import Profile

    from .compatibility import compatibility

    my_profile = getattr(user, "profile", None)
    if my_profile is None:
        return 0

    banned_ids = set(UserBan.objects.active(
    ).values_list("user_id", flat=True))
    blocked_ids = set(UserBlock.objects.filter(
        blocker=user).values_list("blocked_id", flat=True))
    blocked_by_ids = set(UserBlock.objects.filter(
        blocked=user).values_list("blocker_id", flat=True))
    swiped_ids = set(Swipe.objects.filter(
        from_user=user).values_list("to_user_id", flat=True))
    already_recommended_ids = set(
        UserRecommendation.objects.filter(to_user=user, consumed_at__isnull=True).values_list(
            "recommended_user_id", flat=True
        )
    )
    exclude_ids = banned_ids | blocked_ids | blocked_by_ids | swiped_ids | already_recommended_ids | {
        user.id}

    qs = (
        Profile.objects.select_related("user")
        .filter(user__is_active=True)
        .exclude(user_id__in=exclude_ids)
        .order_by("-updated_at")
    )

    my_gender = my_profile.gender or None
    if my_profile.looking_for == Profile.LookingFor.MEN:
        qs = qs.filter(gender=Profile.Gender.MALE)
    elif my_profile.looking_for == Profile.LookingFor.WOMEN:
        qs = qs.filter(gender=Profile.Gender.FEMALE)

    if my_gender == Profile.Gender.MALE:
        qs = qs.filter(
            Q(looking_for="") | Q(looking_for=Profile.LookingFor.EVERYONE) | Q(
                looking_for=Profile.LookingFor.MEN)
        )
    elif my_gender == Profile.Gender.FEMALE:
        qs = qs.filter(
            Q(looking_for="") | Q(looking_for=Profile.LookingFor.EVERYONE) | Q(
                looking_for=Profile.LookingFor.WOMEN)
        )
    elif my_gender:
        qs = qs.filter(Q(looking_for="") | Q(
            looking_for=Profile.LookingFor.EVERYONE))

    candidates = list(qs[:300])

    matched = []
    for candidate_profile in candidates:
        report = compatibility(my_profile, candidate_profile)
        overall = report.get("overall")
        if overall is not None and overall >= min_compatibility_percent:
            matched.append((overall, candidate_profile))

    matched.sort(key=lambda pair: pair[0], reverse=True)
    matched = matched[:limit]

    created = 0
    with transaction.atomic():
        for overall, candidate_profile in matched:
            UserRecommendation.objects.create(
                to_user=user,
                recommended_user=candidate_profile.user,
                is_self_search=True,
                score=overall,
            )
            created += 1

    return created
