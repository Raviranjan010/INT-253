from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser, XPLedger
from courses.models import Course, Category, Enrollment
from live_classes.models import LiveSession, LiveClassDoubt, SessionAttendee

class LiveClassesFunctionalityAndSecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.instructor = CustomUser.objects.create_user(
            username='live_teacher', email='lt@test.com', password='Password123!', role='instructor', is_instructor_approved=True
        )
        self.enrolled_student = CustomUser.objects.create_user(
            username='enrolled_stud', email='es@test.com', password='Password123!', role='student'
        )
        self.unenrolled_student = CustomUser.objects.create_user(
            username='unenrolled_stud', email='us@test.com', password='Password123!', role='student'
        )
        self.category = Category.objects.create(name='Live Tech', slug='live-tech')
        self.course = Course.objects.create(
            title='Live Full-Stack Course',
            slug='live-fullstack-course',
            category=self.category,
            instructor=self.instructor,
            is_published=True
        )
        Enrollment.objects.create(student=self.enrolled_student, course=self.course)

        self.session = LiveSession.objects.create(
            title='WebRTC Live Masterclass',
            course=self.course,
            instructor=self.instructor,
            description='Live coding session',
            scheduled_start=timezone.now() + timezone.timedelta(hours=1),
            duration_minutes=60,
            status='scheduled'
        )

    def test_live_class_list_view(self):
        res = self.client.get(reverse('live_classes:live_class_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'WebRTC Live Masterclass')

    def test_classroom_enrollment_access_restriction(self):
        # Unenrolled student should be blocked and redirected
        self.client.login(username='unenrolled_stud', password='Password123!')
        res_unenrolled = self.client.get(reverse('live_classes:live_class_room', kwargs={'session_id': self.session.id}))
        self.assertEqual(res_unenrolled.status_code, 302)

        # Enrolled student CAN join
        self.client.login(username='enrolled_stud', password='Password123!')
        res_enrolled = self.client.get(reverse('live_classes:live_class_room', kwargs={'session_id': self.session.id}))
        self.assertEqual(res_enrolled.status_code, 200)
        self.assertContains(res_enrolled, 'WebRTC Live Masterclass')
        self.assertFalse(SessionAttendee.objects.filter(session=self.session, user=self.enrolled_student).exists())
        self.session.status = 'live'
        self.session.save(update_fields=['status'])
        self.client.get(reverse('live_classes:live_class_room', kwargs={'session_id': self.session.id}))
        self.assertTrue(SessionAttendee.objects.filter(session=self.session, user=self.enrolled_student).exists())

    def test_attendance_xp_not_farmable(self):
        self.session.status = 'live'
        self.session.save(update_fields=['status'])
        self.client.login(username='enrolled_stud', password='Password123!')
        initial_xp = self.enrolled_student.xp_points

        # First visit awards attendance XP
        self.client.get(reverse('live_classes:live_class_room', kwargs={'session_id': self.session.id}))
        self.enrolled_student.refresh_from_db()
        self.assertEqual(self.enrolled_student.xp_points, initial_xp + 10)

        # Refreshing / revisiting the page should NOT award XP again
        self.client.get(reverse('live_classes:live_class_room', kwargs={'session_id': self.session.id}))
        self.enrolled_student.refresh_from_db()
        self.assertEqual(self.enrolled_student.xp_points, initial_xp + 10)

    def test_post_doubt_enforces_post(self):
        self.client.login(username='enrolled_stud', password='Password123!')
        doubt_url = reverse('live_classes:post_doubt', kwargs={'session_id': self.session.id})

        # GET should be rejected with 405
        get_res = self.client.get(doubt_url)
        self.assertEqual(get_res.status_code, 405)

        # POST creates doubt
        post_res = self.client.post(doubt_url, {'question': 'How does WebRTC peer connection work?'}, follow=True)
        self.assertEqual(post_res.status_code, 200)
        self.assertTrue(LiveClassDoubt.objects.filter(session=self.session, student=self.enrolled_student).exists())

    def test_unenrolled_student_cannot_post_doubt(self):
        self.client.login(username='unenrolled_stud', password='Password123!')
        response = self.client.post(
            reverse('live_classes:post_doubt', kwargs={'session_id': self.session.id}),
            {'question': 'Unauthorized question'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(LiveClassDoubt.objects.filter(student=self.unenrolled_student).exists())

    def test_instructor_answering_doubt(self):
        doubt = LiveClassDoubt.objects.create(session=self.session, student=self.enrolled_student, question='Question test?')
        answer_url = reverse('live_classes:answer_doubt', kwargs={'doubt_id': doubt.id})

        # Student cannot answer
        self.client.login(username='enrolled_stud', password='Password123!')
        res_stud = self.client.post(answer_url, {'answer': 'Student answer'}, follow=True)
        doubt.refresh_from_db()
        self.assertFalse(doubt.is_answered)

        # Host instructor CAN answer
        self.client.login(username='live_teacher', password='Password123!')
        res_inst = self.client.post(answer_url, {'answer': 'Teacher verified answer'}, follow=True)
        doubt.refresh_from_db()
        self.assertTrue(doubt.is_answered)
        self.assertEqual(doubt.answer, 'Teacher verified answer')
