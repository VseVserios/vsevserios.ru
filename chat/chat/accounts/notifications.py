from .models import UserNotification


def create_user_notification(*, recipient, event: str, title: str, body: str = "", url: str = ""):
    if recipient is None or not getattr(recipient, "is_active", True):
        return None

    return UserNotification.objects.create(
        recipient=recipient,
        event=event,
        title=(title or "").strip()[:140],
        body=(body or "").strip()[:300],
        url=(url or "").strip()[:300],
    )
