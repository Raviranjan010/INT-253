from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse


class PasswordFlowTests(TestCase):
    def test_email_login_and_reset(self):
        user = get_user_model().objects.create_user(
            username='Learner', email='Learner@example.test', password='OriginalPass!4932',
        )
        self.assertTrue(self.client.login(username='learner@EXAMPLE.TEST', password='OriginalPass!4932'))
        self.client.logout()
        result = self.client.post(reverse('accounts:password_reset'), {'email': user.email})
        self.assertRedirects(result, reverse('accounts:password_reset_done'))
        url = next(line for line in mail.outbox[0].body.splitlines() if line.startswith('http'))
        confirm = self.client.get(url)
        response = self.client.post(confirm.url, {
            'new_password1': 'ReplacementPass!5932', 'new_password2': 'ReplacementPass!5932',
        })
        self.assertRedirects(response, reverse('accounts:login'))
        self.assertTrue(self.client.login(username='learner', password='ReplacementPass!5932'))

    def test_database_rejects_email_duplicate_case_insensitively(self):
        users = get_user_model().objects
        users.create_user(username='one', email='learner@example.test')
        with self.assertRaises(IntegrityError), transaction.atomic():
            users.create_user(username='two', email='Learner@example.test')
