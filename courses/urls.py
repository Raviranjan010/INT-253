from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('new/', views.create_course, name='create_course'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),
    path('<slug:slug>/edit/', views.edit_course, name='edit_course'),
    path('<slug:slug>/delete/', views.delete_course, name='delete_course'),
    path('<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
    path('<slug:course_slug>/learn/<int:lesson_id>/', views.lesson_player, name='lesson_player'),
    path('<slug:course_slug>/learn/<int:lesson_id>/toggle/', views.toggle_lesson_completion, name='toggle_lesson_completion'),
]
