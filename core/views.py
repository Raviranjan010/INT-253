from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from django.db import DatabaseError, connection
from django.utils.http import url_has_allowed_host_and_scheme
from courses.models import Course, Category
from live_classes.models import LiveSession
from .models import Announcement
from .forms import ContactForm, NewsletterForm

def home(request):
    featured_courses = Course.objects.filter(is_published=True).select_related('category', 'instructor')[:6]
    upcoming_live = LiveSession.objects.filter(status__in=['scheduled', 'live']).select_related('course', 'instructor')[:3]
    categories = Category.objects.all()[:8]
    announcements = Announcement.objects.filter(is_active=True)[:2]
    
    from community.models import DiscussionThread
    recent_threads = DiscussionThread.objects.select_related('author', 'course').prefetch_related('replies')[:3]

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
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you! Your message has been received. Our team will get back to you shortly.")
            return redirect('core:contact')
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})


def newsletter_subscribe(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    form = NewsletterForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "You are now subscribed to free educational updates & live webinar alerts!")
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


def health_check(request):
    """Check that both Django and its configured database can respond."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except DatabaseError:
        return JsonResponse({'status': 'unavailable'}, status=503)
    return JsonResponse({'status': 'ok'})
