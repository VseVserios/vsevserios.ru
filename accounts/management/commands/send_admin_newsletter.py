from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
from matchmaking.models import Match
from chat.models import Message

User = get_user_model()


class Command(BaseCommand):
    help = "Отправляет рассылку сообщения от администратора всем пользователям"

    def add_arguments(self, parser):
        parser.add_argument(
            "message_text",
            type=str,
            help="Текст сообщения для рассылки",
        )

    def handle(self, *args, **options):
        admin_users = list(User.objects.filter(is_superuser=True))
        if not admin_users:
            self.stdout.write(self.style.ERROR("Администраторы не найдены"))
            return

        admin_user = admin_users[0]  # Используем первого администратора
        message_text = options["message_text"]
        users = User.objects.filter(is_superuser=False, is_active=True)
        sent_count = 0

        for user in users:
            match = Match.objects.filter(
                is_admin_chat=True
            ).filter(
                Q(user1=admin_user, user2=user) |
                Q(user1=user, user2=admin_user)
            ).first()
            
            if not match:
                self.stdout.write(
                    self.style.WARNING(
                        f"Чат с пользователем {user.username} не найден"
                    )
                )
                continue
            
            Message.objects.create(
                match=match,
                sender=admin_user,
                text=message_text,
            )
            sent_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Рассылка отправлена {sent_count} пользователям"
            )
        )
