from django.urls import path
from . import views

app_name = 'live_classes'

urlpatterns = [
    path('', views.live_class_list, name='live_class_list'),
    path('schedule/', views.schedule_live_class, name='schedule_live_class'),
    path('<uuid:session_id>/', views.live_class_room, name='live_class_room'),
    path('<uuid:session_id>/doubt/', views.post_doubt, name='post_doubt'),
    path('doubt/<int:doubt_id>/answer/', views.answer_doubt, name='answer_doubt'),
]

