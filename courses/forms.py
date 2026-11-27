from django import forms
from django.core.files.uploadedfile import UploadedFile
from pathlib import PurePath
from zipfile import BadZipFile, ZipFile
from .models import Course, Module, Lesson, CourseReview
from .video import embed_url


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ('title', 'order', 'description')

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
    def clean_resource_file(self):
        resource = self.cleaned_data['resource_file']
        if not isinstance(resource, UploadedFile):
            return resource
        if resource.size > 10 * 1024 * 1024:
            raise forms.ValidationError('Use a resource smaller than 10 MB.')
        suffix = PurePath(resource.name).suffix.lower()
        header = resource.read(8)
        resource.seek(0)
        valid = (
            (suffix == '.pdf' and header.startswith(b'%PDF-'))
            or (suffix in {'.jpg', '.jpeg'} and header.startswith(bytes.fromhex('ffd8ff')))
            or (suffix == '.png' and header == bytes.fromhex('89504e470d0a1a0a'))
        )
        if suffix in {'.zip', '.pptx', '.docx'}:
            try:
                with ZipFile(resource) as archive:
                    entries = set(archive.namelist())
                    expected = {'.pptx': 'ppt/presentation.xml', '.docx': 'word/document.xml'}
                    valid = suffix == '.zip' or (
                        '[Content_Types].xml' in entries and expected[suffix] in entries
                    )
            except BadZipFile:
                valid = False
            finally:
                resource.seek(0)
        if not valid:
            raise forms.ValidationError('Upload a PDF, PowerPoint, Word, ZIP, PNG, or JPEG file.')
        return resource

    def clean_video_url(self):
        value = self.cleaned_data['video_url']
        if value and not embed_url(value):
            raise forms.ValidationError('Enter a supported HTTPS YouTube or Vimeo video URL.')
        return value

    class Meta:
        model = Lesson
        fields = ('title', 'order', 'video_url', 'duration_minutes', 'content', 'resource_file')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }

