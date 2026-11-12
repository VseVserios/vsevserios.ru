from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmailVerification


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_email_verification_exists(sender, instance, created, **kwargs):
    if created:
        EmailVerification.objects.get_or_create(user=instance)
        # Создаём администраторский чат для нового пользователя
        create_admin_chat_for_user(instance)


def create_admin_chat_for_user(user):
    """Создаёт чат пользователя с администратором"""
    from django.contrib.auth import get_user_model
    from matchmaking.models import Match
    from chat.models import Message
    
    # Не создаём чат для самого администратора
    if user.is_superuser:
        return
    
    User = get_user_model()
    admin_users = list(User.objects.filter(is_superuser=True))
    if not admin_users:
        return
    
    admin_user = admin_users[0]  # Используем первого администратора
    
    # Создаём чат между пользователем и администратором
    match, created = Match.objects.get_or_create(
        user1_id=min(admin_user.id, user.id),
        user2_id=max(admin_user.id, user.id),
        defaults={"is_admin_chat": True},
    )
    
    # Если чат был только что создан, отправляем приветствие
    if created:
        Message.objects.create(
            match=match,
            sender=admin_user,
            text="Привет! Это админ"
        )
