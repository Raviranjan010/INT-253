import uuid
import hashlib
import hmac
from django.db import models
from django.conf import settings
from django.utils import timezone
from courses.models import Course

def generate_cert_id():
    return f"LS-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}"

def compute_digital_signature(student_id, course_id, certificate_id, timestamp_str):
    secret = settings.SECRET_KEY.encode('utf-8')
    payload = f"{student_id}:{course_id}:{certificate_id}:{timestamp_str}".encode('utf-8')
    return hmac.new(secret, payload, hashlib.sha256).hexdigest()

class Certificate(models.Model):
    certificate_id = models.CharField(max_length=40, unique=True, default=generate_cert_id)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='issued_certificates')
    issued_at = models.DateTimeField(default=timezone.now)
    grade = models.CharField(max_length=50, default='Honors (100% Completion)')
    verification_code = models.CharField(max_length=64, unique=True, blank=True)
    digital_signature = models.CharField(max_length=64, blank=True, help_text='Server HMAC-SHA256 signature for tamper detection')

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-issued_at']

    def save(self, *args, **kwargs):
        if not self.verification_code:
            raw_hash = f"{self.student_id}:{self.course_id}:{self.certificate_id}"
            self.verification_code = hashlib.sha256(raw_hash.encode()).hexdigest()[:16].upper()
        
        # Calculate genuine HMAC-SHA256 digital signature
        time_str = self.issued_at.strftime('%Y-%m-%d %H:%M:%S') if self.issued_at else timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        self.digital_signature = compute_digital_signature(
            self.student_id, self.course_id, self.certificate_id, time_str
        )
        super().save(*args, **kwargs)

    def verify_signature(self):
        """
        Cryptographically validates that this certificate record matches the server's HMAC signature
        and has not been tampered with or altered directly in the database.
        """
        time_str = self.issued_at.strftime('%Y-%m-%d %H:%M:%S')
        expected = compute_digital_signature(self.student_id, self.course_id, self.certificate_id, time_str)
        return hmac.compare_digest(self.digital_signature, expected)

    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.student.username} - {self.course.title}"
