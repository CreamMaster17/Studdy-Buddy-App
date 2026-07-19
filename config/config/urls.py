from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include(("studybuddy_cms.urls", "studybuddy_cms"), namespace="studybuddy_cms")),
]