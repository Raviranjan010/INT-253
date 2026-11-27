from django.contrib import admin
from .models import DiscussionThread, DiscussionReply, Report
from django.utils import timezone

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


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('thread', 'reply', 'reporter', 'created_at', 'resolved_at')
    list_filter = ('resolved_at',)
    search_fields = ('reason', 'thread__title', 'reporter__username')
    list_select_related = ('thread', 'reply', 'reporter')
    readonly_fields = ('thread', 'reply', 'reporter', 'reason', 'created_at', 'resolved_at')
    actions = ('hide_reported_content',)

    def has_add_permission(self, request):
        return False

    @admin.action(permissions=['change'], description='Hide reported content and resolve selected reports')
    def hide_reported_content(self, request, queryset):
        for report in queryset.select_related('thread', 'reply'):
            target = report.reply or report.thread
            required = f'{target._meta.app_label}.change_{target._meta.model_name}'
            if not request.user.has_perm(required):
                continue
            target.is_hidden = True
            target.save(update_fields=['is_hidden'])
            report.resolved_at = timezone.now()
            report.save(update_fields=['resolved_at'])
            self.log_change(request, report, 'Reported content hidden.')
