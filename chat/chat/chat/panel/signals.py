from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AdminNotification


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def notify_admin_new_user(sender, instance, created, **kwargs):
    if not created:
        return
    AdminNotification.objects.create(event=AdminNotification.Event.NEW_USER, user=instance)
