from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import UserNotification


class Command(BaseCommand):
    help = "Delete old notifications (older than specified days)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Delete notifications older than this many days (default: 90)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        cutoff_date = timezone.now() - timedelta(days=days)

        qs = UserNotification.objects.filter(created_at__lt=cutoff_date)
        count = qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} notifications older than {days} days"
                )
            )
        else:
            deleted_count, _ = qs.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted {deleted_count} notifications older than {days} days"
                )
            )
