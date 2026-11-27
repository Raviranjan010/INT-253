from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from courses.studio import owned_course
from .models import Choice, Question, Quiz


class QuizForm(forms.ModelForm):
    pass_percentage = forms.IntegerField(min_value=0, max_value=100)

    class Meta:
        model = Quiz
        fields = ('title', 'description', 'pass_percentage', 'time_limit_minutes', 'max_attempts')


class QuestionForm(forms.ModelForm):
    correct_choice = forms.IntegerField(min_value=1, max_value=6, help_text='Enter the number of the correct choice.')

    class Meta:
        model = Question
        fields = ('text', 'explanation', 'order')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for position in range(1, 7):
            self.fields[f'choice_{position}'] = forms.CharField(
                max_length=300, label=f'Choice {position}', required=position <= 2,
            )
        if self.instance.pk:
            for position, choice in enumerate(self.instance.choices.order_by('pk')[:6], start=1):
                self.initial[f'choice_{position}'] = choice.text
                if choice.is_correct:
                    self.initial['correct_choice'] = position

    def clean(self):
        data = super().clean()
        correct = data.get('correct_choice')
        if correct is not None and not data.get(f'choice_{correct}'):
            self.add_error('correct_choice', 'The correct choice must have text.')
        return data


@login_required
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def add_quiz_content(request, slug, quiz_id=None, question_id=None, *, edit_quiz=False):
    course = owned_course(request.user, slug)
    quiz = get_object_or_404(course.quizzes.select_for_update(), pk=quiz_id) if quiz_id else None
    question = get_object_or_404(quiz.questions, pk=question_id) if question_id else None
    editing_question = quiz is not None and not edit_quiz
    instance = question if editing_question else quiz
    form_class = QuestionForm if editing_question else QuizForm
    if request.method == 'POST' and quiz and quiz.attempts.exists():
        messages.error(request, 'Quizzes with recorded attempts cannot be changed. Create a new quiz instead.')
        return redirect('courses:studio', slug=slug)
    form = form_class(request.POST if request.method == 'POST' else None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        if editing_question:
            item.quiz = quiz
            item.save()
            if question:
                item.choices.all().delete()
            for position in range(1, 7):
                choice = form.cleaned_data[f'choice_{position}']
                if choice:
                    Choice.objects.create(
                        question=item, text=choice,
                        is_correct=position == form.cleaned_data['correct_choice'],
                    )
        else:
            item.course = course
            item.save()
        messages.success(request, 'Saved.')
        return redirect('courses:studio', slug=slug)
    return render(request, 'courses/studio_form.html', {
        'course': course,
        'form': form,
        'heading': ('Edit' if instance else 'Add') + (' question' if editing_question else ' quiz'),
    })


@login_required
@require_POST
@transaction.atomic
def delete_quiz_content(request, slug, quiz_id, question_id=None):
    course = owned_course(request.user, slug)
    quiz = get_object_or_404(course.quizzes.select_for_update(), pk=quiz_id)
    item = get_object_or_404(quiz.questions, pk=question_id) if question_id else quiz
    if quiz.attempts.exists():
        messages.error(request, 'Quizzes with recorded attempts cannot be deleted.')
    else:
        item.delete()
        messages.success(request, 'Deleted.')
    return redirect('courses:studio', slug=slug)
