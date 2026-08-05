from django.conf import settings
from django.db import migrations, models


def _unwrap_email(value):
    """Undo one or two layers of accidental Fernet double-encryption."""
    for _ in range(3):
        try:
            value = settings.FERNET.decrypt(value.encode()).decode()
        except Exception:
            break
    return value


def decrypt_emails(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT id, email FROM accounts_user")
        rows = cursor.fetchall()
        for user_id, email in rows:
            if not email:
                continue
            plain = _unwrap_email(email)
            if plain != email:
                cursor.execute(
                    "UPDATE accounts_user SET email = %s WHERE id = %s", [plain, user_id])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_merge_20260805_2104"),
    ]

    operations = [
        migrations.RunPython(decrypt_emails, noop_reverse),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
