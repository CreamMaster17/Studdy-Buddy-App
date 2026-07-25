from django.contrib import admin

from .models import GeneratedQuiz, QuizQuestionResult, QuizResult


class QuizQuestionResultInline(admin.TabularInline):
    model = QuizQuestionResult
    extra = 0
    readonly_fields = (
        "question_id",
        "question_text",
        "user_answer",
        "correct_answer",
        "is_correct",
        "explanation",
        "created_at",
    )


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "quiz_title",
        "score_percentage",
        "correct_count",
        "total_questions",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("quiz_title", "user__username")
    inlines = [QuizQuestionResultInline]


@admin.register(GeneratedQuiz)
class GeneratedQuizAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz_title", "source_notes_length", "created_at")
    search_fields = ("quiz_title", "user__username")
