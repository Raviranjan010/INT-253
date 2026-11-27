from django import forms
from django.utils import timezone
from urllib.parse import urlsplit
from .models import LiveSession, LiveClassDoubt
from courses.models import Course

class LiveSessionScheduleForm(forms.ModelForm):
    def clean_scheduled_start(self):
        start = self.cleaned_data['scheduled_start']
        if start <= timezone.now():
            raise forms.ValidationError('Choose a future date and time (IST).')
        return start

    def clean_meeting_url(self):
        value = self.cleaned_data['meeting_url']
        if value and urlsplit(value).scheme != 'https':
            raise forms.ValidationError('Enter an HTTPS meeting link.')
        return value

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.is_staff:
            self.fields['course'].queryset = Course.objects.filter(instructor=user)

    class Meta:
        model = LiveSession
        fields = ('title', 'course', 'scheduled_start', 'duration_minutes', 'description', 'target_demographics', 'meeting_url')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Masterclass: Python OOP from Scratch'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'value': 60}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'target_demographics': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. High schoolers, Rural STEM learners, Beginners'}),
        }


class DoubtForm(forms.ModelForm):
    class Meta:
        model = LiveClassDoubt
        fields = ('question',)
        widgets = {
            'question': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Type your question or doubt for the instructor...'}),
        }

