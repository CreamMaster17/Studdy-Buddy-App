from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include(("studybuddy_cms.urls", "studybuddy_cms"), namespace="studybuddy_cms")),
    # quiz APIs (generate, history, stats, recommendations)
    path("", include(("studybuddy_quiz.urls", "studybuddy_quiz"), namespace="studybuddy_quiz")),
]
