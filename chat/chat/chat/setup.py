#!/usr/bin/env python
"""
Скрипт для первого запуска и конфигурации приложения
"""

import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command
from profiles.models import Profile

User = get_user_model()


def create_admin_user():
    """Создает администратора для тестирования"""
    print("=" * 60)
    print("Создание администратора")
    print("=" * 60)
    
    # Проверить существует ли уже админ
    if User.objects.filter(is_staff=True).exists():
        print("✓ Администратор уже существует")
        admin_user = User.objects.filter(is_staff=True).first()
        print(f"  Пользователь: {admin_user.username}")
        print(f"  Email: {admin_user.email}")
        return
    
    # Создать нового админа
    username = 'admin'
    email = 'admin@example.com'
    password = 'adminpass123'
    
    try:
        admin_user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        # Создать профиль
        Profile.objects.get_or_create(
            user=admin_user,
            defaults={'display_name': 'Администратор'}
        )
        
        print(f"✓ Администратор создан успешно!")
        print(f"  Пользователь: {username}")
        print(f"  Пароль: {password}")
        print(f"  Email: {email}")
        print(f"  Войти в админ-панель: http://localhost:8000/admin/")
    except Exception as e:
        print(f"✗ Ошибка при создании администратора: {e}")


def apply_migrations():
    """Применяет все миграции"""
    print("\n" + "=" * 60)
    print("Применение миграций")
    print("=" * 60)
    
    try:
        call_command('migrate', verbosity=1)
        print("✓ Миграции применены успешно!")
    except Exception as e:
        print(f"✗ Ошибка при применении миграций: {e}")


def create_test_data():
    """Создает тестовые данные"""
    print("\n" + "=" * 60)
    print("Создание тестовых данных")
    print("=" * 60)
    
    try:
        call_command('create_test_data', users=5, verbosity=1)
        print("✓ Тестовые данные созданы успешно!")
    except Exception as e:
        print(f"✗ Ошибка при создании тестовых данных: {e}")


def main():
    """Главная функция"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         ВсёВсерьёз - Инициализация приложения             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    # Этап 1: Миграции
    apply_migrations()
    
    # Этап 2: Администратор
    create_admin_user()
    
    # Этап 3: Тестовые данные
    response = input("\nСоздать тестовые данные? (y/n): ").strip().lower()
    if response == 'y':
        create_test_data()
    
    # Итоговая информация
    print("\n" + "=" * 60)
    print("✓ Инициализация завершена!")
    print("=" * 60)
    print("\n📌 Что дальше:")
    print("  1. Запустить сервер: python manage.py runserver")
    print("  2. Открыть браузер: http://localhost:8000")
    print("  3. Админ-панель: http://localhost:8000/admin/")
    print("  4. Войти как администратор с созданными учетными данными")
    print("\n💡 Полезные команды:")
    print("  - Создать суперпользователя: python manage.py createsuperuser")
    print("  - Создать тестовые данные: python manage.py create_test_data")
    print("  - Сбор статических файлов: python manage.py collectstatic")
    print("  - Запуск тестов: python manage.py test")
    print("\n📚 Документация:")
    print("  - README.md - основная информация")
    print("  - DEPLOYMENT.md - развертывание на production")
    print("  - API_EXTENSIONS.md - расширение функциональности")
    print()


if __name__ == '__main__':
    main()
