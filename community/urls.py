from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    path('', views.forum_list, name='forum_list'),
    path('ask/', views.create_thread, name='create_thread'),
    path('<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('<int:thread_id>/report/', views.report_content, name='report_thread'),
    path('<int:thread_id>/reply/<int:reply_id>/report/', views.report_content, name='report_reply'),
    path('reply/<int:reply_id>/upvote/', views.upvote_reply, name='upvote_reply'),
    path('reply/<int:reply_id>/solution/', views.toggle_solution, name='toggle_solution'),
]

