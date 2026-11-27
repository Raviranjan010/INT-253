from datetime import datetime, timedelta, timezone as utc
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import LiveSessionScheduleForm
from .models import LiveSession


class LiveLifecycleTests(TestCase):
    def test_host_controls_status_and_join_link(self):
        users = get_user_model().objects
        host = users.create_user(username='host', role='instructor', is_instructor_approved=True)
        student = users.create_user(username='learner')
        session = LiveSession.objects.create(title='Office hours', instructor=host, scheduled_start=timezone.now(),
                                             meeting_url='https://meet.google.com/')
        manage = reverse('live_classes:manage_session', args=[session.pk])
        room = reverse('live_classes:live_class_room', args=[session.pk])
        self.client.force_login(student)
        self.assertNotContains(self.client.get(room), 'Join meeting')
        self.assertEqual(self.client.post(manage, {'action': 'start'}).status_code, 403)
        self.client.force_login(host)
        self.assertEqual(self.client.get(manage).status_code, 405)
        self.client.post(manage, {'action': 'start'})
        self.assertContains(self.client.get(room), 'Join meeting')
        self.client.post(manage, {'action': 'end'})
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')
        self.assertIn(session.pk.hex, session.room_name)

    def test_datetime_local_is_interpreted_as_ist_and_past_rejected(self):
        year = timezone.localdate().year + 1
        values = {'title': 'Office hours', 'scheduled_start': f'{year}-01-01T18:00',
                  'duration_minutes': 60, 'description': 'Questions and answers', 'target_demographics': 'Everyone'}
        form = LiveSessionScheduleForm(values)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['scheduled_start'].astimezone(utc.utc),
                         datetime(year, 1, 1, 12, 30, tzinfo=utc.utc))
        values['scheduled_start'] = (timezone.localtime() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        self.assertIn('scheduled_start', LiveSessionScheduleForm(values).errors)
