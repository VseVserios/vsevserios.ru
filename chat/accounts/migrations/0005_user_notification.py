from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_rename_accounts_pas_user_id_5fcefe_idx_accounts_pa_user_id_8b0b73_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserNotification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "event",
                    models.CharField(
                        choices=[("new_match", "Новый мэтч"), ("new_message", "Новое сообщение")],
                        max_length=64,
                    ),
                ),
                ("title", models.CharField(max_length=140)),
                ("body", models.CharField(blank=True, default="", max_length=300)),
                ("url", models.CharField(blank=True, default="", max_length=300)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="usernotification",
            index=models.Index(fields=["recipient", "is_read", "created_at"], name="acc_notif_rec_read_created_idx"),
        ),
    ]
