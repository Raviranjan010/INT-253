import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course

class LiveSession(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now 🔴'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_sessions')
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='live_sessions_hosted',
        limit_choices_to={'role__in': ['instructor', 'admin']}
    )
    description = models.TextField()
    scheduled_start = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    room_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    target_demographics = models.CharField(max_length=150, default='All Demographics & Remote Students')
    recording_url = models.URLField(blank=True, null=True, help_text='Link to session recording for offline/rural students')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_start']

    def save(self, *args, **kwargs):
        if not self.room_name:
            self.room_name = f"liveschool-{str(self.id)[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.instructor.get_full_name() or self.instructor.username}"

    @property
    def is_live_now(self):
        if self.status == 'live':
            return True
        now = timezone.now()
        end_time = self.scheduled_start + timezone.timedelta(minutes=self.duration_minutes)
        return self.scheduled_start <= now <= end_time and self.status != 'completed'

    @property
    def attendee_count(self):
        return self.attendees.count()


class SessionAttendee(models.Model):
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attended_sessions')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'user')

    def __str__(self):
        return f"{self.user.username} attended {self.session.title}"


class LiveClassDoubt(models.Model):
    session = models.ForeignKey(LiveSession, on_delete=models.CASCADE, related_name='doubts')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.TextField()
    is_answered = models.BooleanField(default=False)
    answer = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Doubt by {self.student.username} in {self.session.title}"
