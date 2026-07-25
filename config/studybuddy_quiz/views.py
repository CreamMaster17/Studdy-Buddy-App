"""
Django REST API views for Study Buddy Quiz features
Author: Samuel Gamon

Endpoints:
  POST /api/quiz/generate
  POST /api/quiz/grade
  POST /api/quiz/submit-and-save
  POST /api/history/save
  GET  /api/history/list
  GET  /api/history/detail/<id>
  GET  /api/history/stats
  GET  /api/stats/dashboard
  POST /api/stats/refresh
  GET  /api/stats/quick-summary
  POST /api/recommendations/generate
  GET  /api/recommendations/cached
  GET  /api/recommendations/status
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import GeneratedQuiz
from .quiz_generator import (
    generate_quiz_from_notes,
    grade_quiz_submission,
    quiz_for_client,
)
from .quiz_history import (
    get_quiz_result_detail,
    get_user_quiz_history,
    get_user_quiz_stats,
    save_quiz_result,
)
from .study_recommendations import (
    RATE_LIMIT_SECONDS,
    GEMINI_API_KEY,
    GEMINI_AVAILABLE,
    OPENAI_API_KEY,
    OPENAI_AVAILABLE,
    check_rate_limit,
    generate_study_recommendations,
)
from .study_stats import get_quick_summary, get_user_dashboard_stats
from django.utils import timezone


# ---------- Quiz generation / grading ----------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def generate_quiz(request):
    """POST {"notes": "...", "num_questions": 5}"""
    notes_text = request.data.get("notes", "")
    num_questions = request.data.get("num_questions", 5)

    if not isinstance(notes_text, str) or len(notes_text.strip()) < 10:
        return Response(
            {"error": "Notes text is too short. Minimum 10 characters required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        num_questions = int(num_questions)
    except (TypeError, ValueError):
        return Response(
            {"error": "num_questions must be an integer between 1 and 20."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if num_questions < 1 or num_questions > 20:
        return Response(
            {"error": "num_questions must be an integer between 1 and 20."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    quiz_data = generate_quiz_from_notes(notes_text.strip(), num_questions)
    if "error" in quiz_data:
        return Response(quiz_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    request.session["last_generated_quiz"] = quiz_data

    GeneratedQuiz.objects.create(
        user=request.user,
        quiz_title=quiz_data.get("quiz_title", "Generated Quiz"),
        quiz_data=quiz_data,
        source_notes_length=quiz_data.get("source_notes_length"),
    )

    return Response(quiz_for_client(quiz_data), status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grade_quiz(request):
    """POST {"answers": {"1": "A", "2": "C", ...}}"""
    answers = request.data.get("answers")
    if not isinstance(answers, dict):
        return Response(
            {"error": "Missing required field: 'answers'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    quiz_data = request.session.get("last_generated_quiz")
    if not quiz_data:
        return Response(
            {"error": "No quiz found. Please generate a quiz first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results = grade_quiz_submission(quiz_data, answers)
    if "error" in results:
        return Response(results, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    request.session["last_graded_result"] = {
        "quiz_title": quiz_data.get("quiz_title", "Untitled Quiz"),
        "results": results,
    }
    return Response(results, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_and_save_quiz(request):
    """Grade and save to the authenticated user's history."""
    answers = request.data.get("answers")
    if not isinstance(answers, dict):
        return Response(
            {"error": "Missing required field: 'answers'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    quiz_data = request.session.get("last_generated_quiz")
    if not quiz_data:
        return Response(
            {"error": "No quiz found. Please generate a quiz first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results = grade_quiz_submission(quiz_data, answers)
    if "error" in results:
        return Response(results, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    save_result = save_quiz_result(
        user=request.user,
        quiz_title=quiz_data.get("quiz_title", "Untitled Quiz"),
        score_percentage=results["score_percentage"],
        correct_count=results["correct_count"],
        total_questions=results["total_questions"],
        question_results=results["question_results"],
    )
    results["saved_to_history"] = save_result
    return Response(results, status=status.HTTP_200_OK)


# ---------- History ----------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_history(request):
    result = save_quiz_result(
        user=request.user,
        quiz_title=request.data.get("quiz_title", "Untitled Quiz"),
        score_percentage=request.data.get("score_percentage", 0.0),
        correct_count=request.data.get("correct_count", 0),
        total_questions=request.data.get("total_questions", 0),
        question_results=request.data.get("question_results", []),
    )
    if result.get("success"):
        return Response(result, status=status.HTTP_201_CREATED)
    return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_history(request):
    try:
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
    except (TypeError, ValueError):
        limit, offset = 50, 0

    if limit < 1 or limit > 100:
        limit = 50
    if offset < 0:
        offset = 0

    history = get_user_quiz_history(request.user, limit=limit, offset=offset)
    return Response(
        {
            "history": history,
            "total_count": len(history),
            "limit": limit,
            "offset": offset,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history_detail(request, quiz_result_id):
    detail = get_quiz_result_detail(quiz_result_id, request.user)
    if detail is None:
        return Response(
            {"error": "Quiz result not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(detail)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def history_stats(request):
    return Response(get_user_quiz_stats(request.user))


# ---------- Stats dashboard ----------


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_dashboard(request):
    return Response(get_user_dashboard_stats(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stats_refresh(request):
    stats = get_user_dashboard_stats(request.user)
    stats["refreshed_at"] = timezone.now().isoformat()
    return Response(stats)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stats_quick_summary(request):
    return Response(get_quick_summary(request.user))


# ---------- Recommendations ----------


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def recommendations_generate(request):
    if not check_rate_limit(request.user.id):
        return Response(
            {
                "error": "RATE_LIMITED",
                "message": (
                    f"Please wait {RATE_LIMIT_SECONDS} seconds between "
                    "recommendation requests."
                ),
                "retry_after": RATE_LIMIT_SECONDS,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    try:
        result = generate_study_recommendations(request.user)
        if "error" in result and result["error"] in ("AI_API_ERROR", "PARSE_ERROR"):
            code = (
                status.HTTP_503_SERVICE_UNAVAILABLE
                if result["error"] == "AI_API_ERROR"
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(result, status=code)

        request.session["last_recommendations"] = result
        return Response(result)
    except Exception as e:
        return Response(
            {
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while generating recommendations.",
                "detail": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommendations_cached(request):
    cached = request.session.get("last_recommendations")
    if not cached:
        return Response(
            {
                "message": "No cached recommendations. Generate new ones first.",
                "recommendations": [],
            }
        )
    return Response(cached)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommendations_status(request):
    gemini_ok = GEMINI_AVAILABLE and bool(GEMINI_API_KEY)
    openai_ok = OPENAI_AVAILABLE and bool(OPENAI_API_KEY)
    return Response(
        {
            "gemini_available": gemini_ok,
            "openai_available": openai_ok,
            "any_api_available": gemini_ok or openai_ok,
            "rate_limit_seconds": RATE_LIMIT_SECONDS,
        }
    )
