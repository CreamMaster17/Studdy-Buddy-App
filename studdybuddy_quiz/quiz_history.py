"""
Sprint 2 / Sprint 5 - Quiz History and Progress Tracking
Author: Samuel Gamon

Save/retrieve quiz results per user via Django ORM (SQLite in this project).
Indexes on (user, created_at) keep history queries fast as attempts pile up.
"""

from .models import QuizQuestionResult, QuizResult


def save_quiz_result(
    user,
    quiz_title,
    score_percentage,
    correct_count,
    total_questions,
    question_results=None,
):
    """
    Persist a completed quiz result for a user.

    Returns:
        dict: {success, quiz_result_id, message} or error info
    """
    try:
        quiz_result = QuizResult.objects.create(
            user=user,
            quiz_title=quiz_title or "Untitled Quiz",
            score_percentage=score_percentage,
            correct_count=correct_count,
            total_questions=total_questions,
        )

        if question_results:
            QuizQuestionResult.objects.bulk_create(
                [
                    QuizQuestionResult(
                        quiz_result=quiz_result,
                        question_id=qr.get("question_id", 0),
                        question_text=qr.get("question_text", ""),
                        user_answer=str(qr.get("user_answer", ""))[:10],
                        correct_answer=str(qr.get("correct_answer", ""))[:10],
                        is_correct=bool(qr.get("is_correct", False)),
                        explanation=qr.get("explanation", "") or "",
                    )
                    for qr in question_results
                ]
            )

        return {
            "success": True,
            "quiz_result_id": quiz_result.id,
            "message": "Quiz result saved successfully.",
        }
    except Exception as e:
        return {"success": False, "error": f"Database error: {str(e)}"}


def get_user_quiz_history(user, limit=50, offset=0):
    """Return a user's quiz history as clean JSON-ready dicts."""
    rows = (
        QuizResult.objects.filter(user=user)
        .order_by("-created_at")[offset : offset + limit]
    )
    history = []
    for row in rows:
        history.append(
            {
                "quiz_result_id": row.id,
                "quiz_title": row.quiz_title,
                "score_percentage": float(row.score_percentage),
                "correct_count": row.correct_count,
                "total_questions": row.total_questions,
                "taken_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return history


def get_quiz_result_detail(quiz_result_id, user):
    """Fetch detailed results for one quiz attempt (scoped to user)."""
    try:
        result = QuizResult.objects.prefetch_related("question_results").get(
            id=quiz_result_id, user=user
        )
    except QuizResult.DoesNotExist:
        return None

    return {
        "quiz_result_id": result.id,
        "quiz_title": result.quiz_title,
        "score_percentage": float(result.score_percentage),
        "correct_count": result.correct_count,
        "total_questions": result.total_questions,
        "taken_at": result.created_at.isoformat() if result.created_at else None,
        "questions": [
            {
                "question_id": q.question_id,
                "question_text": q.question_text,
                "user_answer": q.user_answer,
                "correct_answer": q.correct_answer,
                "is_correct": q.is_correct,
                "explanation": q.explanation,
            }
            for q in result.question_results.all()
        ],
    }


def get_user_quiz_stats(user):
    """Aggregate quiz statistics for a user (empty-safe for new users)."""
    from django.db.models import Avg, Count, Max, Min, Sum

    agg = QuizResult.objects.filter(user=user).aggregate(
        total_quizzes=Count("id"),
        average_score=Avg("score_percentage"),
        best_score=Max("score_percentage"),
        worst_score=Min("score_percentage"),
        total_correct_answers=Sum("correct_count"),
        total_questions_answered=Sum("total_questions"),
    )

    if not agg["total_quizzes"]:
        return {
            "total_quizzes": 0,
            "average_score": 0.0,
            "best_score": 0.0,
            "worst_score": 0.0,
            "total_correct_answers": 0,
            "total_questions_answered": 0,
        }

    return {
        "total_quizzes": agg["total_quizzes"],
        "average_score": round(float(agg["average_score"] or 0), 1),
        "best_score": round(float(agg["best_score"] or 0), 1),
        "worst_score": round(float(agg["worst_score"] or 0), 1),
        "total_correct_answers": agg["total_correct_answers"] or 0,
        "total_questions_answered": agg["total_questions_answered"] or 0,
    }