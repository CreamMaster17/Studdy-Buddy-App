"""
Sprint 4 / Sprint 5 - Personalized AI Study Recommendations
Author: Samuel Gamon

Analyzes quiz history (weak/strong subjects) and returns actionable advice.
Includes rate limiting so recommendation requests don't over-hit the AI API.
"""

import os
import re
import time
from statistics import pstdev

from django.db.models import Avg, Count, Max
from django.utils import timezone

from .models import QuizResult

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from google import genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

GEMINI_CLIENT = None
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# New API keys can no longer use gemini-2.5-flash; default to a current Flash model.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    GEMINI_CLIENT = genai.Client(api_key=GEMINI_API_KEY)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
if OPENAI_AVAILABLE and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Rate limiter: {user_id: last_request_timestamp}
_rate_limit_cache = {}
RATE_LIMIT_SECONDS = 30


def _variance_to_consistency(stddev):
    if stddev is None:
        return "unknown"
    val = float(stddev)
    if val < 10:
        return "very_consistent"
    if val < 20:
        return "consistent"
    if val < 30:
        return "variable"
    return "inconsistent"


def _build_quiz_history_payload(user):
    """Structure quiz history for the recommendation prompt. None if empty."""
    qs = QuizResult.objects.filter(user=user)
    overall = qs.aggregate(
        total_quizzes=Count("id"),
        average_score=Avg("score_percentage"),
        last_quiz_date=Max("created_at"),
    )

    if not overall["total_quizzes"]:
        return None

    subjects = []
    for row in (
        qs.values("quiz_title")
        .annotate(times_taken=Count("id"), average_score=Avg("score_percentage"))
        .order_by("-times_taken", "average_score")[:8]
    ):
        scores = list(
            qs.filter(quiz_title=row["quiz_title"]).values_list(
                "score_percentage", flat=True
            )
        )
        variance = pstdev([float(s) for s in scores]) if len(scores) > 1 else 0.0
        subjects.append(
            {
                "subject": row["quiz_title"],
                "times_taken": row["times_taken"],
                "average_score": round(float(row["average_score"] or 0), 1),
                "consistency": _variance_to_consistency(variance),
            }
        )

    recent_quizzes = []
    for row in qs.order_by("-created_at")[:10]:
        recent_quizzes.append(
            {
                "subject": row.quiz_title,
                "score": round(float(row.score_percentage), 1),
                "correct": row.correct_count,
                "total": row.total_questions,
                "date": row.created_at.strftime("%Y-%m-%d"),
            }
        )

    weak_areas = [s for s in subjects if s["average_score"] < 70.0]
    strong_areas = [s for s in subjects if s["average_score"] >= 85.0]

    return {
        "overall_stats": {
            "total_quizzes": overall["total_quizzes"],
            "average_score": round(float(overall["average_score"] or 0), 1),
            "last_quiz_date": (
                overall["last_quiz_date"].strftime("%Y-%m-%d")
                if overall["last_quiz_date"]
                else None
            ),
        },
        "subject_performance": subjects,
        "recent_quizzes": recent_quizzes,
        "weak_areas": weak_areas,
        "strong_areas": strong_areas,
    }


def _build_recommendation_prompt(history_payload):
    overall = history_payload["overall_stats"]
    subjects = history_payload["subject_performance"]
    weak_areas = history_payload["weak_areas"]
    strong_areas = history_payload["strong_areas"]
    recent = history_payload["recent_quizzes"]

    prompt = f"""You are an expert academic coach AI. Analyze this student's quiz performance data and provide personalized study recommendations.

STUDENT OVERVIEW:
- Total quizzes taken: {overall['total_quizzes']}
- Overall average score: {overall['average_score']}%
- Last quiz taken: {overall['last_quiz_date']}

SUBJECT PERFORMANCE:
"""
    for s in subjects:
        prompt += (
            f"- {s['subject']}: {s['average_score']}% average over "
            f"{s['times_taken']} attempt(s)\n"
        )

    if weak_areas:
        prompt += "\nWEAKEST AREAS (below 70%):\n"
        for w in weak_areas:
            prompt += f"- {w['subject']}: {w['average_score']}%\n"

    if strong_areas:
        prompt += "\nSTRONGEST AREAS (above 85%):\n"
        for s in strong_areas:
            prompt += f"- {s['subject']}: {s['average_score']}%\n"

    prompt += "\nRECENT QUIZZES:\n"
    for r in recent[:5]:
        prompt += (
            f"- {r['subject']}: {r['score']}% ({r['correct']}/{r['total']}) "
            f"on {r['date']}\n"
        )

    prompt += """

Provide 4-5 specific, actionable study recommendations. Format your response EXACTLY as follows:

RECOMMENDATION 1: [Title]
[2-3 sentence specific actionable advice]

RECOMMENDATION 2: [Title]
[2-3 sentence specific actionable advice]

RECOMMENDATION 3: [Title]
[2-3 sentence specific actionable advice]

RECOMMENDATION 4: [Title]
[2-3 sentence specific actionable advice]

FOCUS AREA: [Name the single most important subject/topic to focus on]
WHY: [One sentence explaining why this is the priority]

Keep advice practical and specific. Do not use markdown formatting."""

    return prompt


def _call_gemini_for_recommendations(prompt):
    if not GEMINI_AVAILABLE or GEMINI_CLIENT is None:
        return None, "Gemini API not configured"

    try:
        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0.4,
                "max_output_tokens": 1024,
            },
        )
        return response.text, None
    except Exception as e:
        return None, f"Gemini API error: {str(e)}"


def _call_openai_for_recommendations(prompt):
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        return None, "OpenAI API not configured"

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert academic coach. Provide concise, actionable "
                        "study recommendations based on quiz performance data."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1024,
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"OpenAI API error: {str(e)}"


def _parse_recommendations(ai_text):
    if not ai_text:
        return None

    recommendations = []
    rec_pattern = r"RECOMMENDATION\s+\d+:\s*(.+?)(?=RECOMMENDATION|FOCUS AREA|$)"
    rec_matches = re.findall(rec_pattern, ai_text, re.DOTALL | re.IGNORECASE)

    for i, match in enumerate(rec_matches, 1):
        lines = match.strip().split("\n", 1)
        title = lines[0].strip() if lines else f"Recommendation {i}"
        body = lines[1].strip() if len(lines) > 1 else ""
        title = title.rstrip(":").strip()
        body = body.replace("\n", " ").strip()
        recommendations.append({"id": i, "title": title, "description": body})

    if not recommendations:
        current_rec = None
        for line in ai_text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.upper().startswith("RECOMMENDATION"):
                if current_rec:
                    recommendations.append(current_rec)
                title = re.sub(
                    r"RECOMMENDATION\s+\d+[:.\s]*",
                    "",
                    line,
                    flags=re.IGNORECASE,
                ).strip()
                current_rec = {
                    "id": len(recommendations) + 1,
                    "title": title,
                    "description": "",
                }
            elif current_rec is not None:
                current_rec["description"] += line + " "
        if current_rec:
            recommendations.append(current_rec)

    focus_area = ""
    focus_why = ""
    focus_match = re.search(
        r"FOCUS AREA:\s*(.+?)(?:WHY:|$)", ai_text, re.DOTALL | re.IGNORECASE
    )
    if focus_match:
        focus_area = focus_match.group(1).strip().split("\n")[0].strip()

    why_match = re.search(r"WHY:\s*(.+?)(?:\n|$)", ai_text, re.DOTALL | re.IGNORECASE)
    if why_match:
        focus_why = why_match.group(1).strip()

    return {
        "recommendations": recommendations,
        "focus_area": {"topic": focus_area, "reason": focus_why},
        "generated_at": timezone.now().isoformat(),
    }


def generate_study_recommendations(user):
    """Generate personalized study recommendations for a user."""
    history_payload = _build_quiz_history_payload(user)

    if history_payload is None:
        return {
            "error": "NOT_ENOUGH_DATA",
            "message": "Take a few quizzes first to get personalized recommendations!",
            "recommendations": [
                {
                    "id": 1,
                    "title": "Start Taking Quizzes",
                    "description": (
                        "Complete at least 2-3 quizzes on different topics to generate "
                        "personalized study recommendations based on your performance."
                    ),
                }
            ],
            "focus_area": {
                "topic": "Getting Started",
                "reason": "You need more quiz data for meaningful recommendations.",
            },
        }

    prompt = _build_recommendation_prompt(history_payload)
    ai_response, error = _call_gemini_for_recommendations(prompt)
    if ai_response is None:
        ai_response, error = _call_openai_for_recommendations(prompt)

    if ai_response is None:
        return {
            "error": "AI_API_ERROR",
            "message": "Unable to generate recommendations at this time. Please try again later.",
            "detail": error,
        }

    parsed = _parse_recommendations(ai_response)
    if parsed is None or not parsed.get("recommendations"):
        return {
            "error": "PARSE_ERROR",
            "message": "Received an unexpected response from the AI. Please try again.",
            "raw_response": ai_response,
        }

    return parsed


def check_rate_limit(user_id):
    """True if allowed; False if still within RATE_LIMIT_SECONDS."""
    now = time.time()
    last_request = _rate_limit_cache.get(user_id)
    if last_request and (now - last_request) < RATE_LIMIT_SECONDS:
        return False
    _rate_limit_cache[user_id] = now
    return True


def reset_rate_limit(user_id=None):
    """Test helper to clear rate-limit state."""
    if user_id is None:
        _rate_limit_cache.clear()
    else:
        _rate_limit_cache.pop(user_id, None)
