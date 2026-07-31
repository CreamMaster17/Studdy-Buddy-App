from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),


    path("", include(("apps.accounts.urls", "accounts"), namespace="accounts")),
    path("", include(("apps.studybuddy_cms.urls", "studybuddy_cms"), namespace="studybuddy_cms")),
    # quiz APIs (generate, history, stats, recommendations)
    path("", include(("apps.studybuddy_quiz.urls", "studybuddy_quiz"), namespace="studybuddy_quiz")),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)