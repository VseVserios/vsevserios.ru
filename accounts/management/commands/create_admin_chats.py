from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from matchmaking.models import Match

User = get_user_model()


class Command(BaseCommand):
    help = "Создаёт чаты администратора со всеми пользователями"

    def handle(self, *args, **options):
        admin_users = list(User.objects.filter(is_superuser=True))
        if not admin_users:
            self.stdout.write(self.style.ERROR("Администраторы не найдены"))
            return

        admin_user = admin_users[0]  # Используем первого администратора
        users = User.objects.filter(is_superuser=False)
        created_count = 0

        for user in users:
            if user.id != admin_user.id:
                match, created = Match.objects.get_or_create(
                    user1_id=min(admin_user.id, user.id),
                    user2_id=max(admin_user.id, user.id),
                    defaults={"is_admin_chat": True},
                )
                if created:
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Создано администраторских чатов: {created_count}"
            )
        )
