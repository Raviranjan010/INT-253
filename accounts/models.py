from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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
        return self.role == 'instructor'

    @property
    def is_platform_admin(self):
        return self.role == 'admin' or self.is_superuser

    def add_xp(self, amount):
        self.xp_points += amount
        self.save(update_fields=['xp_points'])

    def update_streak(self):
        today = timezone.now().date()
        if self.last_active_date:
            diff = (today - self.last_active_date).days
            if diff == 1:
                self.streak_count += 1
            elif diff > 1:
                self.streak_count = 1
        self.last_active_date = today
        self.save(update_fields=['streak_count', 'last_active_date'])
