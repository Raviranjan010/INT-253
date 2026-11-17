from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'demographic_group', 'xp_points', 'streak_count', 'is_staff')
    list_filter = ('role', 'demographic_group', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Demographics & Role Information', {
            'fields': ('role', 'demographic_group', 'country', 'preferred_language', 'bio', 'avatar', 'xp_points', 'streak_count', 'last_active_date')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Demographics & Role Information', {
            'fields': ('role', 'demographic_group', 'country', 'preferred_language', 'email')
        }),
    )
