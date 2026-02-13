from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Swipe(models.Model):
    class Value(models.TextChoices):
        LIKE = "like", "Like"
        PASS = "pass", "Pass"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="swipes_made",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="swipes_received",
    )
    value = models.CharField(max_length=8, choices=Value.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"],
                name="uniq_swipe_pair",
            ),
            models.CheckConstraint(
                condition=~Q(from_user=models.F("to_user")),
                name="no_self_swipe",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.from_user_id}->{self.to_user_id}:{self.value}"


class Match(models.Model):
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matches_as_user1",
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matches_as_user2",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin_chat = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user1", "user2"], name="uniq_match_pair"),
        ]

    def save(self, *args, **kwargs):
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1_id, self.user2_id = self.user2_id, self.user1_id
        return super().save(*args, **kwargs)

    @staticmethod
    def normalize_pair(a, b):
        return (a, b) if a.id < b.id else (b, a)

    @classmethod
    def get_or_create_for_users(cls, a, b):
        u1, u2 = cls.normalize_pair(a, b)
        return cls.objects.get_or_create(user1=u1, user2=u2)

    def other(self, user):
        if user.id == self.user1_id:
            return self.user2
        return self.user1

    def __str__(self) -> str:
        return f"Match({self.user1_id},{self.user2_id})"


class UserBlock(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_made",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocks_received",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["blocker", "blocked"],
                name="uniq_block_pair",
            ),
            models.CheckConstraint(
                condition=~Q(blocker=models.F("blocked")),
                name="no_self_block",
            ),
        ]

    def __str__(self) -> str:
        return f"Block({self.blocker_id}->{self.blocked_id})"


class UserReport(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", "Спам/реклама"
        FAKE = "fake", "Фейк/подмена"
        ABUSE = "abuse", "Оскорбления/агрессия"
        NUDITY = "nudity", "Неприемлемый контент"
        OTHER = "other", "Другое"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_made",
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_received",
    )
    reason = models.CharField(max_length=32, choices=Reason.choices)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports_resolved",
    )
    admin_note = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(reporter=models.F("reported_user")),
                name="no_self_report",
            ),
        ]

    def __str__(self) -> str:
        return f"Report({self.reporter_id}->{self.reported_user_id}:{self.reason})"


class UserBanQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(revoked_at__isnull=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        )


class UserBan(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", "Спам/реклама"
        FAKE = "fake", "Фейк/подмена"
        ABUSE = "abuse", "Оскорбления/агрессия"
        NUDITY = "nudity", "Неприемлемый контент"
        OTHER = "other", "Другое"

    objects = UserBanQuerySet.as_manager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bans",
    )
    reason = models.CharField(max_length=32, choices=Reason.choices)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bans_created",
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bans_revoked",
    )

    class Meta:
        ordering = ["-created_at"]

    def is_active(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is None:
            return True
        return self.expires_at > timezone.now()

    def __str__(self) -> str:
        return f"Ban({self.user_id}:{self.reason})"


class UserRecommendation(models.Model):
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendations_received",
    )
    recommended_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recommendations_as_candidate",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations_created",
    )
    score = models.PositiveSmallIntegerField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=~Q(to_user=models.F("recommended_user")),
                name="no_self_recommendation",
            ),
        ]

    def __str__(self) -> str:
        return f"Recommendation({self.to_user_id}->{self.recommended_user_id})"


class HomePage(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200, blank=True, default="")
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["slug"]

    def __str__(self) -> str:
        return f"HomePage({self.slug})"


class HomeBlock(models.Model):
    class Type(models.TextChoices):
        HERO = "hero", "Hero"
        STATS = "stats", "Stats"
        STEPS = "steps", "Steps"
        LIST = "list", "List"
        GRID = "grid", "Grid"
        FAQ = "faq", "FAQ"
        CTA = "cta", "CTA"

    page = models.ForeignKey(HomePage, on_delete=models.CASCADE, related_name="blocks")
    type = models.CharField(max_length=32, choices=Type.choices)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    badge = models.CharField(max_length=80, blank=True, default="")
    title = models.CharField(max_length=200, blank=True, default="")
    subtitle = models.CharField(max_length=260, blank=True, default="")
    body = models.TextField(blank=True, default="")

    primary_button_text = models.CharField(max_length=60, blank=True, default="")
    primary_button_url = models.CharField(max_length=200, blank=True, default="")
    secondary_button_text = models.CharField(max_length=60, blank=True, default="")
    secondary_button_url = models.CharField(max_length=200, blank=True, default="")

    image = models.ImageField(upload_to="landing/", blank=True, null=True)
    items = models.JSONField(blank=True, null=True)
    extra = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["order", "id"]
        indexes = [
            models.Index(fields=["page", "is_active", "order"]),
        ]

    def __str__(self) -> str:
        return f"HomeBlock({self.page.slug}:{self.type}:{self.order})"
