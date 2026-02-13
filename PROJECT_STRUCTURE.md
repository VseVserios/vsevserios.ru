# 📂 Структура файлов ВсёвСерьез

## 📚 Документация

```
├── README.md                 # Главная информация о проекте
├── QUICKSTART.md            # Быстрый старт за 5 минут
├── DEPLOYMENT.md            # Развертывание на production
├── TESTING.md              # Тестирование приложения
├── ROADMAP.md              # Планы развития
├── CHANGELOG.md            # История версий и изменений
├── API_EXTENSIONS.md       # Расширение функциональности
├── CONTRIBUTING.md         # Как внести свой вклад
├── .env.example            # Пример конфигурации
└── manage.py               # Django точка входа
```

## 🔧 Конфигурация

```
config/
├── __init__.py
├── settings.py             # Основные настройки Django
├── urls.py                 # Главные URL маршруты
├── asgi.py                 # ASGI конфигурация для развертывания
└── wsgi.py                 # WSGI конфигурация для развертывания
```

## 👥 Приложение Accounts (Аутентификация и пользователи)

```
accounts/
├── migrations/             # Миграции БД
├── management/
│   └── commands/
│       └── create_test_data.py  # Команда для создания тестовых данных
├── __init__.py
├── admin.py                # Админ-панель
├── apps.py                 # Конфигурация приложения
├── models.py               # Модели User, EmailVerification, PasswordResetCode, UserNotification
├── views.py                # Views для регистрации, входа, настроек
├── forms.py                # Формы аутентификации
├── urls.py                 # URL маршруты
├── signals.py              # Django signals для автоматизации
├── middleware.py           # Custom middleware для проверок
├── context_processors.py   # Context processors для шаблонов
├── email_verification.py   # Логика верификации email
├── password_reset.py       # Логика восстановления пароля
├── notifications.py        # Логика уведомлений
├── cache_utils.py          # Утилиты для кеширования
├── security.py             # Утилиты безопасности
├── error_handling.py       # Обработка ошибок
├── form_utils.py           # Валидаторы форм
└── db_optimization.py      # Оптимизация БД
```

## 👤 Приложение Profiles (Профили пользователей)

```
profiles/
├── migrations/             # Миграции БД
├── management/             # Management команды
├── __init__.py
├── admin.py                # Админ-панель для профилей
├── apps.py                 # Конфигурация приложения
├── models.py               # Модели Profile, ProfilePhoto, QuestionnaireSection
├── views.py                # Views для редактирования профилей
├── forms.py                # Формы профилей
├── urls.py                 # URL маршруты
├── signals.py              # Signals для автоматизации
├── questionnaire.py        # Логика анкеты
└── admin.py                # Админ-панель
```

## 💘 Приложение Matchmaking (Рекомендации и свайпы)

```
matchmaking/
├── migrations/             # Миграции БД
├── __init__.py
├── admin.py                # Админ-панель для мэтчей
├── apps.py                 # Конфигурация приложения
├── models.py               # Модели Swipe, Match, UserBlock, UserReport, UserBan, UserRecommendation, HomePage, HomeBlock
├── views.py                # Views для ленты, свайпов, мэтчей
├── forms.py                # Формы (например ReportUserForm)
├── urls.py                 # URL маршруты
├── services.py             # Бизнес-логика (record_swipe)
├── compatibility.py        # Логика расчета совместимости
└── admin.py                # Админ-панель
```

## 💬 Приложение Chat (Чаты)

```
chat/
├── migrations/             # Миграции БД
├── __init__.py
├── admin.py                # Админ-панель для чатов
├── apps.py                 # Конфигурация приложения
├── models.py               # Модель Message
├── views.py                # Views для чата
├── forms.py                # Формы сообщений
├── urls.py                 # URL маршруты
└── admin.py                # Админ-панель
```

## 🎛️ Приложение Panel (Админ-панель)

```
panel/
├── migrations/             # Миграции БД
├── __init__.py
├── admin.py                # Админ-панель для модерации
├── apps.py                 # Конфигурация приложения
├── models.py               # Модели (если есть)
├── views.py                # Views для админ-панели
├── forms.py                # Формы для администрирования
├── urls.py                 # URL маршруты
└── admin.py                # Админ-панель
```

## 🎨 Шаблоны (HTML)

```
templates/
├── base.html               # Базовый шаблон со стилями
├── accounts/
│   ├── login.html         # Страница входа
│   ├── register.html      # Страница регистрации
│   ├── verify_email.html  # Верификация email
│   ├── password_reset_request.html
│   ├── password_reset_code.html
│   ├── password_change.html
│   ├── settings.html      # Настройки аккаунта
│   └── notifications.html # Уведомления
├── profiles/
│   ├── profile_edit.html  # Редактирование профиля
│   ├── profile_view.html  # Просмотр профиля
│   └── photos.html        # Управление фото
├── matchmaking/
│   ├── feed.html          # Лента с рекомендациями
│   ├── matches.html       # Список мэтчей
│   ├── landing.html       # Главная страница
│   ├── _card.html         # Карточка профиля (HTMX)
│   ├── recommendation_compatibility.html
│   └── report_user.html   # Жалоба на пользователя
├── chat/
│   ├── inbox.html         # Список чатов
│   ├── room.html          # Окно чата
│   └── _messages.html     # Сообщения (HTMX)
├── panel/
│   ├── dashboard.html     # Дашборд администратора
│   ├── users.html         # Управление пользователями
│   ├── moderation.html    # Модерация
│   └── analytics.html     # Аналитика
└── registration/
    └── email_confirmation.html  # Email подтверждение
```

## 📦 Статические файлы (CSS, JS)

```
static/
├── app.js                  # Главный JavaScript файл
│   ├── CSRF обработка
│   ├── HTMX поддержка
│   ├── Автозагрузка стилей форм
│   ├── Обработка меню
│   └── Анимации
└── (CSS генерируется Tailwind)
```

## 📁 Media (Пользовательские файлы)

```
media/
├── avatars/               # Аватары пользователей
├── photos/                # Фотографии профилей
└── landing/               # Изображения для главной
```

## 🗄️ База данных

```
db.sqlite3                 # SQLite БД (development)
```

## 📋 Вспомогательные файлы

```
.env                       # Конфигурация окружения (не в гите)
.env.example              # Пример конфигурации (в гите)
.gitignore                # Git ignore файл
requirements.txt          # Зависимости Python
setup.py                  # Скрипт инициализации
manage.py                 # Django управления командами
```

---

## 🗂️ Полная структура

```
site/
├── .env.example
├── .gitignore
├── README.md
├── QUICKSTART.md
├── DEPLOYMENT.md
├── TESTING.md
├── ROADMAP.md
├── CHANGELOG.md
├── API_EXTENSIONS.md
├── CONTRIBUTING.md
├── manage.py
├── setup.py
├── requirements.txt
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   ├── wsgi.py
│   └── __pycache__/
│
├── accounts/
│   ├── migrations/
│   ├── management/
│   │   ├── __init__.py
│   │   └── commands/
│   │       ├── __init__.py
│   │       └── create_test_data.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── signals.py
│   ├── middleware.py
│   ├── context_processors.py
│   ├── email_verification.py
│   ├── password_reset.py
│   ├── notifications.py
│   ├── cache_utils.py
│   ├── security.py
│   ├── error_handling.py
│   ├── form_utils.py
│   ├── db_optimization.py
│   └── __pycache__/
│
├── profiles/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── signals.py
│   ├── questionnaire.py
│   └── __pycache__/
│
├── matchmaking/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── services.py
│   ├── compatibility.py
│   └── __pycache__/
│
├── chat/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── __pycache__/
│
├── panel/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── signals.py
│   └── __pycache__/
│
├── templates/
│   ├── base.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── verify_email.html
│   │   ├── password_reset_request.html
│   │   ├── password_reset_code.html
│   │   ├── password_change.html
│   │   ├── settings.html
│   │   └── notifications.html
│   ├── profiles/
│   │   └── ...
│   ├── matchmaking/
│   │   ├── feed.html
│   │   ├── matches.html
│   │   ├── landing.html
│   │   ├── _card.html
│   │   ├── recommendation_compatibility.html
│   │   └── report_user.html
│   ├── chat/
│   │   ├── inbox.html
│   │   ├── room.html
│   │   └── _messages.html
│   ├── panel/
│   │   └── ...
│   └── registration/
│       └── ...
│
├── static/
│   ├── app.js
│   └── (CSS from Tailwind)
│
├── media/
│   ├── avatars/
│   ├── photos/
│   └── landing/
│
├── db.sqlite3
├── .venv/
│   └── (виртуальное окружение Python)
│
└── __pycache__/
```

---

## 📊 Статистика кода

- **Python файлов**: ~25
- **HTML шаблонов**: ~20
- **Строк кода**: ~8000+
- **Модели БД**: 15+
- **Views**: 40+
- **Forms**: 10+
- **Management Commands**: 1+
- **Утилиты**: 5+

---

## 🔗 Связи между приложениями

```
accounts (пользователи)
    ↓
profiles (профили)
    ↓
matchmaking (рекомендации и свайпы)
    ↓
chat (чаты)
    ↓
panel (админ-панель - управляет всем)
```

---

**Последнее обновление**: Февраль 2026
