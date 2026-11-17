from django.contrib import admin
from .models import DiscussionThread, DiscussionReply

class DiscussionReplyInline(admin.StackedInline):
    model = DiscussionReply
    extra = 1

@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'course', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    inlines = [DiscussionReplyInline]

@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ('author', 'thread', 'is_solution', 'created_at')
    list_filter = ('is_solution', 'created_at')
