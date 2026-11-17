import uuid
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course

def generate_cert_id():
    return f"LS-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}"

class Certificate(models.Model):
    certificate_id = models.CharField(max_length=40, unique=True, default=generate_cert_id)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='issued_certificates')
    issued_at = models.DateTimeField(default=timezone.now)
    grade = models.CharField(max_length=50, default='Honors (100% Completion)')
    verification_code = models.CharField(max_length=64, unique=True, blank=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-issued_at']

    def save(self, *args, **kwargs):
        if not self.verification_code:
            raw_hash = f"{self.student_id}:{self.course_id}:{self.issued_at.timestamp()}"
            self.verification_code = hashlib.sha256(raw_hash.encode()).hexdigest()[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.student.username} - {self.course.title}"
