from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

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

    def clean(self):
        data = super().clean()
        correct = data.get('correct_choice')
        if correct is not None and not data.get(f'choice_{correct}'):
            self.add_error('correct_choice', 'The correct choice must have text.')
        return data


@login_required
@require_http_methods(['GET', 'POST'])
@transaction.atomic
def add_quiz_content(request, slug, quiz_id=None):
    course = owned_course(request.user, slug)
    quiz = get_object_or_404(course.quizzes, pk=quiz_id) if quiz_id else None
    form_class = QuestionForm if quiz else QuizForm
    form = form_class(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        if quiz:
            item.quiz = quiz
            item.save()
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
        'course': course, 'form': form, 'heading': 'Add question' if quiz else 'Add quiz',
    })
