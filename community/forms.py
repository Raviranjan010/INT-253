from django import forms
from .models import DiscussionThread, DiscussionReply

class ThreadForm(forms.ModelForm):
    class Meta:
        model = DiscussionThread
        fields = ('title', 'course', 'content', 'tags')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. How does recursion work in Python?'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe your doubt or question in detail...'}),
            'tags': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. python, algorithm, loops'}),
        }


class ReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write your helpful explanation or answer here...'}),
        }

