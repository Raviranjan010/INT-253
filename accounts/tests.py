from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser, XPLedger

class AccountsSecurityAndAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = CustomUser.objects.create_user(
            username='learner1',
            email='learner1@example.com',
            password='Password123!',
            first_name='Learner',
            role='student'
        )
        self.instructor = CustomUser.objects.create_user(
            username='prof1',
            email='prof1@example.com',
            password='Password123!',
            first_name='Professor',
            role='instructor',
            is_instructor_approved=True
        )

    def test_student_registration(self):
        res = self.client.post(reverse('accounts:register'), {
            'username': 'newstudent',
            'email': 'newstudent@example.com',
            'first_name': 'New',
            'last_name': 'Student',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'demographic_group': 'rural',
            'country': 'India',
            'preferred_language': 'English',
        })
        self.assertEqual(res.status_code, 302)
        new_user = CustomUser.objects.get(username='newstudent')
        self.assertEqual(new_user.role, 'student')
        self.assertTrue(new_user.is_student)
        self.assertFalse(new_user.is_instructor)
        # Verify signup bonus in XP ledger
        self.assertTrue(XPLedger.objects.filter(user=new_user, action='signup_bonus').exists())

    def test_instructor_registration_requires_approval(self):
        res = self.client.post(reverse('accounts:register') + '?type=instructor', {
            'username': 'newteacher',
            'email': 'newteacher@example.com',
            'first_name': 'New',
            'last_name': 'Teacher',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'bio': 'Passionate mathematics educator',
            'country': 'India',
        })
        self.assertEqual(res.status_code, 302)
        new_teacher = CustomUser.objects.get(username='newteacher')
        self.assertEqual(new_teacher.role, 'instructor')
        # Crucial security assertion: unapproved instructor must NOT have instructor permissions
        self.assertFalse(new_teacher.is_instructor_approved)
        self.assertFalse(new_teacher.is_instructor)
        self.assertTrue(new_teacher.is_pending_instructor)

    def test_login_and_streak(self):
        res = self.client.post(reverse('accounts:login'), {
            'username': 'learner1',
            'password': 'Password123!',
        })
        self.assertEqual(res.status_code, 302)
        self.student.refresh_from_db()
        self.assertGreaterEqual(self.student.streak_count, 1)

    def test_login_rejects_external_next_redirect(self):
        response = self.client.post(
            reverse('accounts:login') + '?next=https://evil.example/phish',
            {'username': 'learner1', 'password': 'Password123!'},
        )
        self.assertRedirects(
            response,
            reverse('accounts:dashboard_redirect'),
            fetch_redirect_response=False,
        )

    def test_logout_enforces_post(self):
        self.client.login(username='learner1', password='Password123!')
        
        # GET request should render confirmation page, NOT log out
        get_res = self.client.get(reverse('accounts:logout'))
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, 'Sign Out')

        # POST request should execute logout
        post_res = self.client.post(reverse('accounts:logout'))
        self.assertEqual(post_res.status_code, 302)
        # User should now be logged out
        dashboard_res = self.client.get(reverse('accounts:student_dashboard'))
        self.assertEqual(dashboard_res.status_code, 302)

    def test_xp_ledger_prevents_farming(self):
        initial_xp = self.student.xp_points
        # Award XP for first event
        first_attempt = self.student.award_xp('lesson_completed', 'lesson_101', 20)
        self.assertTrue(first_attempt)
        self.student.refresh_from_db()
        self.assertEqual(self.student.xp_points, initial_xp + 20)

        # Attempt to claim XP again for the exact same event
        second_attempt = self.student.award_xp('lesson_completed', 'lesson_101', 20)
        self.assertFalse(second_attempt)
        self.student.refresh_from_db()
        # XP must remain unchanged
        self.assertEqual(self.student.xp_points, initial_xp + 20)
