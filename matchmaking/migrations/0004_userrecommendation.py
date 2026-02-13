import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matchmaking", "0003_userban"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserRecommendation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("score", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("seen_at", models.DateTimeField(blank=True, null=True)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recommendations_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "recommended_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recommendations_as_candidate",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "to_user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recommendations_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="userrecommendation",
            constraint=models.UniqueConstraint(
                fields=("to_user", "recommended_user"),
                name="uniq_recommendation_pair",
            ),
        ),
        migrations.AddConstraint(
            model_name="userrecommendation",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("to_user", models.F("recommended_user")),
                    _negated=True,
                ),
                name="no_self_recommendation",
            ),
        ),
    ]
