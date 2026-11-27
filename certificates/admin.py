from django.contrib import admin
from .models import Certificate

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_id', 'student', 'course', 'issued_at', 'grade')
    list_filter = ('issued_at', 'course')
    search_fields = ('certificate_id', 'student__username', 'course__title', 'verification_code')
    readonly_fields = ('certificate_id', 'verification_code', 'digital_signature')
    list_select_related = ('student', 'course')
