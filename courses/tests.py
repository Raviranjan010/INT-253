from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser, XPLedger
from courses.models import Course, Category, Module, Lesson, Enrollment, LessonProgress, CourseReview
from certificates.models import Certificate

class CoursesFunctionalityAndSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.instructor = CustomUser.objects.create_user(
            username='course_prof', email='cp@test.com', password='Password123!', role='instructor', is_instructor_approved=True
        )
        self.other_instructor = CustomUser.objects.create_user(
            username='other_prof', email='op@test.com', password='Password123!', role='instructor', is_instructor_approved=True
        )
        self.student = CustomUser.objects.create_user(
            username='course_student', email='cstudent@test.com', password='Password123!', role='student'
        )
        self.category = Category.objects.create(name='Computing', slug='computing')

        self.course = Course.objects.create(
            title='Python Fundamentals',
            slug='python-fundamentals',
            category=self.category,
            instructor=self.instructor,
            short_description='Learn python step by step',
            description='Full curriculum description',
            level='beginner',
            is_published=True
        )
        self.module = Module.objects.create(course=self.course, title='Module 1', order=1)
        self.lesson1 = Lesson.objects.create(module=self.module, title='Variables', order=1, duration_minutes=15)
        self.lesson2 = Lesson.objects.create(module=self.module, title='Loops', order=2, duration_minutes=20)

    def test_course_list_and_sorting_by_actual_rating(self):
        # Unreviewed course should have average_rating as None (not artificial 5.0)
        self.assertIsNone(self.course.average_rating)

        # Enroll student and add review
        Enrollment.objects.create(student=self.student, course=self.course)
        CourseReview.objects.create(course=self.course, student=self.student, rating=4, review_text='Good course')
        self.assertEqual(self.course.average_rating, 4.0)

        # Test sorting by rating
        res = self.client.get(reverse('courses:course_list') + '?sort=rating')
        self.assertEqual(res.status_code, 200)

    def test_unpublished_course_permission(self):
        draft_course = Course.objects.create(
            title='Draft Course',
            slug='draft-course',
            category=self.category,
            instructor=self.instructor,
            short_description='Draft description',
            description='Draft long',
            is_published=False
        )

        # Unauthenticated or other student cannot access
        res = self.client.get(reverse('courses:course_detail', kwargs={'slug': draft_course.slug}))
        self.assertEqual(res.status_code, 302)

        # Host instructor CAN access
        self.client.login(username='course_prof', password='Password123!')
        res_inst = self.client.get(reverse('courses:course_detail', kwargs={'slug': draft_course.slug}))
        self.assertEqual(res_inst.status_code, 200)

    def test_enrollment_enforces_post(self):
        self.client.login(username='course_student', password='Password123!')
        
        # GET request should NOT enroll user
        get_res = self.client.get(reverse('courses:enroll_course', kwargs={'slug': self.course.slug}), follow=True)
        self.assertFalse(Enrollment.objects.filter(student=self.student, course=self.course).exists())

        # POST request enrolls user
        post_res = self.client.post(reverse('courses:enroll_course', kwargs={'slug': self.course.slug}), follow=True)
        self.assertEqual(post_res.status_code, 200)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())
        # Enrollment XP awarded once
        self.assertTrue(XPLedger.objects.filter(user=self.student, action='course_enrolled').exists())

    def test_toggle_lesson_completion_and_certificate(self):
        self.client.login(username='course_student', password='Password123!')
        Enrollment.objects.create(student=self.student, course=self.course)

        toggle_url = reverse('courses:toggle_lesson_completion', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson1.id})

        # GET method must be rejected with 405
        get_res = self.client.get(toggle_url)
        self.assertEqual(get_res.status_code, 405)

        # Complete lesson 1 (50% progress)
        post_res1 = self.client.post(toggle_url, follow=True)
        self.assertEqual(post_res1.status_code, 200)
        enrollment = Enrollment.objects.get(student=self.student, course=self.course)
        self.assertEqual(enrollment.progress_percentage, 50)
        self.assertFalse(enrollment.is_completed)
        self.assertFalse(Certificate.objects.filter(student=self.student, course=self.course).exists())

        # Complete lesson 2 (100% progress -> certificate issued)
        toggle_url2 = reverse('courses:toggle_lesson_completion', kwargs={'course_slug': self.course.slug, 'lesson_id': self.lesson2.id})
        post_res2 = self.client.post(toggle_url2, follow=True)
        self.assertEqual(post_res2.status_code, 200)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.progress_percentage, 100)
        self.assertTrue(enrollment.is_completed)
        self.assertTrue(Certificate.objects.filter(student=self.student, course=self.course).exists())

    def test_course_editing_and_deletion_permissions(self):
        # Non-owner instructor cannot edit
        self.client.login(username='other_prof', password='Password123!')
        edit_url = reverse('courses:edit_course', kwargs={'slug': self.course.slug})
        res_unauthorized = self.client.post(edit_url, {'title': 'Hacked Title'})
        self.assertEqual(res_unauthorized.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Python Fundamentals')

        # Owner instructor CAN edit
        self.client.login(username='course_prof', password='Password123!')
        res_authorized = self.client.post(edit_url, {
            'title': 'Python Fundamentals Advanced Edition',
            'category': self.category.id,
            'level': 'intermediate',
            'short_description': 'Updated short description',
            'description': 'Updated full description',
            'estimated_hours': 10,
            'language': 'English',
            'is_published': True
        })
        self.assertEqual(res_authorized.status_code, 302)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Python Fundamentals Advanced Edition')
