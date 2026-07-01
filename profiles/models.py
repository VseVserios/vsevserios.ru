from django.conf import settings
from django.db import models
from django.utils import timezone
from accounts.fields import EncryptedJSONField


class Profile(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Мужчина"
        FEMALE = "female", "Женщина"
        OTHER = "other", "Другое"

    class LookingFor(models.TextChoices):
        MEN = "men", "Мужчин"
        WOMEN = "women", "Женщин"
        EVERYONE = "everyone", "Всех"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=64, blank=True)
    bio = models.TextField(blank=True)
    city = models.CharField(max_length=64, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=16, choices=Gender.choices, blank=True)
    looking_for = models.CharField(max_length=16, choices=LookingFor.choices, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    questionnaire_me = EncryptedJSONField(default=dict, blank=True)
    questionnaire_ideal = EncryptedJSONField(default=dict, blank=True)

    class Theme(models.TextChoices):
        DARK = "dark", "Тёмная"
        LIGHT = "light", "Светлая"

    ui_theme = models.CharField(max_length=16, choices=Theme.choices, default=Theme.DARK)
    notify_email_matches = models.BooleanField(default=True)
    notify_email_messages = models.BooleanField(default=True)
    notify_email_marketing = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.now().date()
        years = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            years -= 1
        return years

    def __str__(self) -> str:
        return f"Profile({self.user_id})"


class ProfileAccessLog(models.Model):
    """Log of who accessed personal data (profile/questionnaire)."""

    class AccessType(models.TextChoices):
        PROFILE_VIEW = "profile_view", "Просмотр профиля"
        QUESTIONNAIRE_VIEW = "questionnaire_view", "Просмотр анкеты"
        PROFILE_EDIT = "profile_edit", "Редактирование профиля"
        QUESTIONNAIRE_EDIT = "questionnaire_edit", "Редактирование анкеты"

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="access_logs")
    accessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="access_logs",
    )
    access_type = models.CharField(max_length=32, choices=AccessType.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-accessed_at"]
        indexes = [
            models.Index(fields=["profile", "accessed_at"]),
            models.Index(fields=["accessed_by", "accessed_at"]),
            models.Index(fields=["accessed_at"]),
        ]

    def __str__(self) -> str:
        return f"ProfileAccessLog({self.profile_id}, {self.access_type}, {self.accessed_at})"


class ProfilePhoto(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="photos/")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"ProfilePhoto({self.profile_id})"


class QuestionnaireSection(models.Model):
    code = models.SlugField(max_length=64, unique=True)
    gender = models.CharField(max_length=16, choices=Profile.Gender.choices, blank=True, default="")
    title = models.CharField(max_length=128)
    hint = models.CharField(max_length=280, blank=True, default="")
    show_in_me = models.BooleanField(default=True)
    show_in_ideal = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"QuestionnaireSection({self.code})"


class QuestionnaireQuestion(models.Model):
    section = models.ForeignKey(
        QuestionnaireSection,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    code = models.SlugField(max_length=64, unique=True)
    gender = models.CharField(max_length=16, choices=Profile.Gender.choices, blank=True, default="")
    text = models.TextField()
    input_type = models.CharField(max_length=16, blank=True, default="choice")
    is_multiple = models.BooleanField(default=False)
    show_in_me = models.BooleanField(default=True)
    show_in_ideal = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"QuestionnaireQuestion({self.code})"


class QuestionnaireChoice(models.Model):
    question = models.ForeignKey(
        QuestionnaireQuestion,
        on_delete=models.CASCADE,
        related_name="choices",
    )
    value = models.CharField(max_length=64)
    label = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["question", "value"], name="uniq_question_choice_value"),
        ]

    def __str__(self) -> str:
        return f"QuestionnaireChoice({self.question_id}:{self.value})"
