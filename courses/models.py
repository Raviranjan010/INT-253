from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=50, default='bi-journal-bookmark', help_text='Bootstrap Icon class')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Course(models.Model):
    LEVEL_CHOICES = (
        ('all', 'All Levels'),
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses')
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses_teaching',
        limit_choices_to={'role__in': ['instructor', 'admin']}
    )
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='all')
    language = models.CharField(max_length=50, default='English')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    estimated_hours = models.PositiveIntegerField(default=8)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    @property
    def total_lessons(self):
        return Lesson.objects.filter(module__course=self).count()

    @property
    def total_duration_minutes(self):
        lessons = Lesson.objects.filter(module__course=self)
        return sum(l.duration_minutes for l in lessons)

    @property
    def enrollment_count(self):
        return self.enrollments.count()

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 5.0  # default free high quality baseline


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.course.title} - Module {self.order}: {self.title}"


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)
    content = models.TextField(help_text='Educational notes, explanations, code snippets, or reading material.')
    video_url = models.URLField(blank=True, help_text='YouTube Embed or Video URL for free lecture playback.')
    duration_minutes = models.PositiveIntegerField(default=15)
    resource_file = models.FileField(upload_to='lesson_resources/', blank=True, null=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.module.title} - Lesson {self.order}: {self.title}"

    @property
    def embed_video_url(self):
        """Converts standard YouTube watch URLs to embed URLs"""
        url = self.video_url
        if not url:
            return ""
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('watch?v=')[1].split('&')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            return f"https://www.youtube.com/embed/{video_id}"
        return url


class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress_percentage = models.PositiveIntegerField(default=0)
    last_accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-last_accessed_at']

    def __str__(self):
        return f"{self.student.username} -> {self.course.title} ({self.progress_percentage}%)"

    def recalculate_progress(self):
        total_lessons = self.course.total_lessons
        if total_lessons == 0:
            self.progress_percentage = 100
            self.is_completed = True
            self.completed_at = timezone.now()
        else:
            completed_count = self.lesson_progresses.filter(is_completed=True).count()
            self.progress_percentage = int((completed_count / total_lessons) * 100)
            if self.progress_percentage >= 100:
                self.progress_percentage = 100
                if not self.is_completed:
                    self.is_completed = True
                    self.completed_at = timezone.now()
            else:
                self.is_completed = False
                self.completed_at = None
        self.save(update_fields=['progress_percentage', 'is_completed', 'completed_at', 'last_accessed_at'])
        return self.progress_percentage


class LessonProgress(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lesson_progresses')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress_records')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('enrollment', 'lesson')

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.lesson.title} - {'Done' if self.is_completed else 'Pending'}"


class CourseReview(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} Stars") for i in range(1, 6)], default=5)
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('course', 'student')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} on {self.course.title} ({self.rating} stars)"
