from django.db import migrations
from django.conf import settings
import json


def encrypt_existing_questionnaires(apps, schema_editor):
    """Encrypt existing questionnaire data with Fernet."""
    Profile = apps.get_model('profiles', 'Profile')
    
    for profile in Profile.objects.all():
        # Encrypt questionnaire_me
        if profile.questionnaire_me:
            try:
                settings.FERNET.decrypt(profile.questionnaire_me.encode())
            except Exception:
                json_str = json.dumps(profile.questionnaire_me, ensure_ascii=False)
                encrypted = settings.FERNET.encrypt(json_str.encode()).decode()
                Profile.objects.filter(id=profile.id).update(questionnaire_me=encrypted)
        
        # Encrypt questionnaire_ideal
        if profile.questionnaire_ideal:
            try:
                settings.FERNET.decrypt(profile.questionnaire_ideal.encode())
            except Exception:
                json_str = json.dumps(profile.questionnaire_ideal, ensure_ascii=False)
                encrypted = settings.FERNET.encrypt(json_str.encode()).decode()
                Profile.objects.filter(id=profile.id).update(questionnaire_ideal=encrypted)


def reverse_encrypt_existing_questionnaires(apps, schema_editor):
    """Reverse encryption (decrypt questionnaires)."""
    Profile = apps.get_model('profiles', 'Profile')
    
    for profile in Profile.objects.all():
        # Decrypt questionnaire_me
        if profile.questionnaire_me:
            try:
                decrypted = settings.FERNET.decrypt(profile.questionnaire_me.encode()).decode()
                Profile.objects.filter(id=profile.id).update(questionnaire_me=json.loads(decrypted))
            except Exception:
                pass
        
        # Decrypt questionnaire_ideal
        if profile.questionnaire_ideal:
            try:
                decrypted = settings.FERNET.decrypt(profile.questionnaire_ideal.encode()).decode()
                Profile.objects.filter(id=profile.id).update(questionnaire_ideal=json.loads(decrypted))
            except Exception:
                pass


class Migration(migrations.Migration):
    dependencies = [
        ('profiles', '0010_alter_profile_questionnaire_ideal_and_more'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing_questionnaires, reverse_encrypt_existing_questionnaires),
    ]
