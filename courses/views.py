from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseNotAllowed
from django.db.models import Q, Avg, Count, F
from django.utils import timezone
from django.core.paginator import Paginator

from .models import Course, Category, Module, Lesson, Enrollment, LessonProgress, CourseReview
from .forms import CourseReviewForm, CourseCreateForm, LessonForm
from certificates.models import Certificate

def course_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '')
    level = request.GET.get('level', '')
    sort = request.GET.get('sort', 'newest')

    courses = Course.objects.filter(is_published=True).select_related('category', 'instructor')

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(category__name__icontains=query)
        )

    if category_slug:
        courses = courses.filter(category__slug=category_slug)

    if level and level != 'all':
        courses = courses.filter(level=level)

    courses = courses.annotate(avg_rating=Avg('reviews__rating'), lesson_total=Count('modules__lessons', distinct=True))
    if sort == 'rating':
        courses = courses.order_by(F('avg_rating').desc(nulls_last=True), '-created_at', '-pk')
    else:
        courses = courses.order_by('-created_at', '-pk')

    categories = Category.objects.all()
    page = Paginator(courses, 12).get_page(request.GET.get('page'))

    context = {
        'courses': page.object_list,
        'page': page,
        'categories': categories,
        'selected_category': category_slug,
        'selected_level': level,
        'selected_sort': sort,
        'query': query,
    }
    return render(request, 'courses/course_list.html', context)


def course_detail(request, slug):
    course = get_object_or_404(Course.objects.select_related('category', 'instructor'), slug=slug)
    
    # Access permission for unpublished courses
    if not course.is_published:
        if not (request.user.is_authenticated and (request.user == course.instructor or request.user.is_staff)):
            messages.error(request, "This course is currently in draft mode and not publicly available.")
            return redirect('courses:course_list')

    modules = course.modules.prefetch_related('lessons').all()
    reviews = course.reviews.select_related('student').all()
    
    is_enrolled = False
    user_enrollment = None
    if request.user.is_authenticated:
        user_enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        is_enrolled = user_enrollment is not None

    review_form = CourseReviewForm()

    context = {
        'course': course,
        'modules': modules,
        'reviews': reviews,
        'is_enrolled': is_enrolled,
        'enrollment': user_enrollment,
        'review_form': review_form,
    }
    return render(request, 'courses/course_detail.html', context)


@login_required
def enroll_course(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)

    # Enforce POST for state-changing enrollment
    if request.method != 'POST':
        messages.info(request, "Please click 'Enroll Free in 1-Click' on the course overview to confirm enrollment.")
        return redirect('courses:course_detail', slug=course.slug)

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    if created:
        request.user.award_xp('course_enrolled', course.id, 50)
        messages.success(request, f"🎉 You've successfully enrolled for free in '{course.title}'! +50 XP awarded.")
    else:
        messages.info(request, f"Welcome back to '{course.title}'!")

    first_lesson = Lesson.objects.filter(module__course=course).order_by('module__order', 'order').first()
    if first_lesson:
        return redirect('courses:lesson_player', course_slug=course.slug, lesson_id=first_lesson.id)
    return redirect('courses:course_detail', slug=course.slug)


@login_required
def lesson_player(request, course_slug, lesson_id):
    course = get_object_or_404(Course, slug=course_slug)
    
    # Unpublished check
    if not course.is_published and not (request.user == course.instructor or request.user.is_staff):
        messages.error(request, "This course is not currently available.")
        return redirect('courses:course_list')

    # Must be enrolled
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)

    modules = course.modules.prefetch_related('lessons').all()

    completed_lesson_ids = set(
        enrollment.lesson_progresses.filter(is_completed=True).values_list('lesson_id', flat=True)
    )

    all_lessons = list(Lesson.objects.filter(module__course=course).order_by('module__order', 'order'))
    current_index = -1
    for idx, l in enumerate(all_lessons):
        if l.id == lesson.id:
            current_index = idx
            break

    prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None

    is_current_completed = lesson.id in completed_lesson_ids
    course_quizzes = course.quizzes.all()

    context = {
        'course': course,
        'lesson': lesson,
        'enrollment': enrollment,
        'modules': modules,
        'completed_lesson_ids': completed_lesson_ids,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'is_current_completed': is_current_completed,
        'course_quizzes': course_quizzes,
    }
    return render(request, 'courses/lesson_player.html', context)


@login_required
def toggle_lesson_completion(request, course_slug, lesson_id):
    # Enforce POST only
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    course = get_object_or_404(Course, slug=course_slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)

    progress, created = LessonProgress.objects.get_or_create(
        enrollment=enrollment,
        lesson=lesson
    )

    # Toggle completion status
    progress.is_completed = not progress.is_completed
    progress.completed_at = timezone.now() if progress.is_completed else None
    progress.save()

    # Recalculate progress percentage
    new_progress = enrollment.recalculate_progress()

    # Unique XP award via ledger (prevents repeated farming)
    xp_awarded = False
    if progress.is_completed:
        xp_awarded = request.user.award_xp('lesson_completed', lesson.id, 20)

    # Verify course completion before issuing certificate
    cert_created = False
    if enrollment.is_completed:
        total_course_lessons = Lesson.objects.filter(module__course=course).count()
        completed_lessons_count = LessonProgress.objects.filter(enrollment=enrollment, is_completed=True).count()
        
        # Rigorous completion check
        if completed_lessons_count >= total_course_lessons and total_course_lessons > 0:
            cert, created_cert = Certificate.objects.get_or_create(
                student=request.user,
                course=course,
                defaults={'grade': 'World-Class Scholar (100% Course Mastery)'}
            )
            if created_cert:
                request.user.award_xp('course_completed', course.id, 200)
                cert_created = True

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'is_completed': progress.is_completed,
            'progress_percentage': new_progress,
            'cert_created': cert_created,
            'xp_awarded': xp_awarded,
        })

    if progress.is_completed:
        msg = "✓ Lesson marked complete!"
        if xp_awarded:
            msg += " (+20 XP)"
        messages.success(request, msg)
        if cert_created:
            messages.success(request, "🏆 Congratulations! You've completed 100% of the course and earned your Verified Certificate of Completion! (+200 XP)")
    else:
        messages.info(request, "Lesson status updated to incomplete.")

    next_lesson_id = request.POST.get('next_lesson_id')
    if next_lesson_id:
        return redirect('courses:lesson_player', course_slug=course.slug, lesson_id=next_lesson_id)
    return redirect('courses:lesson_player', course_slug=course.slug, lesson_id=lesson.id)


@login_required
def add_review(request, slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    course = get_object_or_404(Course, slug=slug)
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        messages.error(request, "You must be enrolled in this free course to submit a review.")
        return redirect('courses:course_detail', slug=course.slug)

    form = CourseReviewForm(request.POST)
    if form.is_valid():
        review, created = CourseReview.objects.update_or_create(
            course=course,
            student=request.user,
            defaults={
                'rating': form.cleaned_data['rating'],
                'review_text': form.cleaned_data['review_text']
            }
        )
        # Prevent review XP farming
        request.user.award_xp('review_submitted', course.id, 15)
        messages.success(request, "Thank you for your valuable feedback! +15 XP awarded.")
    else:
        messages.error(request, "Unable to save review. Please check the form.")

    return redirect('courses:course_detail', slug=course.slug)


@login_required
def create_course(request):
    if not (request.user.is_instructor or request.user.is_staff):
        messages.warning(request, "Instructor verification required. Only approved instructors can publish courses.")
        return redirect('courses:course_list')

    if request.method == 'POST':
        form = CourseCreateForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.is_published = False
            course.save()
            messages.success(request, f"Course '{course.title}' created successfully! Now add modules and lessons.")
            return redirect('courses:studio', slug=course.slug)
    else:
        form = CourseCreateForm()

    return render(request, 'courses/course_form.html', {'form': form, 'is_edit': False})


@login_required
def edit_course(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if not (request.user.is_staff or (request.user.is_instructor and request.user == course.instructor)):
        messages.error(request, "You are not authorized to edit this course.")
        return redirect('courses:course_detail', slug=course.slug)

    if request.method == 'POST':
        form = CourseCreateForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f"Course '{course.title}' updated successfully.")
            return redirect('courses:course_detail', slug=course.slug)
    else:
        form = CourseCreateForm(instance=course)

    return render(request, 'courses/course_form.html', {'form': form, 'course': course, 'is_edit': True})


@login_required
def delete_course(request, slug):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    course = get_object_or_404(Course, slug=slug)
    if not (request.user.is_staff or (request.user.is_instructor and request.user == course.instructor)):
        messages.error(request, "You are not authorized to delete this course.")
        return redirect('courses:course_detail', slug=course.slug)

    course_title = course.title
    if course.enrollments.exists() or course.issued_certificates.exists():
        messages.error(request, 'This course has learning records. Unpublish it in the course studio instead.')
        return redirect('courses:studio', slug=slug)
    course.delete()
    messages.success(request, f"Course '{course_title}' has been deleted.")
    return redirect('accounts:instructor_dashboard')
