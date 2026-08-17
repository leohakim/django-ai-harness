"""Seed the local database with development data.

Extend this command as the domain grows: it is the one entry point that both humans and
agents use to get a realistic local dataset, which keeps fixtures out of the test suite.
"""

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seed the database with development data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--users",
            type=int,
            default=3,
            help="Number of users to create (default: 3).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            from harness_example.users.tests.factories import UserFactory
        except ImportError as exc:  # pragma: no cover - factories are project-specific
            msg = f"Could not import UserFactory: {exc}"
            self.stderr.write(self.style.ERROR(msg))
            self.stdout.write("Add factories, then extend this command for your domain.")
            return

        users = UserFactory.create_batch(options["users"])
        self.stdout.write(self.style.SUCCESS(f"Created {len(users)} users"))
