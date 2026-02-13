def unread_notifications(request):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {"unread_notifications_count": 0}

    from .models import UserNotification

    count = UserNotification.objects.filter(recipient=user, is_read=False).count()
    return {"unread_notifications_count": count}
