from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0008_questionnairesection_hint"),
    ]

    operations = [
        migrations.AddField(
            model_name="questionnairesection",
            name="show_in_me",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="questionnairesection",
            name="show_in_ideal",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="questionnairequestion",
            name="show_in_me",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="questionnairequestion",
            name="show_in_ideal",
            field=models.BooleanField(default=True),
        ),
    ]
