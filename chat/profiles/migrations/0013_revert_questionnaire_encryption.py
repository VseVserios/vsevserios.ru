import json

from django.conf import settings
from django.db import migrations, models


def _unwrap_json(value):
    """Undo accidental Fernet double-encryption of JSON questionnaire data."""
    for _ in range(4):
        if isinstance(value, dict):
            return value
        if not isinstance(value, str) or not value:
            return {}
        try:
            value = settings.FERNET.decrypt(value.encode()).decode()
        except Exception:
            try:
                parsed = json.loads(value)
            except Exception:
                return {}
            if isinstance(parsed, dict):
                return parsed
            value = parsed
            continue
        try:
            value = json.loads(value)
        except Exception:
            return {}
    return value if isinstance(value, dict) else {}


def decrypt_questionnaires(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, questionnaire_me, questionnaire_ideal FROM profiles_profile")
        rows = cursor.fetchall()
        for row_id, q_me, q_ideal in rows:
            new_me = _unwrap_json(q_me) if q_me else {}
            new_ideal = _unwrap_json(q_ideal) if q_ideal else {}
            me_json = json.dumps(new_me, ensure_ascii=False)
            ideal_json = json.dumps(new_ideal, ensure_ascii=False)
            if vendor == "postgresql":
                cursor.execute(
                    "UPDATE profiles_profile SET questionnaire_me = %s::jsonb, "
                    "questionnaire_ideal = %s::jsonb WHERE id = %s",
                    [me_json, ideal_json, row_id],
                )
            else:
                cursor.execute(
                    "UPDATE profiles_profile SET questionnaire_me = %s, "
                    "questionnaire_ideal = %s WHERE id = %s",
                    [me_json, ideal_json, row_id],
                )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0012_merge_20260805_2104"),
    ]

    operations = [
        migrations.RunPython(decrypt_questionnaires, noop_reverse),
        migrations.AlterField(
            model_name="profile",
            name="questionnaire_ideal",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name="profile",
            name="questionnaire_me",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
