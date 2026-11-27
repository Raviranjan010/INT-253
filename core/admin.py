from django.contrib import admin
from .models import ContactMessage, NewsletterSubscriber, Announcement

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    actions = ('mark_as_read',)

    @admin.action(permissions=['change'], description='Mark selected messages as read')
    def mark_as_read(self, request, queryset):
        total = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, f'{total} messages marked as read.')

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
