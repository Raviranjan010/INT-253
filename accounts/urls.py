from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth import views as auth
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('password-reset/', auth.PasswordResetView.as_view(
        template_name='accounts/reset_form.html',
        email_template_name='accounts/reset_email.txt',
        subject_template_name='accounts/reset_subject.txt',
        success_url=reverse_lazy('accounts:password_reset_done'),
    ), name='password_reset'),
    path('password-reset/sent/', auth.PasswordResetDoneView.as_view(
        template_name='accounts/reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth.PasswordResetConfirmView.as_view(
        template_name='accounts/reset_form.html',
        success_url=reverse_lazy('accounts:login'),
    ), name='password_reset_confirm'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('profile/', views.profile_view, name='profile'),
]

