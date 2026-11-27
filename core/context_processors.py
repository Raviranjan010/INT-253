from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError
from courses.models import Course, Category, Enrollment
from live_classes.models import LiveSession
from accounts.models import CustomUser
from certificates.models import Certificate

def global_context(request):
    """
    Supplies verified database metrics and global navigation context.
    No fabricated user counts or synthetic demographic numbers.
    """
    if settings.CACHE_GLOBAL_STATS:
        return cache.get_or_set('public-site-metrics-v1', site_metrics, 60)
    return site_metrics()


def site_metrics():
    try:
        categories = list(Category.objects.all()[:8])
        upcoming_live_count = LiveSession.objects.filter(status__in=['scheduled', 'live']).count()
        total_courses_count = Course.objects.filter(is_published=True).count()
        total_students_count = CustomUser.objects.filter(role='student').count()
        total_countries_count = CustomUser.objects.exclude(country='').exclude(country__isnull=True).values('country').distinct().count()
        total_enrollments_count = Enrollment.objects.count()
        total_certificates_count = Certificate.objects.count()
    except DatabaseError:
        categories = []
        upcoming_live_count = 0
        total_courses_count = 0
        total_students_count = 0
        total_countries_count = 0
        total_enrollments_count = 0
        total_certificates_count = 0

    return {
        'SITE_NAME': 'Live School',
        'SITE_TAGLINE': 'World-Class Free Education for Every Demographic',
        'PROBLEM_STATEMENT': 'Creation of an online platform providing free access to world-class education for students across various demographics.',
        'NAV_CATEGORIES': categories,
        'UPCOMING_LIVE_COUNT': upcoming_live_count,
        'GLOBAL_STATS': {
            'students': total_students_count,
            'courses': total_courses_count,
            'countries': total_countries_count,
            'enrollments': total_enrollments_count,
            'certificates': total_certificates_count,
        }
    }
