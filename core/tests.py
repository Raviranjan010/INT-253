from django.test import TestCase, Client
from django.urls import reverse
from django.db import OperationalError
from django.core.cache import cache
from django.core.management import call_command
from io import StringIO
from unittest.mock import patch
from accounts.models import CustomUser
from courses.models import Course, Category
from core.models import ContactMessage, NewsletterSubscriber

class CorePlatformSecurityAndMetricsTests(TestCase):
    def test_health_check(self):
        response = self.client.get(reverse('core:health_check'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_health_check_reports_database_outage(self):
        with patch('core.views.connection.cursor', side_effect=OperationalError):
            response = self.client.get(reverse('core:health_check'))
        self.assertEqual(response.status_code, 503)

    def test_public_sitemap_excludes_drafts(self):
        self.assertContains(self.client.get(reverse('core:robots')), '/sitemap.xml')
        self.assertContains(self.client.get(reverse('core:sitemap')), self.course.slug)
        self.course.is_published = False
        self.course.save(update_fields=['is_published'])
        self.assertNotContains(self.client.get(reverse('core:sitemap')), self.course.slug)
        self.assertContains(self.client.get('/missing-page/'), 'Page not found', status_code=404)

    def test_contact_honeypot_and_throttle(self):
        cache.clear()
        self.addCleanup(cache.clear)
        url = reverse('core:contact')
        payload = {'name': 'Reader', 'email': 'reader@example.test', 'subject': 'Question', 'message': 'Hello'}
        self.client.post(url, {**payload, 'website': 'filled'})
        self.assertFalse(ContactMessage.objects.exists())
        for _ in range(4):
            self.assertEqual(self.client.post(url, payload).status_code, 302)
        self.assertEqual(self.client.post(url, payload).status_code, 429)

    def test_bootstrap_is_idempotent_and_does_not_create_courses_or_users(self):
        from unittest.mock import patch
        output = StringIO()
        with patch.dict('os.environ', {'ADMIN_USERNAME': '', 'ADMIN_EMAIL': '', 'ADMIN_PASSWORD': ''}):
            call_command('bootstrap_content', dry_run=True, stdout=output)
            self.assertEqual(Category.objects.count(), 1)
            call_command('bootstrap_content', stdout=output)
            total = Category.objects.count()
            call_command('bootstrap_content', stdout=output)
        self.assertEqual(Category.objects.count(), total)
        self.assertEqual(Course.objects.count(), 1)
        self.assertEqual(CustomUser.objects.count(), 2)
        self.course.is_published = False
        self.course.save(update_fields=['is_published'])
        call_command('check_content_links', stdout=output)
        self.assertIn('0 endpoint(s) checked, 0 failed', output.getvalue())

    def test_newsletter_requires_post_and_rejects_external_referer(self):
        url = reverse('core:subscribe')
        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(
            url,
            {'email': 'safe@example.com'},
            HTTP_REFERER='https://evil.example/phish',
        )
        self.assertRedirects(response, reverse('core:home'))

    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Science', slug='science')
        self.teacher = CustomUser.objects.create_user(
            username='core_teacher', email='ct@test.com', password='Password123!', role='instructor', is_instructor_approved=True
        )
        self.student = CustomUser.objects.create_user(
            username='core_student', email='cs@test.com', password='Password123!', role='student', country='India'
        )
        self.course = Course.objects.create(
            title='Core Science Course',
            slug='core-science-course',
            category=self.category,
            instructor=self.teacher,
            short_description='Test short description',
            description='Test long description',
            is_published=True
        )

    def test_homepage_verified_database_statistics(self):
        res = self.client.get(reverse('core:home'))
        self.assertEqual(res.status_code, 200)
        # Stats should come from context processor
        stats = res.context['GLOBAL_STATS']
        # Must reflect actual database records, not hardcoded 12,500 or 85
        self.assertEqual(stats['students'], 1)
        self.assertEqual(stats['courses'], 1)
        self.assertEqual(stats['countries'], 1)

    def test_demographics_impact_page(self):
        res = self.client.get(reverse('core:demographics_impact'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Demographic Inclusivity')

    def test_about_page(self):
        res = self.client.get(reverse('core:about'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'About Live School')

    def test_demo_login_is_unavailable(self):
        self.assertEqual(self.client.get('/demo-login/admin/').status_code, 404)

    def test_contact_form_submission(self):
        res = self.client.post(reverse('core:contact'), {
            'name': 'Ravi Kumar',
            'email': 'ravi@example.com',
            'subject': 'Rural accessibility inquiry',
            'message': 'How does LiveSchool optimize for low-bandwidth connections?',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(ContactMessage.objects.filter(email='ravi@example.com').exists())

    def test_newsletter_subscription(self):
        res = self.client.post(reverse('core:subscribe'), {
            'email': 'subscriber@example.com'
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(NewsletterSubscriber.objects.filter(email='subscriber@example.com').exists())
