from django.contrib import admin
from .models import Category, Course, Module, Lesson, Enrollment, LessonProgress, CourseReview

class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1

class ModuleInline(admin.StackedInline):
    model = Module
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'instructor', 'level', 'language', 'is_published', 'created_at')
    list_filter = ('category', 'level', 'language', 'is_published')
    search_fields = ('title', 'description', 'instructor__username')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order', 'duration_minutes')
    list_filter = ('module__course', 'module')
    search_fields = ('title', 'content')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'progress_percentage', 'is_completed', 'enrolled_at', 'completed_at')
    list_filter = ('is_completed', 'course')
    search_fields = ('student__username', 'course__title')

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed',)

@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'rating', 'created_at')
    list_filter = ('rating', 'course')
