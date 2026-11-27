from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from courses.models import Course, Category
from certificates.models import Certificate, compute_digital_signature

User = get_user_model()

class CertificateCryptographicTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.instructor = User.objects.create_user(
            username='cert_inst',
            email='cert_inst@example.com',
            password='Password123!',
            role='instructor',
            is_instructor_approved=True
        )
        self.student = User.objects.create_user(
            username='cert_student',
            email='cert_student@example.com',
            password='Password123!',
            role='student'
        )
        self.category = Category.objects.create(name='Data Science', slug='data-science')
        self.course = Course.objects.create(
            title='Machine Learning Foundations',
            slug='machine-learning-foundations',
            instructor=self.instructor,
            category=self.category,
            is_published=True
        )
        self.cert = Certificate.objects.create(
            student=self.student,
            course=self.course,
            grade='Honors (100% Completion)'
        )

    def test_certificate_generation_and_signature(self):
        """Certificate should automatically generate ID, verification code, and valid HMAC signature."""
        self.assertTrue(self.cert.certificate_id.startswith('LS-'))
        self.assertTrue(len(self.cert.verification_code) > 0)
        self.assertTrue(len(self.cert.digital_signature) == 64)
        self.assertTrue(self.cert.verify_signature())

    def test_certificate_signature_tamper_detection(self):
        """If digital_signature is modified or data is tampered with, signature validation fails."""
        self.assertTrue(self.cert.verify_signature())

        # Tamper with the digital signature
        self.cert.digital_signature = '0' * 64
        self.assertFalse(self.cert.verify_signature())

    def test_grade_edit_does_not_resign_certificate(self):
        signature = self.cert.digital_signature
        self.cert.grade = 'Changed after issuance'
        self.cert.save()
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.digital_signature, signature)
        self.assertFalse(self.cert.verify_signature())
        response = self.client.get(reverse('certificates:verify'), {'id': self.cert.certificate_id})
        self.assertFalse(response.context['is_valid'])

    def test_certificate_view_page(self):
        """view_certificate renders properly and indicates valid cryptographic signature."""
        response = self.client.get(reverse('certificates:view_certificate', kwargs={'certificate_id': self.cert.certificate_id}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_signature_valid'])
        self.assertEqual(response.context['certificate'], self.cert)

    def test_certificate_public_verification_by_id(self):
        """Public verification endpoint correctly verifies by certificate_id."""
        response = self.client.get(reverse('certificates:verify'), {'id': self.cert.certificate_id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_valid'])
        self.assertTrue(response.context['is_signature_valid'])
        self.assertEqual(response.context['certificate'], self.cert)

    def test_certificate_public_verification_by_hash(self):
        """Public verification endpoint correctly verifies by verification_code hash."""
        response = self.client.get(reverse('certificates:verify_detail', kwargs={'certificate_id': self.cert.verification_code}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_valid'])
        self.assertTrue(response.context['is_signature_valid'])
        self.assertEqual(response.context['certificate'], self.cert)

    def test_invalid_certificate_verification(self):
        """Public verification rejects nonexistent IDs gracefully."""
        response = self.client.get(reverse('certificates:verify'), {'id': 'LS-NONEXISTENT-999'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['is_valid'])
        self.assertIsNone(response.context['certificate'])
