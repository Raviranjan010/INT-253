from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Category, Course
from .video import embed_url


class StudioTests(TestCase):
    def test_owner_can_build_and_publish_but_pending_user_cannot_author(self):
        users = get_user_model().objects
        instructor = users.create_user(username='owner', role='instructor', is_instructor_approved=True)
        pending = users.create_user(username='pending', role='instructor')
        category = Category.objects.create(name='Mathematics')
        course = Course.objects.create(title='Algebra', category=category, instructor=instructor, is_published=False)
        studio = reverse('courses:studio', args=[course.slug])
        self.client.force_login(pending)
        self.assertEqual(self.client.get(studio).status_code, 403)

        self.client.force_login(instructor)
        self.assertEqual(self.client.get(studio).status_code, 200)
        publish = reverse('courses:studio_publication', args=[course.slug])
        self.assertEqual(self.client.get(publish).status_code, 405)
        self.client.post(publish)
        course.refresh_from_db()
        self.assertFalse(course.is_published)
        self.client.post(reverse('courses:studio_module_new', args=[course.slug]), {'title': 'Equations', 'order': 1})
        module = course.modules.get()
        self.client.post(reverse('courses:studio_lesson_new', args=[course.slug, module.pk]), {
            'title': 'Linear equations', 'order': 1, 'duration_minutes': 15, 'content': 'Work through the equation.',
        })
        self.assertEqual(module.lessons.count(), 1)
        self.client.post(publish)
        course.refresh_from_db()
        self.assertTrue(course.is_published)

    def test_video_embed_parses_allowed_hosts_only(self):
        self.assertEqual(embed_url('https://youtu.be/dQw4w9WgXcQ'), 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ')
        self.assertEqual(embed_url('https://vimeo.com/123456'), 'https://player.vimeo.com/video/123456')
        self.assertEqual(embed_url('https://youtube.com.example.org/watch?v=dQw4w9WgXcQ'), '')
