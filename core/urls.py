from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('demographics-impact/', views.demographics_impact, name='demographics_impact'),
    path('contact/', views.contact, name='contact'),
    path('subscribe/', views.newsletter_subscribe, name='subscribe'),
    path('demo-login/<str:role>/', views.demo_login, name='demo_login'),
]

