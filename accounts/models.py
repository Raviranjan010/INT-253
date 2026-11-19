from django.db import models, transaction, IntegrityError
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student / Learner'),
        ('instructor', 'Teacher / Instructor'),
        ('admin', 'Platform Administrator'),
    )

    DEMOGRAPHIC_CHOICES = (
        ('general', 'General Learner'),
        ('rural', 'Rural / Remote Student'),
        ('low_income', 'Economically Disadvantaged'),
        ('female_stem', 'Women / Girls in STEM'),
        ('homeschool', 'Homeschooling Learner'),
        ('working_adult', 'First-Generation / Working Adult'),
        ('international', 'Global / Developing Nation Student'),
        ('differently_abled', 'Differently Abled / Inclusive Learner'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_instructor_approved = models.BooleanField(
        default=False, 
        help_text='Administrator approval required before instructor can publish courses or host live sessions.'
    )
    demographic_group = models.CharField(
        max_length=30, 
        choices=DEMOGRAPHIC_CHOICES, 
        default='general',
        help_text='Demographic category for personalized accessibility & impact metrics.'
    )
    bio = models.TextField(blank=True, default='')
    country = models.CharField(max_length=100, blank=True, default='India')
    preferred_language = models.CharField(max_length=50, default='English')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    xp_points = models.PositiveIntegerField(default=100, help_text='Gamified Learning Points')
    streak_count = models.PositiveIntegerField(default=1)
    last_active_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_instructor(self):
        return (self.role == 'instructor' and self.is_instructor_approved) or self.is_superuser

    @property
    def is_pending_instructor(self):
        return self.role == 'instructor' and not self.is_instructor_approved and not self.is_superuser

    @property
    def is_platform_admin(self):
        return self.role == 'admin' or self.is_superuser

    @property
    def xp(self):
        return self.xp_points

    def award_xp(self, action, reference_id, amount):
        """
        Atomically and uniquely awards XP. Prevents repeated XP farming.
        Returns True if XP was awarded, False if already claimed.
        """
        try:
            with transaction.atomic():
                XPLedger.objects.create(
                    user=self,
                    action=action,
                    reference_id=str(reference_id),
                    amount=amount
                )
                self.xp_points = models.F('xp_points') + amount
                self.save(update_fields=['xp_points'])
                self.refresh_from_db(fields=['xp_points'])
                return True
        except IntegrityError:
            return False

    def add_xp(self, amount):
        """Direct XP increment for backwards compatibility."""
        self.xp_points = models.F('xp_points') + amount
        self.save(update_fields=['xp_points'])
        self.refresh_from_db(fields=['xp_points'])

    def update_streak(self):
        today = timezone.now().date()
        if self.last_active_date:
            last_date = self.last_active_date.date() if hasattr(self.last_active_date, 'date') else self.last_active_date
            diff = (today - last_date).days
            if diff == 1:
                self.streak_count += 1
            elif diff > 1:
                self.streak_count = 1
        self.last_active_date = today
        self.save(update_fields=['streak_count', 'last_active_date'])


class XPLedger(models.Model):
    ACTION_CHOICES = (
        ('signup_bonus', 'Signup Bonus'),
        ('lesson_completed', 'Lesson Completed'),
        ('quiz_passed', 'Quiz Passed'),
        ('live_attendance', 'Live Class Attendance'),
        ('course_completed', 'Course Completed'),
        ('course_enrolled', 'Course Enrolled'),
        ('review_submitted', 'Course Review Submitted'),
        ('solution_accepted', 'Solution Accepted in Forum'),
        ('reply_upvoted', 'Reply Upvoted in Forum'),
        ('thread_created', 'Discussion Thread Created'),
        ('reply_created', 'Discussion Reply Created'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='xp_records')
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    reference_id = models.CharField(max_length=100, help_text='Unique identifier for the source event')
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'action', 'reference_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} +{self.amount} XP for {self.action} ({self.reference_id})"
