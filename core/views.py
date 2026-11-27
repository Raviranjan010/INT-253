from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.core import signing
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.db import DatabaseError, connection
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from courses.models import Course, Category
from live_classes.models import LiveSession
from .models import Announcement, NewsletterSubscriber
from .forms import ContactForm, NewsletterForm
from .throttle import rate_limited

def home(request):
    featured_courses = Course.objects.filter(is_published=True).select_related('category', 'instructor')[:6]
    upcoming_live = LiveSession.objects.filter(status__in=['scheduled', 'live']).select_related('course', 'instructor')[:3]
    categories = Category.objects.all()[:8]
    announcements = Announcement.objects.filter(is_active=True)[:2]
    
    from community.models import DiscussionThread
    recent_threads = DiscussionThread.objects.filter(is_hidden=False).select_related('author', 'course')[:3]

    context = {
        'featured_courses': featured_courses,
        'upcoming_live': upcoming_live,
        'categories': categories,
        'announcements': announcements,
        'recent_threads': recent_threads,
    }
    return render(request, 'core/home.html', context)


def about(request):
    return render(request, 'core/about.html')


def demographics_impact(request):
    return render(request, 'core/demographics_impact.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if rate_limited(request, 'contact', 5, 900):
            return HttpResponse('Too many requests. Please try again later.', status=429)
        if request.POST.get('website'):
            return redirect('core:contact')
        if form.is_valid():
            contact_message = form.save()
            if settings.CONTACT_NOTIFICATION_EMAIL:
                send_mail('New LiveSchool contact message',
                          f'Message #{contact_message.pk} is available in Django admin.',
                          settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_NOTIFICATION_EMAIL], fail_silently=True)
            messages.success(request, 'Your message has been received.')
            return redirect('core:contact')
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})


def newsletter_subscribe(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    if rate_limited(request, 'newsletter', 10, 900):
        return HttpResponse('Too many requests. Please try again later.', status=429)
    if request.POST.get('website'):
        return redirect('core:home')

    form = NewsletterForm(request.POST)
    if form.is_valid():
        subscriber = form.save()
        confirm = newsletter_url(request, subscriber, 'confirm')
        unsubscribe = newsletter_url(request, subscriber, 'unsubscribe')
        send_mail('Confirm your LiveSchool subscription',
                  f'Confirm your subscription: {confirm}\n\nRemove this address: {unsubscribe}',
                  settings.DEFAULT_FROM_EMAIL, [subscriber.email], fail_silently=True)
        messages.info(request, 'Check your email to confirm your subscription.')
    else:
        messages.info(request, "This email is already subscribed or invalid.")

    referer = request.META.get('HTTP_REFERER', '')
    if referer and url_has_allowed_host_and_scheme(
        referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(referer)
    return redirect('core:home')


def newsletter_url(request, subscriber, action):
    token = signing.dumps({'id': subscriber.pk, 'email': subscriber.email}, salt=f'newsletter-{action}')
    return request.build_absolute_uri(reverse(f'core:newsletter_{action}', args=[token]))


@require_http_methods(['GET', 'POST'])
def newsletter_manage(request, token, *, action):
    try:
        data = signing.loads(token, salt=f'newsletter-{action}', max_age=172800 if action == 'confirm' else None)
        subscriber = NewsletterSubscriber.objects.get(pk=data['id'], email=data['email'])
    except (signing.BadSignature, NewsletterSubscriber.DoesNotExist):
        return render(request, 'core/newsletter_manage.html', {'invalid': True}, status=400)
    if request.method == 'POST':
        if action == 'confirm':
            NewsletterSubscriber.objects.filter(pk=subscriber.pk, confirmed_at__isnull=True).update(confirmed_at=timezone.now())
            messages.success(request, 'Subscription confirmed.')
        else:
            subscriber.delete()
            messages.success(request, 'You are unsubscribed.')
        return redirect('core:home')
    return render(request, 'core/newsletter_manage.html', {'action': action})


def health_check(request):
    """Check that both Django and its configured database can respond."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except DatabaseError:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})


def robots(request):
    sitemap_url = request.build_absolute_uri(reverse('core:sitemap'))
    return HttpResponse(f'User-agent: *\nDisallow: /admin/\nSitemap: {sitemap_url}\n', content_type='text/plain')


def sitemap(request):
    public_routes = ('core:home', 'core:about', 'core:contact', 'courses:course_list', 'live_classes:live_class_list', 'community:forum_list')
    paths = [reverse(name) for name in public_routes]
    paths.extend(reverse('courses:course_detail', args=[slug]) for slug in
                 Course.objects.filter(is_published=True).values_list('slug', flat=True))
    return render(request, 'core/sitemap.xml',
                  {'locations': [request.build_absolute_uri(path) for path in paths]},
                  content_type='application/xml')
