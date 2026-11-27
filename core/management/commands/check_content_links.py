from urllib.error import URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.core.management.base import BaseCommand, CommandError

from courses.models import Lesson


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Command(BaseCommand):
    help = 'Check supported video embed endpoints used by published lessons.'

    def handle(self, *args, **options):
        opener = build_opener(NoRedirects())
        checked = failed = 0
        lessons = Lesson.objects.filter(module__course__is_published=True).exclude(video_url='')
        for lesson in lessons.iterator():
            checked += 1
            url = lesson.embed_video_url
            try:
                if not url:
                    raise ValueError('Unsupported provider')
                with opener.open(Request(url, method='GET'), timeout=8) as response:
                    self.stdout.write(f'Lesson {lesson.pk}: HTTP {response.status}')
            except (URLError, ValueError, TimeoutError) as exc:
                failed += 1
                self.stderr.write(f'Lesson {lesson.pk}: {type(exc).__name__}')
        self.stdout.write(f'{checked} endpoint(s) checked, {failed} failed. HTTP success does not confirm playback or licensing.')
        if failed:
            raise CommandError('Some lesson links require review.')
