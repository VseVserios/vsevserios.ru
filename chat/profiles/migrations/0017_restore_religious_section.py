from django.db import migrations, models

RELIGIOUS_QUESTIONS = [
    ("religious_01", "Вера важна для меня"),
    ("religious_02", "Я регулярно посещаю религиозные службы"),
    ("religious_03", "Религиозные традиции важны в моей жизни"),
    ("religious_04", "Я хотел(а) бы, чтобы партнёр разделял мои убеждения"),
    ("religious_05", "Я готов(а) уважать убеждения партнёра, даже если они отличаются"),
    ("religious_06", "Религия влияет на мои решения в жизни"),
    ("religious_07", "Я открыт(а) к обсуждению религиозных вопросов"),
    ("religious_08", "Духовное развитие важно для меня"),
    ("religious_09", "Я практикую религиозные обряды"),
    ("religious_10", "Религиозные ценности влияют на мой выбор партнёра"),
]

SCALE_CHOICES = [
    ("1", "Совсем не про меня"),
    ("2", "Скорее не про меня"),
    ("3", "50/50"),
    ("4", "Скорее про меня"),
    ("5", "Полностью про меня"),
]


def restore_religious_section(apps, schema_editor):
    QuestionnaireSection = apps.get_model("profiles", "QuestionnaireSection")
    QuestionnaireQuestion = apps.get_model("profiles", "QuestionnaireQuestion")
    QuestionnaireChoice = apps.get_model("profiles", "QuestionnaireChoice")

    if QuestionnaireSection.objects.filter(code="religious").exists():
        return

    sexual = QuestionnaireSection.objects.filter(code="sexual").first()
    if sexual is None:
        # Анкета ещё не инициализирована в БД (используется статический fallback
        # из profiles/questionnaire.py, в котором раздел religious уже есть) —
        # восстанавливать здесь нечего.
        return

    QuestionnaireSection.objects.filter(
        order__gt=sexual.order).update(order=models.F("order") + 1)

    section = QuestionnaireSection.objects.create(
        code="religious",
        title="Религиозные убеждения",
        gender="",
        hint="",
        show_in_me=True,
        show_in_ideal=True,
        order=sexual.order + 1,
    )

    for q_order, (code, text) in enumerate(RELIGIOUS_QUESTIONS, start=1):
        question = QuestionnaireQuestion.objects.create(
            section=section,
            code=code,
            gender="",
            text=text,
            input_type="choice",
            is_multiple=False,
            show_in_me=True,
            show_in_ideal=True,
            order=q_order,
        )
        for c_order, (value, label) in enumerate(SCALE_CHOICES, start=1):
            QuestionnaireChoice.objects.create(
                question=question,
                value=value,
                label=label,
                order=c_order,
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0016_profile_native_language"),
    ]

    operations = [
        migrations.RunPython(restore_religious_section, noop),
    ]
