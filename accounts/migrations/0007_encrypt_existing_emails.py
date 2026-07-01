from django.db import migrations
from django.conf import settings


def encrypt_existing_emails(apps, schema_editor):
    """Encrypt existing email addresses with Fernet."""
    User = apps.get_model('accounts', 'User')
    
    for user in User.objects.all():
        if user.email:
            try:
                # Try to decrypt - if it fails, data is not encrypted
                settings.FERNET.decrypt(user.email.encode())
            except Exception:
                # Data is not encrypted, encrypt it
                encrypted = settings.FERNET.encrypt(user.email.encode()).decode()
                User.objects.filter(id=user.id).update(email=encrypted)


def reverse_encrypt_existing_emails(apps, schema_editor):
    """Reverse encryption (decrypt emails)."""
    User = apps.get_model('accounts', 'User')
    
    for user in User.objects.all():
        if user.email:
            try:
                decrypted = settings.FERNET.decrypt(user.email.encode()).decode()
                User.objects.filter(id=user.id).update(email=decrypted)
            except Exception:
                # Data is already decrypted or corrupted, skip
                pass


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0006_alter_user_email_alter_usernotification_event'),
    ]

    operations = [
        migrations.RunPython(encrypt_existing_emails, reverse_encrypt_existing_emails),
    ]
