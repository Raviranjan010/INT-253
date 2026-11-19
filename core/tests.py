from django.test import TestCase, Client, override_settings
from django.urls import reverse
from accounts.models import CustomUser
from courses.models import Course, Category
from core.models import ContactMessage, NewsletterSubscriber

class CorePlatformSecurityAndMetricsTests(TestCase):
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
        self.assertContains(res, 'Problem Statement')

    @override_settings(DEBUG=False)
    def test_demo_login_disabled_when_debug_false(self):
        res = self.client.get(reverse('core:demo_login', kwargs={'role': 'student'}), follow=True)
        # Must redirect to login with error message when DEBUG is False
        self.assertContains(res, 'Security Violation')

    @override_settings(DEBUG=True)
    def test_demo_login_allowed_in_debug_mode(self):
        CustomUser.objects.create_user(username='student_demo', email='demo@test.com', password='Password123!', role='student')
        res = self.client.get(reverse('core:demo_login', kwargs={'role': 'student'}), follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Logged in as Demo Student')

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
