from io import BytesIO
from zipfile import ZipFile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from accounts.forms import UserProfileForm
from .forms import LessonForm


class UploadValidationTests(TestCase):
    def lesson_form(self, file, video=''):
        return LessonForm(
            {'title': 'Reading', 'order': 1, 'content': 'Course notes',
             'duration_minutes': 10, 'video_url': video},
            {'resource_file': file},
        )

    def test_document_checks_content_size_and_randomizes_name(self):
        spoofed = self.lesson_form(SimpleUploadedFile('notes.pdf', b'<html>unsupported</html>'))
        self.assertIn('resource_file', spoofed.errors)
        large = self.lesson_form(SimpleUploadedFile('notes.pdf', b'x' * (10 * 1024 * 1024 + 1)))
        self.assertIn('resource_file', large.errors)
        doc = BytesIO()
        with ZipFile(doc, 'w') as archive:
            archive.writestr('[Content_Types].xml', '<Types/>')
            archive.writestr('word/document.xml', '<document/>')
        valid = self.lesson_form(SimpleUploadedFile('notes.docx', doc.getvalue()))
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertRegex(valid.cleaned_data['resource_file'].name, r'^[a-f0-9]{32}\.docx$')
        bad_archive = self.lesson_form(SimpleUploadedFile('notes.zip', b'not a zip'))
        self.assertIn('resource_file', bad_archive.errors)
        bad_video = self.lesson_form(SimpleUploadedFile('notes.pdf', b'%PDF-1.7'), 'https://example.test/')
        self.assertIn('video_url', bad_video.errors)

    def test_avatar_is_validated_and_renamed(self):
        data = {'preferred_language': 'English', 'demographic_group': 'general'}
        png = BytesIO()
        Image.new('RGB', (5, 5)).save(png, 'PNG')
        valid = UserProfileForm(data, {'avatar': SimpleUploadedFile('portrait.png', png.getvalue())})
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertRegex(valid.cleaned_data['avatar'].name, r'^[a-f0-9]{32}\.png$')
        gif = BytesIO()
        Image.new('RGB', (5, 5)).save(gif, 'GIF')
        unsupported = UserProfileForm(data, {'avatar': SimpleUploadedFile('portrait.gif', gif.getvalue())})
        self.assertIn('avatar', unsupported.errors)
