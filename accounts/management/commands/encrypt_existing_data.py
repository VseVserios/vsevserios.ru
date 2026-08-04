from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User
from profiles.models import Profile


class Command(BaseCommand):
    help = "Encrypt existing email and questionnaire data with Fernet"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be encrypted without actually encrypting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No data will be modified"))

        # Encrypt emails
        users = User.objects.all()
        for user in users:
            if user.email:
                try:
                    # Try to decrypt - if it fails, data is not encrypted
                    settings.FERNET.decrypt(user.email.encode())
                    self.stdout.write(f"User {user.id} email already encrypted")
                except Exception:
                    if dry_run:
                        self.stdout.write(f"Would encrypt email for user {user.id}: {user.email[:20]}...")
                    else:
                        encrypted = settings.FERNET.encrypt(user.email.encode()).decode()
                        User.objects.filter(id=user.id).update(email=encrypted)
                        self.stdout.write(self.style.SUCCESS(f"Encrypted email for user {user.id}"))

        # Encrypt questionnaires
        profiles = Profile.objects.all()
        for profile in profiles:
            if profile.questionnaire_me:
                try:
                    import json
                    settings.FERNET.decrypt(profile.questionnaire_me.encode())
                    self.stdout.write(f"Profile {profile.id} questionnaire_me already encrypted")
                except Exception:
                    if dry_run:
                        self.stdout.write(f"Would encrypt questionnaire_me for profile {profile.id}")
                    else:
                        import json
                        json_str = json.dumps(profile.questionnaire_me, ensure_ascii=False)
                        encrypted = settings.FERNET.encrypt(json_str.encode()).decode()
                        Profile.objects.filter(id=profile.id).update(questionnaire_me=encrypted)
                        self.stdout.write(self.style.SUCCESS(f"Encrypted questionnaire_me for profile {profile.id}"))

            if profile.questionnaire_ideal:
                try:
                    import json
                    settings.FERNET.decrypt(profile.questionnaire_ideal.encode())
                    self.stdout.write(f"Profile {profile.id} questionnaire_ideal already encrypted")
                except Exception:
                    if dry_run:
                        self.stdout.write(f"Would encrypt questionnaire_ideal for profile {profile.id}")
                    else:
                        import json
                        json_str = json.dumps(profile.questionnaire_ideal, ensure_ascii=False)
                        encrypted = settings.FERNET.encrypt(json_str.encode()).decode()
                        Profile.objects.filter(id=profile.id).update(questionnaire_ideal=encrypted)
                        self.stdout.write(self.style.SUCCESS(f"Encrypted questionnaire_ideal for profile {profile.id}"))

        self.stdout.write(self.style.SUCCESS("Encryption complete"))
