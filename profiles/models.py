from django.conf import settings
from django.db import models
from django.utils import timezone


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
    questionnaire_me = models.JSONField(default=dict, blank=True)
    questionnaire_ideal = models.JSONField(default=dict, blank=True)

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
    label = models.CharField(max_length=256)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["question", "value"], name="uniq_question_choice_value"),
        ]

    def __str__(self) -> str:
        return f"QuestionnaireChoice({self.question_id}:{self.value})"
