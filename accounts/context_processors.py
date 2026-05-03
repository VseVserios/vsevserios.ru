def unread_notifications(request):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {"unread_notifications_count": 0, "unread_chat_notifications_count": 0}

    from .models import UserNotification

    count = UserNotification.objects.filter(recipient=user, is_read=False).count()
    chat_count = UserNotification.objects.filter(
        recipient=user,
        is_read=False,
        event=UserNotification.Event.NEW_MESSAGE,
    ).count()
    return {"unread_notifications_count": count, "unread_chat_notifications_count": chat_count}


def staff_flags(request):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {"is_matchmaker": False}

    try:
        is_matchmaker = user.groups.filter(name="matchmaker").exists()
    except Exception:
        is_matchmaker = False

    return {"is_matchmaker": bool(is_matchmaker)}
