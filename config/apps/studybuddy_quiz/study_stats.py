"""
Sprint 3 / Sprint 5 - User Study Statistics Dashboard
Author: Samuel Gamon

Dashboard API aggregates: overview metrics, weekly activity, score trends,
subject breakdown, and progress indicators. Safe for brand-new users.
"""

from datetime import timedelta

from django.db.models import Avg, Count, Max, Min, Sum
from django.utils import timezone

from .models import QuizResult


def _empty_stats():
    """Empty but valid stats for users with no quiz history."""
    return {
        "overview": {
            "total_quizzes_taken": 0,
            "overall_average_score": 0.0,
            "best_score": 0.0,
            "worst_score": 0.0,
            "total_correct_answers": 0,
            "total_questions_answered": 0,
            "overall_accuracy_rate": 0.0,
            "last_quiz_date": None,
        },
        "weekly_activity": {
            "quizzes_this_week": 0,
            "weekly_average_score": 0.0,
        },
        "subject_breakdown": [],
        "score_trend": [],
        "progress_indicator": {
            "status": "new",
            "label": "Just Getting Started",
            "description": "Complete your first quiz to see your progress!",
            "trend_direction": "neutral",
        },
        "last_updated": timezone.now().isoformat(),
    }


def _calculate_progress(recent_scores):
    """Progress trend from recent quiz scores."""
    if len(recent_scores) < 2:
        return {
            "status": "new",
            "label": "Just Getting Started" if not recent_scores else "First Quiz Complete!",
            "description": (
                "Keep taking quizzes to track your progress."
                if not recent_scores
                else "Take more quizzes to see your trend!"
            ),
            "trend_direction": "neutral",
        }

    half = len(recent_scores) // 2
    first_half_avg = sum(s["score"] for s in recent_scores[:half]) / half
    second_half_avg = sum(s["score"] for s in recent_scores[half:]) / (
        len(recent_scores) - half
    )
    diff = second_half_avg - first_half_avg

    if diff >= 10:
        return {
            "status": "improving",
            "label": "Improving",
            "description": f"Your scores are trending up by {round(diff, 1)} points! Keep it up!",
            "trend_direction": "up",
            "trend_value": round(diff, 1),
        }
    if diff >= 5:
        return {
            "status": "improving_slightly",
            "label": "Getting Better",
            "description": f"You're showing improvement (+{round(diff, 1)} points).",
            "trend_direction": "up",
            "trend_value": round(diff, 1),
        }
    if diff <= -10:
        return {
            "status": "declining",
            "label": "Needs Attention",
            "description": "Your recent scores have dropped. Consider reviewing past material.",
            "trend_direction": "down",
            "trend_value": round(diff, 1),
        }
    if diff <= -5:
        return {
            "status": "declining_slightly",
            "label": "Slight Dip",
            "description": "A small decrease in scores. A quick review might help!",
            "trend_direction": "down",
            "trend_value": round(diff, 1),
        }
    return {
        "status": "steady",
        "label": "Steady",
        "description": "Your scores are holding steady. Keep practicing!",
        "trend_direction": "neutral",
        "trend_value": round(diff, 1),
    }


def get_user_dashboard_stats(user):
    """Build the full dashboard payload for a user."""
    qs = QuizResult.objects.filter(user=user)
    basic = qs.aggregate(
        total_quizzes=Count("id"),
        average_score=Avg("score_percentage"),
        best_score=Max("score_percentage"),
        worst_score=Min("score_percentage"),
        total_correct=Sum("correct_count"),
        total_questions=Sum("total_questions"),
        last_quiz_date=Max("created_at"),
    )

    if not basic["total_quizzes"]:
        return _empty_stats()

    week_ago = timezone.now() - timedelta(days=7)
    weekly = qs.filter(created_at__gte=week_ago).aggregate(
        quizzes_this_week=Count("id"),
        weekly_average=Avg("score_percentage"),
    )

    subject_breakdown = []
    for row in (
        qs.values("quiz_title")
        .annotate(times_taken=Count("id"), avg_score=Avg("score_percentage"))
        .order_by("-times_taken")[:5]
    ):
        subject_breakdown.append(
            {
                "subject": row["quiz_title"],
                "quizzes_taken": row["times_taken"],
                "average_score": round(float(row["avg_score"] or 0), 1),
            }
        )

    recent_rows = list(qs.order_by("-created_at")[:10])
    recent_rows.reverse()
    recent_scores = [
        {
            "quiz_id": row.id,
            "quiz_title": row.quiz_title,
            "score": round(float(row.score_percentage), 1),
            "date": row.created_at.strftime("%Y-%m-%d"),
        }
        for row in recent_rows
    ]

    total_correct = basic["total_correct"] or 0
    total_questions = basic["total_questions"] or 0

    return {
        "overview": {
            "total_quizzes_taken": basic["total_quizzes"],
            "overall_average_score": round(float(basic["average_score"] or 0), 1),
            "best_score": round(float(basic["best_score"] or 0), 1),
            "worst_score": round(float(basic["worst_score"] or 0), 1),
            "total_correct_answers": total_correct,
            "total_questions_answered": total_questions,
            "overall_accuracy_rate": (
                round((total_correct / total_questions) * 100, 1)
                if total_questions
                else 0.0
            ),
            "last_quiz_date": (
                basic["last_quiz_date"].isoformat() if basic["last_quiz_date"] else None
            ),
        },
        "weekly_activity": {
            "quizzes_this_week": weekly["quizzes_this_week"] or 0,
            "weekly_average_score": round(float(weekly["weekly_average"] or 0), 1),
        },
        "subject_breakdown": subject_breakdown,
        "score_trend": recent_scores,
        "progress_indicator": _calculate_progress(recent_scores),
        "last_updated": timezone.now().isoformat(),
    }


def get_quick_summary(user):
    """Compact stats for navbar/sidebar widgets."""
    agg = QuizResult.objects.filter(user=user).aggregate(
        total_quizzes=Count("id"),
        average_score=Avg("score_percentage"),
    )
    return {
        "total_quizzes": agg["total_quizzes"] or 0,
        "average_score": round(float(agg["average_score"] or 0), 1),
    }