from django.db import migrations

# Разделы, которые должны существовать в единственном экземпляре (дубликаты могли
# появиться из-за повторного импорта Excel с листами, не замапленными на код раздела).
CANONICAL_TITLES = {
    "Сексуальная совместимость": "sexual",
    "Религиозные убеждения": "religious",
}


def merge_duplicate_sections(apps, schema_editor):
    QuestionnaireSection = apps.get_model("profiles", "QuestionnaireSection")
    QuestionnaireQuestion = apps.get_model("profiles", "QuestionnaireQuestion")

    for title, canonical_code in CANONICAL_TITLES.items():
        sections = list(
            QuestionnaireSection.objects.filter(
                title=title).order_by("order", "id")
        )
        if len(sections) <= 1:
            continue

        canonical = next(
            (s for s in sections if s.code == canonical_code), sections[0])
        duplicates = [s for s in sections if s.pk != canonical.pk]

        next_order = QuestionnaireQuestion.objects.filter(
            section=canonical).count()
        for dup in duplicates:
            questions = list(
                QuestionnaireQuestion.objects.filter(
                    section=dup).order_by("order", "id")
            )
            for q in questions:
                next_order += 1
                q.section = canonical
                q.order = next_order
                q.save(update_fields=["section", "order"])
            dup.delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0017_restore_religious_section"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_sections, noop),
    ]
