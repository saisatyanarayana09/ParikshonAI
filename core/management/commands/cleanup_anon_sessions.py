"""
Management command: cleanup_anon_sessions

Deletes anonymous ChatSession rows (user=None) older than a configurable
number of hours, along with their associated DocumentChunks and ChatMessages
(deleted automatically via CASCADE).

Usage:
    python manage.py cleanup_anon_sessions           # default: 24 hours
    python manage.py cleanup_anon_sessions --hours 48
    python manage.py cleanup_anon_sessions --dry-run
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import ChatSession


class Command(BaseCommand):
    help = "Delete anonymous ChatSession rows older than N hours to prevent DB bloat."

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Delete anonymous sessions older than this many hours (default: 24).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be deleted without actually deleting them.",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(hours=hours)

        stale_sessions = ChatSession.objects.filter(
            user__isnull=True,
            created_at__lt=cutoff,
        )

        count = stale_sessions.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] Would delete {count} anonymous session(s) older than {hours} hour(s)."
                )
            )
            return

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No stale anonymous sessions found. DB is clean."))
            return

        deleted, _ = stale_sessions.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted {count} anonymous session(s) older than {hours} hour(s). "
                f"({deleted} total rows removed including chunks and messages)"
            )
        )
