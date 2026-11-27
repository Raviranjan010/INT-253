from datetime import timedelta

from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from certificates.models import Certificate
from community.models import DiscussionThread, Report
from courses.models import Category, Course
from live_classes.models import LiveSession


class ApplicationWorkflowTests(TestCase):
    def test_instructor_and_learner_workflows(self):
        users = get_user_model().objects
        admin = users.create_superuser(username='operator', email='operator@example.test', password='OperatorPass!4321')
        instructor = Client()
        instructor.post(reverse('accounts:register') + '?type=instructor', {
            'username': 'teacher', 'email': 'teacher@example.test', 'first_name': 'Course', 'last_name': 'Teacher',
            'password1': 'TeacherPass!4321', 'password2': 'TeacherPass!4321',
            'bio': 'Mathematics educator', 'country': 'India',
        })
        owner = users.get(username='teacher')
        create_url = reverse('courses:create_course')
        self.assertRedirects(instructor.get(create_url), reverse('courses:course_list'))
        self.client.force_login(admin)
        self.client.post(reverse('admin:accounts_customuser_changelist'), {
            'action': 'approve_instructors', '_selected_action': [owner.pk],
        })
        owner.refresh_from_db()
        self.assertTrue(owner.is_instructor_approved)
        self.assertTrue(LogEntry.objects.filter(user=admin, object_id=str(owner.pk)).exists())
        self.assertEqual(instructor.get(reverse('accounts:instructor_dashboard')).status_code, 200)
        self.assertEqual(instructor.get(create_url).status_code, 200)
        category = Category.objects.create(name='Mathematics')
        instructor.post(create_url, {
            'title': 'Linear equations', 'category': category.pk, 'level': 'beginner', 'language': 'English',
            'short_description': 'Practice solving equations.', 'description': 'Work with one unknown.',
            'estimated_hours': 1,
        })
        course = Course.objects.get(instructor=owner)
        self.assertFalse(course.is_published)
        instructor.post(reverse('courses:studio_module_new', args=[course.slug]), {'title': 'First steps', 'order': 1})
        module = course.modules.get()
        instructor.post(reverse('courses:studio_lesson_new', args=[course.slug, module.pk]), {
            'title': 'Addition', 'content': 'Subtract the same value from each side.', 'order': 1, 'duration_minutes': 15,
        })
        lesson = module.lessons.get()
        instructor.post(reverse('courses:studio_quiz_new', args=[course.slug]), {
            'title': 'Practice', 'pass_percentage': 70, 'time_limit_minutes': 10, 'max_attempts': 2,
        })
        quiz = course.quizzes.get()
        instructor.post(reverse('courses:studio_question_new', args=[course.slug, quiz.pk]), {
            'text': 'Solve x + 2 = 5', 'order': 1, 'choice_1': '3', 'choice_2': '7', 'correct_choice': 1,
        })
        question = quiz.questions.get()
        instructor.post(reverse('courses:studio_publication', args=[course.slug]))
        course.refresh_from_db()
        self.assertTrue(course.is_published)
        learner = Client()
        learner.post(reverse('accounts:register'), {
            'username': 'learner', 'email': 'learner@example.test', 'first_name': 'Course', 'last_name': 'Learner',
            'password1': 'LearnerPass!4321', 'password2': 'LearnerPass!4321',
            'demographic_group': 'general', 'country': 'India', 'preferred_language': 'English',
        })
        user = users.get(username='learner')
        self.assertEqual(learner.get(reverse('accounts:student_dashboard')).status_code, 200)
        self.assertEqual(learner.get(reverse('accounts:profile')).status_code, 200)
        learner.post(reverse('accounts:profile'), {
            'first_name': 'Returning', 'last_name': 'Learner', 'email': user.email,
            'demographic_group': 'general', 'country': 'India', 'preferred_language': 'English',
        })
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Returning')
        learner.post(reverse('courses:enroll_course', args=[course.slug]))
        learner.post(reverse('courses:toggle_lesson_completion', args=[course.slug, lesson.pk]))
        quiz_url = reverse('quizzes:take_quiz', args=[quiz.pk])
        self.assertEqual(learner.get(quiz_url).status_code, 200)
        learner.post(quiz_url, {f'question_{question.pk}': question.choices.get(is_correct=True).pk})
        self.assertTrue(quiz.attempts.get(student=user).passed)
        certificate = Certificate.objects.get(student=user, course=course)
        result = Client().get(reverse('certificates:verify'), {'id': certificate.certificate_id})
        self.assertTrue(result.context['is_valid'])
        future = timezone.localtime() + timedelta(hours=2)
        instructor.post(reverse('live_classes:schedule_live_class'), {
            'title': 'Office hours', 'course': course.pk, 'scheduled_start': future.strftime('%Y-%m-%dT%H:%M'),
            'duration_minutes': 45, 'description': 'Questions on equations', 'target_demographics': 'Learners',
        })
        session = LiveSession.objects.get(instructor=owner)
        controls = reverse('live_classes:manage_session', args=[session.pk])
        self.assertEqual(learner.post(controls, {'action': 'start'}).status_code, 403)
        instructor.post(controls, {'action': 'start'})
        instructor.post(controls, {'action': 'end'})
        session.refresh_from_db()
        self.assertEqual(session.status, 'completed')

    def test_thread_report_is_idempotent_and_moderators_can_hide_content(self):
        users = get_user_model().objects
        staff = users.create_superuser(username='moderator', email='moderator@example.test', password='ModeratorPass!4321')
        user = users.create_user(username='reporter')
        thread = DiscussionThread.objects.create(title='Reportable thread', content='A post', author=staff)
        url = reverse('community:report_thread', args=[thread.pk])
        self.assertEqual(self.client.post(url, {'reason': 'Review requested'}).status_code, 302)
        self.assertFalse(Report.objects.exists())
        self.client.force_login(user)
        self.assertEqual(self.client.get(url).status_code, 405)
        for _ in range(2):
            self.client.post(url, {'reason': 'Review requested'})
        report = Report.objects.get(reporter=user)
        self.client.force_login(staff)
        self.client.post(reverse('admin:community_report_changelist'), {
            'action': 'hide_reported_content', '_selected_action': [report.pk],
        })
        report.refresh_from_db()
        self.assertIsNotNone(report.resolved_at)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('community:thread_detail', args=[thread.pk])).status_code, 404)
