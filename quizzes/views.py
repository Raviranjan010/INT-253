from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Quiz, Question, Choice, QuizAttempt

@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz.objects.prefetch_related('questions__choices'), id=quiz_id)
    questions = quiz.questions.all()

    if request.method == 'POST':
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

        if passed:
            request.user.add_xp(50)
            messages.success(request, f"🎉 Outstanding! You passed with {score_percentage}%! (+50 XP)")
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

    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'quizzes/take_quiz.html', context)
