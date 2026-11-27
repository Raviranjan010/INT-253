from django.contrib import admin
from django.http import HttpResponse
import csv
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
    list_display = ('email', 'subscribed_at', 'confirmed_at')
    search_fields = ('email',)
    readonly_fields = ('confirmed_at',)
    actions = ('export_confirmed',)

    @admin.action(permissions=['view'], description='Export selected confirmed subscribers')
    def export_confirmed(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="confirmed-subscribers.csv"'
        writer = csv.writer(response)
        writer.writerow(['email'])
        for address in queryset.filter(confirmed_at__isnull=False).values_list('email', flat=True).iterator():
            writer.writerow(["'" + address if address.startswith(('=', '+', '-', '@')) else address])
        return response

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
