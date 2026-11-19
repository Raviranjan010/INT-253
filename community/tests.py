from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from community.models import DiscussionThread, DiscussionReply
from courses.models import Course, Category

User = get_user_model()

class CommunityForumTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='author_alice',
            email='alice@example.com',
            password='Password123!',
            role='student'
        )
        self.user2 = User.objects.create_user(
            username='helper_bob',
            email='bob@example.com',
            password='Password123!',
            role='student'
        )
        self.thread = DiscussionThread.objects.create(
            title='How does QuickSort pivot selection work?',
            author=self.user1,
            content='Can someone explain median-of-three partitioning?',
            tags='algorithms, python'
        )

    def test_thread_creation_and_xp(self):
        """Creating a discussion thread awards 25 XP once."""
        self.client.login(username='author_alice', password='Password123!')
        response = self.client.post(reverse('community:create_thread'), {
            'title': 'Understanding Big-O Notation',
            'content': 'What is the exact definition of upper bound?',
            'tags': 'theory, math'
        })
        self.assertEqual(response.status_code, 302)
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.xp, 25)

    def test_reply_creation_and_xp(self):
        """Posting a reply awards 15 XP to the author."""
        self.client.login(username='helper_bob', password='Password123!')
        response = self.client.post(
            reverse('community:thread_detail', kwargs={'thread_id': self.thread.id}),
            {'content': 'Median of three chooses the median of first, middle, and last elements.'}
        )
        self.assertEqual(response.status_code, 302)
        self.helper_bob_reply = DiscussionReply.objects.get(thread=self.thread, author=self.user2)
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.xp, 15)

    def test_upvote_post_enforced_and_no_xp_farming(self):
        """Upvoting must be POST-only, awards 5 XP to reply author, and cannot be farmed by toggling."""
        reply = DiscussionReply.objects.create(
            thread=self.thread,
            author=self.user2,
            content='Helpful explanation.'
        )
        # GET should be rejected with 405 Method Not Allowed
        self.client.login(username='author_alice', password='Password123!')
        get_resp = self.client.get(reverse('community:upvote_reply', kwargs={'reply_id': reply.id}))
        self.assertEqual(get_resp.status_code, 405)

        # POST upvotes the reply
        post_resp = self.client.post(reverse('community:upvote_reply', kwargs={'reply_id': reply.id}))
        self.assertEqual(post_resp.status_code, 302)
        self.assertTrue(reply.upvotes.filter(id=self.user1.id).exists())
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.xp, 5)

        # Remove upvote
        self.client.post(reverse('community:upvote_reply', kwargs={'reply_id': reply.id}))
        self.assertFalse(reply.upvotes.filter(id=self.user1.id).exists())

        # Upvote again: XP should NOT increase again
        self.client.post(reverse('community:upvote_reply', kwargs={'reply_id': reply.id}))
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.xp, 5)

    def test_toggle_solution_permissions_and_xp(self):
        """Only thread author can mark solution, POST is enforced, and awards 40 XP once."""
        reply = DiscussionReply.objects.create(
            thread=self.thread,
            author=self.user2,
            content='This is the correct solution.'
        )
        # Random non-author user cannot mark solution
        user3 = User.objects.create_user(
            username='stranger_dan',
            email='dan@example.com',
            password='Password123!'
        )
        self.client.login(username='stranger_dan', password='Password123!')
        post_resp = self.client.post(reverse('community:toggle_solution', kwargs={'reply_id': reply.id}))
        reply.refresh_from_db()
        self.assertFalse(reply.is_solution)

        # GET is rejected with 405
        self.client.login(username='author_alice', password='Password123!')
        get_resp = self.client.get(reverse('community:toggle_solution', kwargs={'reply_id': reply.id}))
        self.assertEqual(get_resp.status_code, 405)

        # Author marks solution via POST
        post_resp2 = self.client.post(reverse('community:toggle_solution', kwargs={'reply_id': reply.id}))
        self.assertEqual(post_resp2.status_code, 302)
        reply.refresh_from_db()
        self.assertTrue(reply.is_solution)
        self.thread.refresh_from_db()
        self.assertTrue(self.thread.is_resolved)

        self.user2.refresh_from_db()
        self.assertEqual(self.user2.xp, 40)

        # Author unmarks and remarks: XP should not be awarded again
        self.client.post(reverse('community:toggle_solution', kwargs={'reply_id': reply.id}))
        self.client.post(reverse('community:toggle_solution', kwargs={'reply_id': reply.id}))
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.xp, 40)
