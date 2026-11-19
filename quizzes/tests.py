from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from courses.models import Course, Category, Enrollment
from quizzes.models import Quiz, Question, Choice, QuizAttempt

User = get_user_model()

class QuizSecurityAndValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.instructor = User.objects.create_user(
            username='quiz_inst',
            email='quiz_inst@example.com',
            password='Password123!',
            role='instructor',
            is_instructor_approved=True
        )
        self.student = User.objects.create_user(
            username='quiz_student',
            email='quiz_student@example.com',
            password='Password123!',
            role='student'
        )
        self.category = Category.objects.create(name='Tech', slug='tech')
        self.course = Course.objects.create(
            title='Intro to Algorithms',
            slug='intro-to-algorithms',
            instructor=self.instructor,
            category=self.category,
            is_published=True
        )
        self.quiz = Quiz.objects.create(
            course=self.course,
            title='Sorting Quiz',
            pass_percentage=70,
            time_limit_minutes=5,
            max_attempts=2
        )
        self.question = Question.objects.create(
            quiz=self.quiz,
            text='What is the best case time complexity of Merge Sort?',
            order=1
        )
        self.choice_correct = Choice.objects.create(
            question=self.question,
            text='O(n log n)',
            is_correct=True
        )
        self.choice_wrong = Choice.objects.create(
            question=self.question,
            text='O(n^2)',
            is_correct=False
        )

    def test_unenrolled_student_blocked_from_quiz(self):
        """Unenrolled student should be redirected to course detail page."""
        self.client.login(username='quiz_student', password='Password123!')
        response = self.client.get(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}))
        self.assertRedirects(response, reverse('courses:course_detail', kwargs={'slug': self.course.slug}))

    def test_unpublished_course_quiz_blocked_for_normal_users(self):
        """Quiz on unpublished course cannot be accessed by general students."""
        self.course.is_published = False
        self.course.save()
        Enrollment.objects.create(student=self.student, course=self.course)

        self.client.login(username='quiz_student', password='Password123!')
        response = self.client.get(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}))
        self.assertRedirects(response, reverse('courses:course_list'))

        # Instructor can access even when unpublished
        self.client.login(username='quiz_inst', password='Password123!')
        Enrollment.objects.create(student=self.instructor, course=self.course)
        resp_inst = self.client.get(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}))
        self.assertEqual(resp_inst.status_code, 200)

    def test_choice_single_correct_validation(self):
        """A question cannot have more than one correct choice."""
        duplicate_correct = Choice(
            question=self.question,
            text='Another correct choice',
            is_correct=True
        )
        with self.assertRaises(ValidationError):
            duplicate_correct.save()

    def test_quiz_attempt_limit_enforced(self):
        """Students cannot take a quiz more than max_attempts times."""
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='quiz_student', password='Password123!')

        # Create 2 prior attempts (max_attempts = 2)
        QuizAttempt.objects.create(quiz=self.quiz, student=self.student, score_percentage=50, passed=False)
        QuizAttempt.objects.create(quiz=self.quiz, student=self.student, score_percentage=60, passed=False)

        response = self.client.get(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}))
        self.assertRedirects(response, reverse('courses:course_detail', kwargs={'slug': self.course.slug}))

    def test_quiz_successful_completion_and_xp_award(self):
        """Passing the quiz awards 50 XP, and repeated pass does not farm XP."""
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='quiz_student', password='Password123!')
        initial_xp = self.student.xp

        # Initial GET to initialize session start timestamp
        self.client.get(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}))

        post_data = {
            f'question_{self.question.id}': self.choice_correct.id
        }
        response = self.client.post(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}), post_data)
        self.assertEqual(response.status_code, 200)

        self.student.refresh_from_db()
        self.assertEqual(self.student.xp, initial_xp + 50)
        self.assertEqual(QuizAttempt.objects.filter(student=self.student, passed=True).count(), 1)

        # Second attempt (allowed because max_attempts=2)
        self.client.get(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}))
        response2 = self.client.post(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}), post_data)
        self.assertEqual(response2.status_code, 200)

        # XP should NOT increase again
        self.student.refresh_from_db()
        self.assertEqual(self.student.xp, initial_xp + 50)

    def test_quiz_time_limit_enforced(self):
        """Submitting past the allowed time limit rejects the attempt."""
        Enrollment.objects.create(student=self.student, course=self.course)
        self.client.login(username='quiz_student', password='Password123!')

        # Set session start timestamp to 10 minutes ago (time limit is 5 mins + 1 min grace)
        session = self.client.session
        session[f'quiz_start_{self.quiz.id}'] = timezone.now().timestamp() - 600
        session.save()

        post_data = {
            f'question_{self.question.id}': self.choice_correct.id
        }
        response = self.client.post(reverse('quizzes:take_quiz', kwargs={'quiz_id': self.quiz.id}), post_data)
        self.assertRedirects(response, reverse('courses:course_detail', kwargs={'slug': self.course.slug}))
        self.assertEqual(QuizAttempt.objects.filter(student=self.student).count(), 0)
