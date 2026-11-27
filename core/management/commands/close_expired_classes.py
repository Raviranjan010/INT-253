from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from live_classes.models import LiveSession


class Command(BaseCommand):
    help = 'Complete expired active classes and cancel expired classes that never started.'

    def handle(self, *args, **options):
        now = timezone.now()
        candidates = LiveSession.objects.filter(status__in=['scheduled', 'live'], scheduled_start__lt=now)
        count = 0
        for session in candidates.only('id', 'scheduled_start', 'duration_minutes', 'status').iterator():
            if session.scheduled_start + timedelta(minutes=session.duration_minutes + 15) >= now:
                continue
            count += LiveSession.objects.filter(pk=session.pk, status=session.status).update(
                status='completed' if session.status == 'live' else 'cancelled',
            )
        self.stdout.write(f'Closed {count} expired class(es).')
