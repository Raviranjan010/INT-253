from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    path('verify/', views.verify_certificate, name='verify'),
    path('verify/<str:certificate_id>/', views.verify_certificate, name='verify_detail'),
    path('<str:certificate_id>/', views.view_certificate, name='view_certificate'),
]

