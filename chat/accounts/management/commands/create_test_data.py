from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from profiles.models import Profile, ProfilePhoto
from matchmaking.models import UserRecommendation
import random
from django.utils import timezone
from datetime import timedelta, date

User = get_user_model()


FIRST_NAMES_MALE = ['Александр', 'Сергей', 'Дмитрий', 'Иван', 'Артём', 'Алексей', 'Максим', 'Станислав']
FIRST_NAMES_FEMALE = ['Мария', 'Екатерина', 'Анна', 'Ольга', 'Инна', 'Елена', 'Александра', 'Наталья']
LAST_NAMES = ['Смирнов', 'Иванов', 'Петров', 'Соколов', 'Лебедев', 'Морозов', 'Федоров', 'Волков']
CITIES = ['Москва', 'СПб', 'Казань', 'Екатеринбург', 'Новосибирск', 'Челябинск', 'Ростов', 'Пермь']
BIOS = [
    'Люблю путешествовать и открывать новые места',
    'Ищу человека для серьёзных отношений',
    'Люблю кино, музыку и спорт',
    'Работаю в IT, ищу единомышленника',
    'Люблю готовить и общаться за чашкой кофе',
    'Активный образ жизни, спорт и здоровье',
    'Интересуюсь искусством и культурой',
    'Люблю животных и природу',
]


class Command(BaseCommand):
    help = 'Создает тестовые данные для разработки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Количество тестовых пользователей'
        )

    def handle(self, *args, **options):
        count = options['users']
        self.stdout.write(f'Создание {count} тестовых пользователей...')

        genders = ['male', 'female']
        looking_for = ['men', 'women', 'everyone']

        for i in range(count):
            is_male = random.choice([True, False])
            first_name = random.choice(FIRST_NAMES_MALE if is_male else FIRST_NAMES_FEMALE)
            last_name = random.choice(LAST_NAMES)
            
            username = f"user{i}{random.randint(1000, 9999)}"
            email = f"test{i}+{random.randint(1000, 9999)}@example.com"
            
            # Создать пользователя
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'email_verified': True,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )

            if created:
                user.set_password('testpass123')
                user.save()

            # Создать профиль
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={
                    'display_name': f"{first_name} {last_name}",
                    'bio': random.choice(BIOS),
                    'city': random.choice(CITIES),
                    'birth_date': date(
                        year=random.randint(1990, 2005),
                        month=random.randint(1, 12),
                        day=random.randint(1, 28)
                    ),
                    'gender': 'male' if is_male else 'female',
                    'looking_for': random.choice(looking_for),
                    'ui_theme': random.choice(['dark', 'light']),
                }
            )

        self.stdout.write(
            self.style.SUCCESS(f'✓ Создано {count} пользователей')
        )

        # Создать рекомендации между пользователями
        users = list(User.objects.all())
        created_recs = 0

        for user in users:
            # Создать несколько рекомендаций для каждого пользователя
            candidates = [u for u in users if u.id != user.id]
            for candidate in candidates[:5]:
                rec, created = UserRecommendation.objects.get_or_create(
                    to_user=user,
                    recommended_user=candidate,
                    defaults={
                        'score': random.randint(60, 100),
                        'created_at': timezone.now() - timedelta(days=random.randint(0, 30))
                    }
                )
                if created:
                    created_recs += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Создано {created_recs} рекомендаций')
        )
        self.stdout.write(
            self.style.SUCCESS('✓ Тестовые данные готовы!')
        )
