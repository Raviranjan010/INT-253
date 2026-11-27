from django.urls import path
from . import views, studio
from quizzes.studio import add_quiz_content

app_name = 'courses'

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('new/', views.create_course, name='create_course'),
    path('<slug:slug>/studio/', studio.studio, name='studio'),
    path('<slug:slug>/studio/quizzes/new/', add_quiz_content, name='studio_quiz_new'),
    path('<slug:slug>/studio/quizzes/<int:quiz_id>/questions/new/', add_quiz_content, name='studio_question_new'),
    path('<slug:slug>/studio/publication/', studio.change_content, {'action': 'publication'}, name='studio_publication'),
    path('<slug:slug>/studio/modules/new/', studio.edit_content, {'kind': 'module'}, name='studio_module_new'),
    path('<slug:slug>/studio/modules/<int:module_id>/edit/', studio.edit_content, {'kind': 'module'}, name='studio_module_edit'),
    path('<slug:slug>/studio/modules/<int:module_id>/delete/', studio.change_content, {'action': 'delete'}, name='studio_module_delete'),
    path('<slug:slug>/studio/modules/<int:module_id>/lessons/new/', studio.edit_content, {'kind': 'lesson'}, name='studio_lesson_new'),
    path('<slug:slug>/studio/modules/<int:module_id>/lessons/<int:lesson_id>/edit/', studio.edit_content, {'kind': 'lesson'}, name='studio_lesson_edit'),
    path('<slug:slug>/studio/modules/<int:module_id>/lessons/<int:lesson_id>/delete/', studio.change_content, {'action': 'delete'}, name='studio_lesson_delete'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),
    path('<slug:slug>/edit/', views.edit_course, name='edit_course'),
    path('<slug:slug>/delete/', views.delete_course, name='delete_course'),
    path('<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
    path('<slug:course_slug>/learn/<int:lesson_id>/', views.lesson_player, name='lesson_player'),
    path('<slug:course_slug>/learn/<int:lesson_id>/toggle/', views.toggle_lesson_completion, name='toggle_lesson_completion'),
]
