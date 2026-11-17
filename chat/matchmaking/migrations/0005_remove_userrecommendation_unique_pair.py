from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("matchmaking", "0004_userrecommendation"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="userrecommendation",
            name="uniq_recommendation_pair",
        ),
    ]
