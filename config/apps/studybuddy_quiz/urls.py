"""
URL routes for Study Buddy Quiz APIs
Author: Samuel Gamon
"""

from django.urls import path

from . import views

app_name = "apps.studybuddy_quiz"

urlpatterns = [
    # Quiz generation & grading
    path("api/quiz/generate", views.generate_quiz, name="quiz-generate"),
    path("api/quiz/grade", views.grade_quiz, name="quiz-grade"),
    path("api/quiz/submit-and-save", views.submit_and_save_quiz, name="quiz-submit-save"),
    # History
    path("api/history/save", views.save_history, name="history-save"),
    path("api/history/list", views.list_history, name="history-list"),
    path(
        "api/history/detail/<int:quiz_result_id>",
        views.history_detail,
        name="history-detail",
    ),
    path("api/history/stats", views.history_stats, name="history-stats"),
    # Stats dashboard
    path("api/stats/dashboard", views.stats_dashboard, name="stats-dashboard"),
    path("api/stats/refresh", views.stats_refresh, name="stats-refresh"),
    path("api/stats/quick-summary", views.stats_quick_summary, name="stats-quick"),
    # Recommendations
    path(
        "api/recommendations/generate",
        views.recommendations_generate,
        name="rec-generate",
    ),
    path(
        "api/recommendations/cached",
        views.recommendations_cached,
        name="rec-cached",
    ),
    path(
        "api/recommendations/status",
        views.recommendations_status,
        name="rec-status",
    ),

    path(
        "api/quiz/submit-and-save/<int:quiz_id>/",
        views.submit_saved_quiz,
        name="submit-saved-quiz",
    ),

    # Quiz Page
    path(
        "quiz/",
        views.quiz_page,
        name="quiz-page",
    ),

    path(
        "quiz/practice/<int:quiz_id>/",
        views.practice_saved_quiz,
        name="practice-saved-quiz"
    ),

    path(
        "quiz-history/",
        views.quiz_history_pages,
        name="quiz-history",
        ),

    path(
        "quiz-results/<int:quiz_result_id>",
        views.quiz_results,
        name="quiz-results",
        ),
]