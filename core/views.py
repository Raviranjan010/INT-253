from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from courses.models import Course, Category
from live_classes.models import LiveSession
from accounts.models import CustomUser
from .models import Announcement
from .forms import ContactForm, NewsletterForm

def home(request):
    featured_courses = Course.objects.filter(is_published=True).select_related('category', 'instructor')[:6]
    upcoming_live = LiveSession.objects.filter(status__in=['scheduled', 'live']).select_related('course', 'instructor')[:3]
    categories = Category.objects.all()[:6]
    announcements = Announcement.objects.filter(is_active=True)[:2]

    context = {
        'featured_courses': featured_courses,
        'upcoming_live': upcoming_live,
        'categories': categories,
        'announcements': announcements,
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
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "You are now subscribed to free educational updates & live webinar alerts!")
        else:
            messages.info(request, "This email is already subscribed or invalid.")
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


def demo_login(request, role):
    """Convenience 1-click login for demonstration in local development. Strictly disabled in production."""
    from django.conf import settings
    if not settings.DEBUG:
        messages.error(request, "Security Violation: 1-Click Demo Login is disabled in production mode.")
        return redirect('accounts:login')

    if role == 'student':
        user = CustomUser.objects.filter(username='student_demo').first()
    elif role == 'instructor':
        user = CustomUser.objects.filter(username='teacher_demo').first()
    elif role == 'admin':
        user = CustomUser.objects.filter(is_superuser=True).first()
    else:
        user = None

    if user:
        login(request, user)
        messages.success(request, f"Logged in as Demo {role.capitalize()} ({user.username})! Note: Available in DEBUG mode only.")
        return redirect('accounts:dashboard_redirect')
    else:
        messages.warning(request, f"Demo {role} account not seeded yet. Run seed data or register.")
        return redirect('accounts:login')
