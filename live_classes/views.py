from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.utils import timezone
from django.conf import settings

from .models import LiveSession, SessionAttendee, LiveClassDoubt
from .forms import LiveSessionScheduleForm, DoubtForm
from courses.models import Enrollment

def live_class_list(request):
    now = timezone.now()
    upcoming_sessions = LiveSession.objects.filter(
        status__in=['scheduled', 'live'],
        scheduled_start__gte=now - timezone.timedelta(hours=2)
    ).select_related('course', 'instructor').order_by('scheduled_start')

    past_sessions = LiveSession.objects.filter(
        status='completed'
    ).select_related('course', 'instructor').order_by('-scheduled_start')[:6]

    context = {
        'upcoming_sessions': upcoming_sessions,
        'past_sessions': past_sessions,
    }
    return render(request, 'live_classes/live_class_list.html', context)


@login_required
def live_class_room(request, session_id):
    session = get_object_or_404(LiveSession.objects.select_related('course', 'instructor'), id=session_id)
    is_session_host = (request.user == session.instructor or request.user.is_staff)

    # 1. Enforce enrollment access restriction if session is tied to a specific course
    if session.course and not is_session_host:
        if not Enrollment.objects.filter(student=request.user, course=session.course).exists():
            messages.warning(
                request, 
                f"Course Enrollment Required: You must be enrolled in '{session.course.title}' to join its live synchronous classrooms."
            )
            return redirect('courses:course_detail', slug=session.course.slug)

    # 2. Check session status
    if session.status == 'cancelled':
        messages.error(request, f"This live session ('{session.title}') has been cancelled by the instructor.")
        return redirect('live_classes:live_class_list')

    # 3. Track attendance & prevent XP manipulation (award attendance XP exactly once per session)
    SessionAttendee.objects.get_or_create(session=session, user=request.user)
    request.user.award_xp('live_attendance', session.id, 10)

    # Doubts in this session
    doubts = session.doubts.select_related('student').all()
    doubt_form = DoubtForm()

    context = {
        'session': session,
        'doubts': doubts,
        'doubt_form': doubt_form,
        'jitsi_domain': getattr(settings, 'JITSI_DOMAIN', 'meet.jit.si'),
        'user_display_name': request.user.get_full_name() or request.user.username,
        'is_instructor': is_session_host,
    }
    return render(request, 'live_classes/live_class_room.html', context)


@login_required
def schedule_live_class(request):
    if not (request.user.is_instructor or request.user.is_staff):
        messages.warning(request, "Instructor verification required. Only approved instructors can schedule live classes.")
        return redirect('live_classes:live_class_list')

    if request.method == 'POST':
        form = LiveSessionScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            live_session = form.save(commit=False)
            live_session.instructor = request.user
            live_session.save()
            messages.success(request, f"Live class '{live_session.title}' scheduled successfully!")
            return redirect('live_classes:live_class_list')
    else:
        form = LiveSessionScheduleForm(user=request.user)

    return render(request, 'live_classes/schedule_live_class.html', {'form': form})


@login_required
def post_doubt(request, session_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    session = get_object_or_404(LiveSession, id=session_id)
    is_host = request.user == session.instructor or request.user.is_staff
    if session.course and not is_host and not Enrollment.objects.filter(
        student=request.user, course=session.course
    ).exists():
        messages.error(request, "You must be enrolled in this course to post questions in its live class.")
        return redirect('courses:course_detail', slug=session.course.slug)
    if session.status == 'cancelled':
        messages.error(request, "Questions cannot be posted to a cancelled live class.")
        return redirect('live_classes:live_class_list')
    form = DoubtForm(request.POST)
    if form.is_valid():
        doubt = form.save(commit=False)
        doubt.session = session
        doubt.student = request.user
        doubt.save()
        messages.success(request, "Your doubt has been submitted to the teacher!")
    else:
        messages.error(request, "Unable to post question. Please enter valid question text.")
    return redirect('live_classes:live_class_room', session_id=session.id)


@login_required
def answer_doubt(request, doubt_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    doubt = get_object_or_404(LiveClassDoubt, id=doubt_id)
    if request.user != doubt.session.instructor and not request.user.is_staff:
        messages.error(request, "Unauthorized: Only the host instructor can answer doubts for this session.")
        return redirect('live_classes:live_class_room', session_id=doubt.session.id)

    answer_text = request.POST.get('answer', '').strip()
    if answer_text:
        doubt.answer = answer_text
        doubt.is_answered = True
        doubt.save()
        messages.success(request, "Doubt marked as answered!")
    return redirect('live_classes:live_class_room', session_id=doubt.session.id)
