from django.contrib import admin
from .models import LiveSession, SessionAttendee, LiveClassDoubt

@admin.register(LiveSession)
class LiveSessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'course', 'scheduled_start', 'status', 'duration_minutes')
    list_filter = ('status', 'scheduled_start')
    search_fields = ('title', 'description', 'instructor__username')

@admin.register(SessionAttendee)
class SessionAttendeeAdmin(admin.ModelAdmin):
    list_display = ('session', 'user', 'joined_at')
    list_filter = ('session',)

@admin.register(LiveClassDoubt)
class LiveClassDoubtAdmin(admin.ModelAdmin):
    list_display = ('session', 'student', 'is_answered', 'created_at')
    list_filter = ('is_answered',)
