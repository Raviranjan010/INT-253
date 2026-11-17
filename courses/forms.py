from django import forms
from .models import Course, Module, Lesson, CourseReview

class CourseReviewForm(forms.ModelForm):
    class Meta:
        model = CourseReview
        fields = ('rating', 'review_text')
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'review_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share how this free course helped your learning...'}),
        }


class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'category', 'level', 'language', 'short_description', 'description', 'estimated_hours', 'thumbnail')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. English, Hindi'}),
            'short_description': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'estimated_hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('title', 'order', 'video_url', 'duration_minutes', 'content')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

