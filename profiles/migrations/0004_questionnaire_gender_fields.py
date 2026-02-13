from django.db import migrations, models


GENDER_CHOICES = [
    ("male", "Мужчина"),
    ("female", "Женщина"),
    ("other", "Другое"),
]


def ensure_gender_columns(apps, schema_editor):
    connection = schema_editor.connection
    introspection = connection.introspection

    section_table = "profiles_questionnairesection"
    question_table = "profiles_questionnairequestion"

    with connection.cursor() as cursor:
        section_cols = {c.name for c in introspection.get_table_description(cursor, section_table)}
        if "gender" not in section_cols:
            schema_editor.execute(
                "ALTER TABLE %s ADD COLUMN gender varchar(16) NOT NULL DEFAULT ''" % schema_editor.quote_name(section_table)
            )

        question_cols = {c.name for c in introspection.get_table_description(cursor, question_table)}
        if "gender" not in question_cols:
            schema_editor.execute(
                "ALTER TABLE %s ADD COLUMN gender varchar(16) NOT NULL DEFAULT ''" % schema_editor.quote_name(question_table)
            )


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0003_questionnaire_models"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(ensure_gender_columns, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="questionnairesection",
                    name="gender",
                    field=models.CharField(blank=True, choices=GENDER_CHOICES, default="", max_length=16),
                ),
                migrations.AddField(
                    model_name="questionnairequestion",
                    name="gender",
                    field=models.CharField(blank=True, choices=GENDER_CHOICES, default="", max_length=16),
                ),
            ],
        ),
    ]
