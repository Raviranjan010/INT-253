from django.conf import settings
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject

from accounts.models import CustomUser
from certificates.models import Certificate
from courses.models import Course, Enrollment


def site_metrics() -> dict[str, int]:
    return {
        'students': CustomUser.objects.filter(role='student').count(),
        'courses': Course.objects.filter(is_published=True).count(),
        'countries': CustomUser.objects.exclude(country='').values('country').distinct().count(),
        'enrollments': Enrollment.objects.count(),
        'certificates': Certificate.objects.count(),
    }


def public_stats() -> dict[str, int]:
    if settings.CACHE_GLOBAL_STATS:
        return cache.get_or_set('public-site-metrics-v2', site_metrics, 60)
    return site_metrics()


def global_context(request):
    return {
        'SITE_NAME': 'SKuL',
        'SITE_TAGLINE': 'Next-Gen Open Academy',
        'GLOBAL_STATS': SimpleLazyObject(public_stats),
    }
