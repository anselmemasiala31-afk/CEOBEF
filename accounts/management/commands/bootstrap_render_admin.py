import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = 'Create the initial Render administrator from one-time environment variables.'

    def handle(self, *args, **options):
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', '').strip()
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', '').strip()
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', '')
        if not username or not email or not password:
            raise CommandError('Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, and DJANGO_SUPERUSER_PASSWORD in the Render service environment.')
        if len(password) < 16:
            raise CommandError('DJANGO_SUPERUSER_PASSWORD must contain at least 16 characters.')

        user_model = get_user_model()
        with transaction.atomic():
            existing = user_model.objects.filter(username=username).first()
            if existing:
                if not existing.is_superuser:
                    raise CommandError(f'The existing account {username!r} is not a superuser; refusing to modify it.')
                self.stdout.write(self.style.WARNING(f'Superuser {username!r} already exists; leaving it unchanged.'))
                return
            user_model.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Created the initial Render superuser {username!r}.'))
