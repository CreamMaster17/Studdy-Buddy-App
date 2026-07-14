from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "cms"

router = DefaultRouter()
router.register("subjects", views.SubjectViewSet, basename="subject")
router.register("content", views.ContentItemViewSet, basename="content")
router.register("assessments", views.AssessmentViewSet, basename="assessment")
router.register("attempts", views.AssessmentAttemptViewSet, basename="attempt")
router.register("notes", views.NoteViewSet, basename="note")

urlpatterns = [
    path("", include(router.urls)),
]
