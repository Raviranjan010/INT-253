from django.db import models
from django.conf import settings
from courses.models import Course

class DiscussionThread(models.Model):
    title = models.CharField(max_length=250)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='discussions')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='threads')
    content = models.TextField()
    tags = models.CharField(max_length=150, blank=True, help_text='Comma separated tags (e.g. python, calculus, doubt)')
    is_resolved = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def replies_count(self):
        return self.replies.count()


class DiscussionReply(models.Model):
    thread = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    is_solution = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    upvotes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='upvoted_replies', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_solution', 'created_at']

    def __str__(self):
        return f"Reply by {self.author.username} on {self.thread.title}"

    @property
    def upvote_count(self):
        return self.upvotes.count()


class Report(models.Model):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thread = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='reports')
    reply = models.ForeignKey(DiscussionReply, on_delete=models.CASCADE, blank=True, null=True)
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('reporter', 'thread'), condition=models.Q(reply__isnull=True), name='one_thread_report_per_user'),
            models.UniqueConstraint(fields=('reporter', 'reply'), condition=models.Q(reply__isnull=False), name='one_reply_report_per_user'),
        ]
