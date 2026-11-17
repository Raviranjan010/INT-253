from django import forms
from .models import LiveSession, LiveClassDoubt

class LiveSessionScheduleForm(forms.ModelForm):
    class Meta:
        model = LiveSession
        fields = ('title', 'course', 'scheduled_start', 'duration_minutes', 'description', 'target_demographics')
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

