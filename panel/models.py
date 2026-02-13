from django.conf import settings
from django.db import models


class AdminNotification(models.Model):
    class Event(models.TextChoices):
        NEW_USER = "new_user", "Новый пользователь"
        QUESTIONNAIRE_COMPLETED = "questionnaire_completed", "Анкета заполнена"

    event = models.CharField(max_length=64, choices=Event.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_notifications",
    )
    questionnaire_kind = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
