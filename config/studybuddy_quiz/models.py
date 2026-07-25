"""
Quiz History models (Sprint 2 / Sprint 5)
Author: Samuel Gamon

Django ORM equivalent of db_schema_quiz.sql for saving quiz results,
per-question responses, and generated quiz snapshots.
"""

from django.conf import settings
from django.db import models


class QuizResult(models.Model):
    """Overall result of one completed quiz attempt."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_results",
    )
    quiz_title = models.CharField(max_length=255)
    score_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    correct_count = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.quiz_title} ({self.score_percentage}%) — {self.user_id}"


class QuizQuestionResult(models.Model):
    """Per-question response within a quiz attempt."""

    quiz_result = models.ForeignKey(
        QuizResult,
        on_delete=models.CASCADE,
        related_name="question_results",
    )
    question_id = models.PositiveIntegerField()
    question_text = models.TextField()
    user_answer = models.CharField(max_length=10)
    correct_answer = models.CharField(max_length=10)
    is_correct = models.BooleanField()
    explanation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["question_id"]
        indexes = [
            models.Index(fields=["quiz_result"]),
        ]

    def __str__(self):
        return f"Q{self.question_id} ({'✓' if self.is_correct else '✗'})"


class GeneratedQuiz(models.Model):
    """Snapshot of an AI-generated quiz for review/retake."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generated_quizzes",
    )
    quiz_title = models.CharField(max_length=255)
    quiz_data = models.JSONField()
    source_notes_length = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.quiz_title} (user {self.user_id})"
