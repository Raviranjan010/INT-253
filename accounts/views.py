from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .forms import StudentRegistrationForm, InstructorRegistrationForm, UserProfileForm, CustomLoginForm
from .models import CustomUser
from courses.models import Enrollment, Course
from live_classes.models import LiveSession
from quizzes.models import QuizAttempt
from certificates.models import Certificate
from core.throttle import rate_limited

def register_view(request):
    account_type = request.GET.get('type', 'student')
    
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        if rate_limited(request, 'registration', 8, 900):
            return HttpResponse('Too many registrations. Please try again later.', status=429)
        if request.POST.get('website'):
            return redirect('accounts:register')
        if account_type == 'instructor':
            form = InstructorRegistrationForm(request.POST)
        else:
            form = StudentRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            if account_type == 'instructor':
                user.role = 'instructor'
                user.is_instructor_approved = False
            else:
                user.role = 'student'
            user.save()
            login(request, user)
            user.update_streak()
            user.award_xp('signup_bonus', f'user_{user.id}', 100)
            
            if account_type == 'instructor':
                messages.info(
                    request, 
                    f"Welcome to Live School, {user.first_name}! Your instructor registration is pending administrator review. "
                    "You can enroll in and explore all courses as a student while approval is pending."
                )
            else:
                messages.success(request, f"Welcome to Live School, {user.first_name}! You've been awarded +100 XP points for joining.")
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, "Please correct the errors below to complete registration.")
    else:
        if account_type == 'instructor':
            form = InstructorRegistrationForm()
        else:
            form = StudentRegistrationForm()

    return render(request, 'accounts/register.html', {
        'form': form,
        'account_type': account_type
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        if rate_limited(request, 'login', 15, 600):
            return HttpResponse('Too many sign-in requests. Please try again later.', status=429)
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            user.update_streak()
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password. Please check your credentials.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Enforces POST for secure logout to prevent cross-site logout request attacks."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out safely.")
        return redirect('core:home')
    return render(request, 'accounts/logout_confirm.html')


@login_required
def dashboard_redirect(request):
    if request.user.is_instructor:
        return redirect('accounts:instructor_dashboard')
    elif request.user.is_platform_admin and request.user.is_staff:
        # If staff/admin wants admin panel or dashboard
        if request.GET.get('panel') == 'admin':
            return redirect('admin:index')
        return redirect('accounts:student_dashboard')
    else:
        return redirect('accounts:student_dashboard')


@login_required
def student_dashboard(request):
    user = request.user
    user.update_streak()

    enrollments = Enrollment.objects.filter(student=user).select_related('course', 'course__category')
    completed_courses_count = enrollments.filter(is_completed=True).count()
    in_progress_count = enrollments.filter(is_completed=False).count()
    
    # Upcoming live classes relevant to enrolled courses or general
    upcoming_live = LiveSession.objects.filter(
        Q(course__isnull=True) | Q(course_id__in=enrollments.values('course_id')),
        Q(status='live') | Q(status='scheduled', scheduled_start__gte=timezone.now()),
    ).order_by('scheduled_start')[:4]

    # Recent quiz attempts
    recent_quizzes = QuizAttempt.objects.filter(student=user).select_related('quiz', 'quiz__course')[:5]

    # Certificates earned
    certificates = Certificate.objects.filter(student=user).select_related('course')

    context = {
        'enrollments': enrollments,
        'completed_courses_count': completed_courses_count,
        'in_progress_count': in_progress_count,
        'upcoming_live': upcoming_live,
        'recent_quizzes': recent_quizzes,
        'certificates': certificates,
    }
    return render(request, 'accounts/student_dashboard.html', context)


@login_required
def instructor_dashboard(request):
    if not (request.user.is_instructor or request.user.is_staff):
        messages.warning(request, "Only instructors have access to the Instructor Hub.")
        return redirect('accounts:student_dashboard')

    user = request.user
    courses = Course.objects.filter(instructor=user).annotate(
        enrollment_total=Count('enrollments'),
    ).order_by('-created_at', '-pk')
    live_sessions = LiveSession.objects.filter(instructor=user).order_by('-scheduled_start', '-pk')
    
    # Compute totals
    total_students = Enrollment.objects.filter(course__instructor=user).values('student').distinct().count()

    context = {
        'courses': Paginator(courses, 12).get_page(request.GET.get('courses_page')),
        'live_sessions': Paginator(live_sessions, 12).get_page(request.GET.get('live_page')),
        'total_students': total_students,
    }
    return render(request, 'accounts/instructor_dashboard.html', context)


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'accounts/profile.html', {'form': form})
