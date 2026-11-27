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

    def test_quiz_builder_validates_edits_and_protects_attempts(self):
        from quizzes.models import QuizAttempt
        users = get_user_model().objects
        owner = users.create_user(username='owner', role='instructor', is_instructor_approved=True)
        learner = users.create_user(username='learner')
        category = Category.objects.create(name='Mathematics')
        course = Course.objects.create(title='Algebra', category=category, instructor=owner)
        self.client.force_login(owner)
        self.client.post(reverse('courses:studio_quiz_new', args=[course.slug]), {
            'title': 'Linear equations', 'time_limit_minutes': 10, 'pass_percentage': 70, 'max_attempts': 2,
        })
        quiz = course.quizzes.get()
        new_question = reverse('courses:studio_question_new', args=[course.slug, quiz.pk])
        data = {'text': 'Solve 2x = 6', 'order': 1, 'choice_1': '3', 'choice_2': '6', 'correct_choice': 3}
        self.assertContains(self.client.post(new_question, data), 'The correct choice must have text.')
        self.client.post(new_question, {**data, 'correct_choice': 1})
        question = quiz.questions.get()
        self.assertEqual(question.choices.get(is_correct=True).text, '3')
        edit_question = reverse('courses:studio_question_edit', args=[course.slug, quiz.pk, question.pk])
        self.assertContains(self.client.get(edit_question), 'Solve 2x = 6')
        self.client.post(edit_question, {**data, 'text': 'Solve x = 6', 'correct_choice': 2})
        self.assertEqual(question.choices.get(is_correct=True).text, '6')
        QuizAttempt.objects.create(quiz=quiz, student=learner, score_percentage=100, passed=True)
        delete_quiz = reverse('courses:studio_quiz_delete', args=[course.slug, quiz.pk])
        self.assertEqual(self.client.get(delete_quiz).status_code, 405)
        self.client.post(delete_quiz)
        self.assertTrue(course.quizzes.filter(pk=quiz.pk).exists())
        self.client.force_login(learner)
        self.assertEqual(self.client.post(edit_question, data).status_code, 403)
