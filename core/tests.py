from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from courses.models import Course, Category, Module, Lesson, Enrollment, LessonProgress
from live_classes.models import LiveSession
from quizzes.models import Quiz, Question, Choice
from certificates.models import Certificate

class LiveSchoolTestSuite(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.admin = CustomUser.objects.create_superuser(username='admin_test', email='admin@test.com', password='password123')
        self.teacher = CustomUser.objects.create_user(username='teacher_test', email='teacher@test.com', password='password123', role='instructor')
        self.student = CustomUser.objects.create_user(username='student_test', email='student@test.com', password='password123', role='student', demographic_group='rural')

        # Category & Course
        self.category = Category.objects.create(name='Test Category', slug='test-category', icon='bi-book')
        self.course = Course.objects.create(
            title='Test Course Python',
            slug='test-course-python',
            category=self.category,
            instructor=self.teacher,
            short_description='A great test course',
            description='Detailed test course description',
            level='beginner',
            is_published=True
        )

        # Module & Lessons
        self.module = Module.objects.create(course=self.course, title='Module 1', order=1)
        self.lesson1 = Lesson.objects.create(module=self.module, title='Lesson 1', order=1, content='Content 1', duration_minutes=10)
        self.lesson2 = Lesson.objects.create(module=self.module, title='Lesson 2', order=2, content='Content 2', duration_minutes=15)

    def test_homepage_loads(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Live School')
        self.assertContains(response, 'World-Class Free Education')

    def test_course_list_and_detail(self):
        # Course list
        res_list = self.client.get(reverse('courses:course_list'))
        self.assertEqual(res_list.status_code, 200)
        self.assertContains(res_list, 'Test Course Python')

        # Course detail
        res_detail = self.client.get(reverse('courses:course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(res_detail.status_code, 200)
        self.assertContains(res_detail, 'Test Course Python')
        self.assertContains(res_detail, 'Enroll Now for Free')

    def test_student_enrollment_and_lesson_completion(self):
        self.client.login(username='student_test', password='password123')
        
        # Enroll
        enroll_res = self.client.get(reverse('courses:enroll_course', kwargs={'slug': self.course.slug}), follow=True)
        self.assertEqual(enroll_res.status_code, 200)
        enrollment = Enrollment.objects.get(student=self.student, course=self.course)
        self.assertEqual(enrollment.progress_percentage, 0)

        # Mark lesson 1 complete
        toggle_res = self.client.post(
            reverse('courses:toggle_lesson_completion', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id}),
            follow=True
        )
        self.assertEqual(toggle_res.status_code, 200)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress_percentage, 50)
        self.assertFalse(enrollment.is_completed)

        # Mark lesson 2 complete -> 100% and auto certificate generation
        toggle_res2 = self.client.post(
            reverse('courses:toggle_lesson_completion', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson2.id}),
            follow=True
        )
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress_percentage, 100)
        self.assertTrue(enrollment.is_completed)
        self.assertTrue(Certificate.objects.filter(student=self.student, course=self.course).exists())

    def test_certificate_public_verification(self):
        cert = Certificate.objects.create(
            certificate_id='LS-TEST-CERT123',
            student=self.student,
            course=self.course
        )

        # Verify page check with query
        res = self.client.get(reverse('certificates:verify'), {'id': 'LS-TEST-CERT123'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'AUTHENTIC & VERIFIED')
        self.assertContains(res, self.student.username)

    def test_live_class_flow(self):
        self.client.login(username='student_test', password='password123')
        session = LiveSession.objects.create(
            title='Live Test WebRTC Class',
            instructor=self.teacher,
            description='Test live video class',
            scheduled_start=timezone.now(),
            duration_minutes=45,
            status='live'
        )

        res = self.client.get(reverse('live_classes:live_class_room', kwargs={'session_id': session.id}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Live Test WebRTC Class')
        self.assertContains(res, 'Live Doubt Board')
