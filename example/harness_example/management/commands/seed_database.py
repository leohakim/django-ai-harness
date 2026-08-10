"""Seed local/dev database with Factory Boy (customize per project)."""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed the database with development data."

    @transaction.atomic
    def handle(self, *args, **options):
        # Example: create a couple of users if factories exist.
        try:
            from harness_example.users.tests.factories import UserFactory
        except Exception as exc:  # pragma: no cover
            self.stderr.write(self.style.ERROR(f"Could not import UserFactory: {exc}"))
            self.stdout.write(
                "Add factories and extend this command as your domain grows."
            )
            return

        users = UserFactory.create_batch(3)
        self.stdout.write(self.style.SUCCESS(f"Created {len(users)} users"))
