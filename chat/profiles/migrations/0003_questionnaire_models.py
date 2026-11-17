import django.db.models.deletion
from django.db import migrations, models


def seed_questionnaire(apps, schema_editor):
    QuestionnaireSection = apps.get_model("profiles", "QuestionnaireSection")
    QuestionnaireQuestion = apps.get_model("profiles", "QuestionnaireQuestion")
    QuestionnaireChoice = apps.get_model("profiles", "QuestionnaireChoice")

    if QuestionnaireSection.objects.exists():
        return

    from profiles.questionnaire import QUESTIONNAIRE_SPEC

    for s_order, s in enumerate(QUESTIONNAIRE_SPEC):
        section = QuestionnaireSection.objects.create(
            code=s["id"],
            title=s["title"],
            order=s_order,
        )
        for q_order, q in enumerate(s.get("questions") or []):
            question = QuestionnaireQuestion.objects.create(
                section=section,
                code=q["id"],
                text=q["text"],
                order=q_order,
            )
            for c_order, c in enumerate(q.get("choices") or []):
                value, label = c
                QuestionnaireChoice.objects.create(
                    question=question,
                    value=value,
                    label=label,
                    order=c_order,
                )


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0002_profile_questionnaires"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuestionnaireSection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.SlugField(max_length=64, unique=True)),
                ("title", models.CharField(max_length=128)),
                ("order", models.PositiveIntegerField(default=0)),
            ],
            options={
                "ordering": ["order", "id"],
            },
        ),
        migrations.CreateModel(
            name="QuestionnaireQuestion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.SlugField(max_length=64, unique=True)),
                ("text", models.TextField()),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "section",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="questions",
                        to="profiles.questionnairesection",
                    ),
                ),
            ],
            options={
                "ordering": ["order", "id"],
            },
        ),
        migrations.CreateModel(
            name="QuestionnaireChoice",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("value", models.CharField(max_length=64)),
                ("label", models.TextField()),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "question",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="choices",
                        to="profiles.questionnairequestion",
                    ),
                ),
            ],
            options={
                "ordering": ["order", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="questionnairechoice",
            constraint=models.UniqueConstraint(
                fields=("question", "value"),
                name="uniq_question_choice_value",
            ),
        ),
        migrations.RunPython(seed_questionnaire, migrations.RunPython.noop),
    ]
