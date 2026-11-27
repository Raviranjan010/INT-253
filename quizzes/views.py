from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from .models import Quiz, Question, Choice, QuizAttempt
from courses.models import Enrollment

@login_required
@transaction.atomic
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.select_related('course').prefetch_related('questions__choices'), id=quiz_id)
    course = quiz.course

    # 1. Enforce unpublished course permission
    if not course.is_published and not (request.user == course.instructor or request.user.is_staff):
        messages.error(request, "This quiz belongs to a course that is not currently published.")
        return redirect('courses:course_list')

    # 2. Enforce course enrollment
    enrollments = Enrollment.objects.filter(student=request.user, course=course)
    if request.method == 'POST':
        enrollments = enrollments.select_for_update()
    if enrollments.only('id').first() is None:
        messages.error(request, "You must be enrolled in this free course before attempting its quizzes.")
        return redirect('courses:course_detail', slug=course.slug)

    # 3. Enforce maximum attempts
    if quiz.max_attempts > 0:
        prior_attempts = QuizAttempt.objects.filter(quiz=quiz, student=request.user).count()
        if prior_attempts >= quiz.max_attempts:
            messages.warning(
                request, 
                f"You have reached the maximum allowed attempts ({quiz.max_attempts}) for this quiz."
            )
            return redirect('courses:course_detail', slug=course.slug)

    questions = quiz.questions.all()

    if request.method == 'POST':
        # 4. Server-Side Time Limit Enforcement
        start_ts = request.session.pop(f'quiz_start_{quiz.id}', None)
        if not start_ts:
            messages.error(request, "Your quiz session expired or was not started. Please open the quiz and try again.")
            return redirect('quizzes:take_quiz', quiz_id=quiz.id)
        if quiz.time_limit_minutes > 0:
            elapsed_seconds = timezone.now().timestamp() - start_ts
            # Grace period of 60 seconds for slow network latency on submit
            allowed_seconds = (quiz.time_limit_minutes * 60) + 60
            if elapsed_seconds > allowed_seconds:
                QuizAttempt.objects.create(quiz=quiz, student=request.user, score_percentage=0, passed=False)
                elapsed_mins = round(elapsed_seconds / 60, 1)
                messages.error(
                    request, 
                    f"Time limit exceeded! You took {elapsed_mins} minutes (allowed: {quiz.time_limit_minutes} mins). "
                    "This attempt was recorded as unsuccessful."
                )
                return redirect('courses:course_detail', slug=course.slug)

        total_questions = questions.count()
        if total_questions == 0:
            messages.warning(request, "This quiz doesn't have any questions yet.")
            return redirect('courses:course_detail', slug=quiz.course.slug)

        correct_count = 0
        detailed_results = []

        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            selected_choice = None
            is_correct = False

            if selected_choice_id:
                try:
                    selected_choice = Choice.objects.get(id=int(selected_choice_id), question=question)
                    if selected_choice.is_correct:
                        correct_count += 1
                        is_correct = True
                except (Choice.DoesNotExist, ValueError):
                    pass

            correct_choice = question.choices.filter(is_correct=True).first()

            detailed_results.append({
                'question': question,
                'selected_choice': selected_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
                'explanation': question.explanation,
            })

        score_percentage = int((correct_count / total_questions) * 100)
        passed = score_percentage >= quiz.pass_percentage

        # Record attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            score_percentage=score_percentage,
            passed=passed,
        )

        xp_awarded = False
        if passed:
            xp_awarded = request.user.award_xp('quiz_passed', quiz.id, 50)
            msg = f"🎉 Outstanding! You passed with {score_percentage}%!"
            if xp_awarded:
                msg += " (+50 XP)"
            messages.success(request, msg)
        else:
            messages.warning(request, f"You scored {score_percentage}%. Passing score is {quiz.pass_percentage}%. Review answers and try again!")

        context = {
            'quiz': quiz,
            'attempt': attempt,
            'detailed_results': detailed_results,
            'score_percentage': score_percentage,
            'passed': passed,
            'correct_count': correct_count,
            'total_questions': total_questions,
        }
        return render(request, 'quizzes/quiz_result.html', context)

    # On GET, record session start timestamp for server-side time tracking
    key = f'quiz_start_{quiz.id}'
    if key not in request.session:
        request.session[key] = timezone.now().timestamp()

    attempts_used = QuizAttempt.objects.filter(quiz=quiz, student=request.user).count()

    context = {
        'quiz': quiz,
        'questions': questions,
        'attempts_used': attempts_used,
        'attempts_remaining': (quiz.max_attempts - attempts_used) if quiz.max_attempts > 0 else 'Unlimited',
    }
    return render(request, 'quizzes/take_quiz.html', context)
