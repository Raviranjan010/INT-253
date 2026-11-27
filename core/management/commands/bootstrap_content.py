import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction

from courses.models import Category


CATEGORIES = ('Technology', 'Science', 'Business', 'Mathematics', 'Languages', 'Creative Skills')


class Command(BaseCommand):
    help = 'Initialize the subject taxonomy and optionally create your administrator.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--reset-content', action='store_true')
        parser.add_argument('--yes', action='store_true')

    @transaction.atomic
    def handle(self, *args, **options):
        if options['reset_content']:
            if not options['yes']:
                raise CommandError('--reset-content requires --yes.')
            self.stdout.write('This bootstrap has no managed course records to reset.')
        User = get_user_model()
        username, email, password = (os.getenv(f'ADMIN_{key}') for key in ('USERNAME', 'EMAIL', 'PASSWORD'))
        if any((username, email, password)) and not all((username, email, password)):
            raise CommandError('Set all three ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD, or none.')
        create_admin = False
        if username:
            existing = User.objects.filter(username__iexact=username).first()
            if existing and (not existing.is_superuser or existing.email.lower() != email.lower()):
                raise CommandError('The requested administrator username is already in use.')
            if not existing:
                if User.objects.filter(email__iexact=email).exists():
                    raise CommandError('The requested administrator email is already in use.')
                try:
                    validate_email(email)
                    validate_password(password, User(username=username, email=email))
                except ValidationError as exc:
                    raise CommandError('; '.join(exc.messages)) from exc
                create_admin = True
        for name in CATEGORIES:
            if not Category.objects.filter(name__iexact=name).exists():
                if not options['dry_run']:
                    Category.objects.create(name=name)
                self.stdout.write(f"{'Would create' if options['dry_run'] else 'Created'} category: {name}")
        if create_admin:
            if not options['dry_run']:
                User.objects.create_superuser(username=username, email=email, password=password, role='admin')
            self.stdout.write('Administrator planned.' if options['dry_run'] else 'Administrator created.')
        self.stdout.write('No externally sourced courses were installed.')
