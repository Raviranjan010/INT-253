from django.contrib import admin
from .models import Quiz, Question, Choice, QuizAttempt

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'pass_percentage', 'time_limit_minutes', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)
    inlines = [ChoiceInline]

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score_percentage', 'passed', 'completed_at')
    list_filter = ('passed', 'quiz')
    search_fields = ('student__username', 'quiz__title')
