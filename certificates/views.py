from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from .models import Certificate

def view_certificate(request, certificate_id):
    cert = get_object_or_404(
        Certificate.objects.select_related('student', 'course', 'course__instructor'),
        certificate_id=certificate_id
    )
    context = {
        'certificate': cert,
    }
    return render(request, 'certificates/view_certificate.html', context)


def verify_certificate(request, certificate_id=None):
    cert_code = certificate_id or request.GET.get('id', '').strip()
    cert = None
    searched = bool(cert_code)
    is_valid = False

    if cert_code:
        cert = Certificate.objects.filter(certificate_id__iexact=cert_code).select_related('student', 'course').first()
        if not cert:
            # Check by verification hash
            cert = Certificate.objects.filter(verification_code__iexact=cert_code).select_related('student', 'course').first()
        is_valid = cert is not None

    context = {
        'certificate': cert,
        'cert_code': cert_code,
        'searched': searched,
        'is_valid': is_valid,
    }
    return render(request, 'certificates/verify_certificate.html', context)
