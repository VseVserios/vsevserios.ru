from django.db import transaction

from .models import Match, Swipe


@transaction.atomic
def record_swipe(*, from_user, to_user, value: str):
    Swipe.objects.filter(from_user=from_user, to_user=to_user).delete()
    swipe = Swipe.objects.create(from_user=from_user, to_user=to_user, value=value)

    created_match = None
    if value == Swipe.Value.LIKE:
        if Swipe.objects.filter(
            from_user=to_user,
            to_user=from_user,
            value=Swipe.Value.LIKE,
        ).exists():
            created_match, _ = Match.get_or_create_for_users(from_user, to_user)

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
            title="Новый мэтч",
            body=f"У вас мэтч с {other_name_for_from}.",
            url=chat_url,
        )
        create_user_notification(
            recipient=to_user,
            event=UserNotification.Event.NEW_MATCH,
            title="Новый мэтч",
            body=f"У вас мэтч с {other_name_for_to}.",
            url=chat_url,
        )

    return swipe, created_match
