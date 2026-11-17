"""
URL configuration for liveschool_project project.
Live School for World-Class Free Education (INT-253)
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('courses/', include('courses.urls', namespace='courses')),
    path('live/', include('live_classes.urls', namespace='live_classes')),
    path('quizzes/', include('quizzes.urls', namespace='quizzes')),
    path('community/', include('community.urls', namespace='community')),
    path('certificates/', include('certificates.urls', namespace='certificates')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
