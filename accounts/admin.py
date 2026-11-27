from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, XPLedger


class XPLedgerInline(admin.TabularInline):
    model = XPLedger
    fields = readonly_fields = ('action', 'reference_id', 'amount', 'created_at')
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_instructor_approved', 'xp_points', 'is_staff')
    list_filter = ('role', 'is_instructor_approved', 'demographic_group', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    date_hierarchy = 'date_joined'
    inlines = (XPLedgerInline,)
    actions = ('approve_instructors', 'revoke_instructors')

    def set_approval(self, request, queryset, approved):
        for user in queryset.filter(role='instructor').exclude(is_instructor_approved=approved):
            user.is_instructor_approved = approved
            user.save(update_fields=['is_instructor_approved'])
            self.log_change(request, user, 'Instructor approval granted.' if approved else 'Instructor approval revoked.')

    @admin.action(permissions=['change'], description='Approve selected instructors')
    def approve_instructors(self, request, queryset):
        self.set_approval(request, queryset, True)

    @admin.action(permissions=['change'], description='Revoke selected instructor approvals')
    def revoke_instructors(self, request, queryset):
        self.set_approval(request, queryset, False)

    fieldsets = UserAdmin.fieldsets + (
        ('Demographics & Role Information', {
            'fields': ('role', 'is_instructor_approved', 'demographic_group', 'country', 'preferred_language', 'bio', 'avatar', 'xp_points', 'streak_count', 'last_active_date')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Demographics & Role Information', {
            'fields': ('role', 'demographic_group', 'country', 'preferred_language', 'email')
        }),
    )
