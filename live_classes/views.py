from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from .models import LiveSession, SessionAttendee, LiveClassDoubt
from .forms import LiveSessionScheduleForm, DoubtForm

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
    
    # Track attendance
    SessionAttendee.objects.get_or_create(session=session, user=request.user)
    request.user.add_xp(10)

    # Doubts in this session
    doubts = session.doubts.select_related('student').all()
    doubt_form = DoubtForm()

    context = {
        'session': session,
        'doubts': doubts,
        'doubt_form': doubt_form,
        'jitsi_domain': getattr(settings, 'JITSI_DOMAIN', 'meet.jit.si'),
        'user_display_name': request.user.get_full_name() or request.user.username,
        'is_instructor': (request.user == session.instructor or request.user.is_staff),
    }
    return render(request, 'live_classes/live_class_room.html', context)


@login_required
def schedule_live_class(request):
    if not (request.user.is_instructor or request.user.is_staff):
        messages.warning(request, "Only verified instructors can schedule live classes.")
        return redirect('live_classes:live_class_list')

    if request.method == 'POST':
        form = LiveSessionScheduleForm(request.POST)
        if form.is_valid():
            live_session = form.save(commit=False)
            live_session.instructor = request.user
            live_session.save()
            messages.success(request, f"Live class '{live_session.title}' scheduled successfully!")
            return redirect('live_classes:live_class_list')
    else:
        form = LiveSessionScheduleForm()

    return render(request, 'live_classes/schedule_live_class.html', {'form': form})


@login_required
def post_doubt(request, session_id):
    session = get_object_or_404(LiveSession, id=session_id)
    if request.method == 'POST':
        form = DoubtForm(request.POST)
        if form.is_valid():
            doubt = form.save(commit=False)
            doubt.session = session
            doubt.student = request.user
            doubt.save()
            messages.success(request, "Your doubt has been submitted to the teacher!")
    return redirect('live_classes:live_class_room', session_id=session.id)


@login_required
def answer_doubt(request, doubt_id):
    doubt = get_object_or_404(LiveClassDoubt, id=doubt_id)
    if request.user != doubt.session.instructor and not request.user.is_staff:
        messages.error(request, "Unauthorized to answer doubts for this session.")
        return redirect('live_classes:live_class_room', session_id=doubt.session.id)

    if request.method == 'POST':
        answer_text = request.POST.get('answer', '').strip()
        if answer_text:
            doubt.answer = answer_text
            doubt.is_answered = True
            doubt.save()
            messages.success(request, "Doubt marked as answered!")
    return redirect('live_classes:live_class_room', session_id=doubt.session.id)
