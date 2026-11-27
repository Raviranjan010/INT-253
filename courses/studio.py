from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST, require_http_methods

from .forms import LessonForm, ModuleForm
from .models import Course
from live_classes.models import LiveClassDoubt
from quizzes.models import QuizAttempt


def owned_course(user, slug):
    course = get_object_or_404(Course, slug=slug)
    if not (user.is_staff or (user.is_instructor and course.instructor_id == user.pk)):
        raise PermissionDenied
    return course


@login_required
def studio(request, slug):
    course = owned_course(request.user, slug)
    enrollments = course.enrollments.select_related('student').order_by('-enrolled_at', '-pk')
    enrollment_stats = enrollments.aggregate(total=Count('pk'), completed=Count('pk', filter=Q(is_completed=True)))
    quiz_stats = QuizAttempt.objects.filter(quiz__course=course).aggregate(
        total=Count('pk'), passed=Count('pk', filter=Q(passed=True)),
    )
    return render(request, 'courses/studio.html', {
        'course': course, 'modules': course.modules.prefetch_related('lessons'),
        'quizzes': course.quizzes.prefetch_related('questions'),
        'page': Paginator(enrollments, 12).get_page(request.GET.get('page')),
        'enrollment_stats': enrollment_stats,
        'quiz_stats': quiz_stats,
        'average_rating': course.reviews.aggregate(average=Avg('rating'))['average'],
        'latest_reviews': course.reviews.select_related('student').order_by('-created_at')[:10],
        'unanswered_doubts': LiveClassDoubt.objects.filter(
            session__course=course, is_answered=False,
        ).select_related('session', 'student')[:10],
    })


@login_required
@require_http_methods(['GET', 'POST'])
def edit_content(request, slug, module_id=None, lesson_id=None, *, kind):
    course = owned_course(request.user, slug)
    module = get_object_or_404(course.modules, pk=module_id) if module_id else None
    lesson = get_object_or_404(module.lessons, pk=lesson_id) if lesson_id else None
    instance = module if kind == 'module' else lesson
    form_type = ModuleForm if kind == 'module' else LessonForm
    form = form_type(request.POST if request.method == 'POST' else None, request.FILES, instance=instance)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        if kind == 'module':
            item.course = course
        else:
            item.module = module
        item.save()
        messages.success(request, f'{kind.capitalize()} saved.')
        return redirect('courses:studio', slug=slug)
    return render(request, 'courses/studio_form.html', {
        'form': form, 'course': course, 'heading': f'{"Edit" if instance else "Add"} {kind}',
    })


@login_required
@require_POST
@transaction.atomic
def change_content(request, slug, action, module_id=None, lesson_id=None):
    course = owned_course(request.user, slug)
    course = Course.objects.select_for_update().get(pk=course.pk)
    if action == 'publication':
        if not course.is_published and not course.modules.filter(lessons__isnull=False).exists():
            messages.error(request, 'Add at least one lesson before publishing.')
        else:
            course.is_published = not course.is_published
            course.save(update_fields=['is_published', 'updated_at'])
    else:
        module = get_object_or_404(course.modules, pk=module_id)
        item = get_object_or_404(module.lessons, pk=lesson_id) if lesson_id else module
        if course.is_published or course.enrollments.exists():
            messages.error(request, 'Content can be deleted only from a draft without enrollments.')
        else:
            item.delete()
            messages.success(request, 'Content deleted.')
    return redirect('courses:studio', slug=slug)
