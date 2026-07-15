"""
Sprint 4 - User Story #14: Personalized AI Study Recommendations
Author: Samuel Gamon

This module analyzes a user's quiz statistics and history to generate
personalized study recommendations using AI. It feeds historical quiz data
to the AI model and parses the response into clean, actionable recommendations
displayed on the user's dashboard.

Includes robust error handling for API downtime, empty histories, and rate limiting.
"""

import os
import re
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta, timezone

# Try to import AI APIs (same pattern as quiz_generator)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

study_rec_bp = Blueprint('study_recommendations', __name__, url_prefix='/api/recommendations')

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'aistudybuddy'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', '')
}

# AI API configuration
if GEMINI_AVAILABLE:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)

if OPENAI_AVAILABLE:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY

# Simple in-memory rate limiter: {user_id: last_request_timestamp}
_rate_limit_cache = {}
RATE_LIMIT_SECONDS = 30  # Minimum seconds between recommendation requests per user


def get_db_connection():
    """Create and return a database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Database connection error: {str(e)}")
        return None


def _build_quiz_history_payload(user_id):
    """
    Query the user's quiz history and structure it into a concise
    data payload for the AI recommendation prompt.
    
    Args:
        user_id (int): The logged-in user's ID
    
    Returns:
        dict: Structured quiz history data, or None if no history exists
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get overall stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_quizzes,
                    COALESCE(AVG(score_percentage), 0) as average_score,
                    MAX(created_at) as last_quiz_date
                FROM quiz_results
                WHERE user_id = %s
            """, (user_id,))
            
            overall = cur.fetchone()
            
            if overall["total_quizzes"] == 0:
                return None  # No quiz history yet
            
            # Get per-subject performance (top subjects)
            cur.execute("""
                SELECT 
                    quiz_title as subject,
                    COUNT(*) as times_taken,
                    COALESCE(AVG(score_percentage), 0) as average_score,
                    COALESCE(STDDEV(score_percentage), 0) as score_variance
                FROM quiz_results
                WHERE user_id = %s
                GROUP BY quiz_title
                ORDER BY times_taken DESC, average_score ASC
                LIMIT 8
            """, (user_id,))
            
            subjects = []
            for row in cur.fetchall():
                subjects.append({
                    "subject": row["subject"],
                    "times_taken": row["times_taken"],
                    "average_score": round(float(row["average_score"]), 1),
                    "consistency": _variance_to_consistency(row["score_variance"])
                })
            
            # Get recent individual quiz results (last 10)
            cur.execute("""
                SELECT 
                    quiz_title,
                    score_percentage,
                    correct_count,
                    total_questions,
                    created_at
                FROM quiz_results
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (user_id,))
            
            recent_quizzes = []
            for row in cur.fetchall():
                recent_quizzes.append({
                    "subject": row["quiz_title"],
                    "score": round(float(row["score_percentage"]), 1),
                    "correct": row["correct_count"],
                    "total": row["total_questions"],
                    "date": row["created_at"].strftime("%Y-%m-%d")
                })
            
            # Identify weak areas (subjects with avg score below 70%)
            weak_areas = [s for s in subjects if s["average_score"] < 70.0]
            
            # Identify strong areas (subjects with avg score above 85%)
            strong_areas = [s for s in subjects if s["average_score"] >= 85.0]
            
            return {
                "overall_stats": {
                    "total_quizzes": overall["total_quizzes"],
                    "average_score": round(float(overall["average_score"]), 1),
                    "last_quiz_date": overall["last_quiz_date"].strftime("%Y-%m-%d") if overall["last_quiz_date"] else None
                },
                "subject_performance": subjects,
                "recent_quizzes": recent_quizzes,
                "weak_areas": weak_areas,
                "strong_areas": strong_areas
            }
            
    except psycopg2.Error as e:
        print(f"Error building history payload: {str(e)}")
        return None
    finally:
        conn.close()


def _variance_to_consistency(stddev):
    """Convert standard deviation to a human-readable consistency label."""
    if stddev is None:
        return "unknown"
    val = float(stddev)
    if val < 10:
        return "very_consistent"
    elif val < 20:
        return "consistent"
    elif val < 30:
        return "variable"
    else:
        return "inconsistent"


def _build_recommendation_prompt(history_payload):
    """
    Build a concise AI prompt from the structured quiz history data.
    
    Args:
        history_payload (dict): Structured quiz history from _build_quiz_history_payload
    
    Returns:
        str: Formatted prompt for the AI model
    """
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
        prompt += f"- {s['subject']}: {s['average_score']}% average over {s['times_taken']} attempt(s)\n"
    
    if weak_areas:
        prompt += f"\nWEAKEST AREAS (below 70%):\n"
        for w in weak_areas:
            prompt += f"- {w['subject']}: {w['average_score']}%\n"
    
    if strong_areas:
        prompt += f"\nSTRONGEST AREAS (above 85%):\n"
        for s in strong_areas:
            prompt += f"- {s['subject']}: {s['average_score']}%\n"
    
    prompt += f"\nRECENT QUIZZES:\n"
    for r in recent[:5]:
        prompt += f"- {r['subject']}: {r['score']}% ({r['correct']}/{r['total']}) on {r['date']}\n"
    
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
    """Call Google Gemini API to generate study recommendations."""
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return None, "Gemini API not configured"
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                max_output_tokens=1024
            )
        )
        return response.text, None
    except Exception as e:
        return None, f"Gemini API error: {str(e)}"


def _call_openai_for_recommendations(prompt):
    """Call OpenAI API to generate study recommendations."""
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        return None, "OpenAI API not configured"
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert academic coach. Provide concise, actionable study recommendations based on quiz performance data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1024
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"OpenAI API error: {str(e)}"


def _parse_recommendations(ai_text):
    """
    Parse the AI's text response into a structured format.
    Handles inconsistent text formatting from the AI.
    
    Args:
        ai_text (str): Raw text response from AI
    
    Returns:
        dict: Structured recommendations with list and focus area
    """
    if not ai_text:
        return None
    
    recommendations = []
    
    # Extract recommendations using regex
    # Pattern matches "RECOMMENDATION N: Title" followed by text
    rec_pattern = r'RECOMMENDATION\s+\d+:\s*(.+?)(?=RECOMMENDATION|FOCUS AREA|$)'
    rec_matches = re.findall(rec_pattern, ai_text, re.DOTALL | re.IGNORECASE)
    
    for i, match in enumerate(rec_matches, 1):
        # Split title from body
        lines = match.strip().split('\n', 1)
        title = lines[0].strip() if lines else f"Recommendation {i}"
        body = lines[1].strip() if len(lines) > 1 else ""
        
        # Clean up the text
        title = title.rstrip(':').strip()
        body = body.replace('\n', ' ').strip()
        
        recommendations.append({
            "id": i,
            "title": title,
            "description": body
        })
    
    # If regex didn't work, try line-by-line parsing as fallback
    if not recommendations:
        lines = ai_text.strip().split('\n')
        current_rec = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.upper().startswith('RECOMMENDATION'):
                if current_rec:
                    recommendations.append(current_rec)
                title = re.sub(r'RECOMMENDATION\s+\d+[:.\s]*', '', line, flags=re.IGNORECASE).strip()
                current_rec = {
                    "id": len(recommendations) + 1,
                    "title": title,
                    "description": ""
                }
            elif current_rec is not None:
                current_rec["description"] += line + " "
        if current_rec:
            recommendations.append(current_rec)
    
    # Extract focus area
    focus_area = ""
    focus_why = ""
    focus_match = re.search(r'FOCUS AREA:\s*(.+?)(?:WHY:|$)', ai_text, re.DOTALL | re.IGNORECASE)
    if focus_match:
        focus_area = focus_match.group(1).strip().split('\n')[0].strip()
    
    why_match = re.search(r'WHY:\s*(.+?)(?:\n|$)', ai_text, re.DOTALL | re.IGNORECASE)
    if why_match:
        focus_why = why_match.group(1).strip()
    
    return {
        "recommendations": recommendations,
        "focus_area": {
            "topic": focus_area,
            "reason": focus_why
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


def generate_study_recommendations(user_id):
    """
    Main function to generate personalized study recommendations.
    
    Args:
        user_id (int): The logged-in user's ID
    
    Returns:
        dict: Structured recommendations, or error info
    """
    # Step 1: Build the history payload
    history_payload = _build_quiz_history_payload(user_id)
    
    if history_payload is None:
        return {
            "error": "NOT_ENOUGH_DATA",
            "message": "Take a few quizzes first to get personalized recommendations!",
            "recommendations": [
                {
                    "id": 1,
                    "title": "Start Taking Quizzes",
                    "description": "Complete at least 2-3 quizzes on different topics to generate personalized study recommendations based on your performance."
                }
            ],
            "focus_area": {
                "topic": "Getting Started",
                "reason": "You need more quiz data for meaningful recommendations."
            }
        }
    
    # Step 2: Build the prompt
    prompt = _build_recommendation_prompt(history_payload)
    
    # Step 3: Call AI API (Gemini first, fallback to OpenAI)
    ai_response, error = _call_gemini_for_recommendations(prompt)
    if ai_response is None:
        ai_response, error = _call_openai_for_recommendations(prompt)
    
    if ai_response is None:
        return {
            "error": "AI_API_ERROR",
            "message": "Unable to generate recommendations at this time. Please try again later.",
            "detail": error
        }
    
    # Step 4: Parse the response
    parsed = _parse_recommendations(ai_response)
    
    if parsed is None or not parsed.get("recommendations"):
        return {
            "error": "PARSE_ERROR",
            "message": "Received an unexpected response from the AI. Please try again.",
            "raw_response": ai_response
        }
    
    return parsed


def check_rate_limit(user_id):
    """
    Check if the user has exceeded the rate limit for recommendation requests.
    
    Args:
        user_id (int): The user's ID
    
    Returns:
        bool: True if request is allowed, False if rate limited
    """
    now = time.time()
    last_request = _rate_limit_cache.get(user_id)
    
    if last_request and (now - last_request) < RATE_LIMIT_SECONDS:
        return False
    
    _rate_limit_cache[user_id] = now
    return True


# Flask Routes

@study_rec_bp.route('/generate', methods=['POST'])
def get_recommendations():
    """
    POST /api/recommendations/generate
    Generate personalized study recommendations for the logged-in user.
    
    Includes rate limiting to prevent excessive API calls.
    
    Response: Structured recommendations with actionable advice
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in."}), 401
    
    # Check rate limit
    if not check_rate_limit(user_id):
        return jsonify({
            "error": "RATE_LIMITED",
            "message": f"Please wait {RATE_LIMIT_SECONDS} seconds between recommendation requests.",
            "retry_after": RATE_LIMIT_SECONDS
        }), 429
    
    try:
        result = generate_study_recommendations(user_id)
        
        if "error" in result and result["error"] in ("AI_API_ERROR", "PARSE_ERROR"):
            # Return 503 for API errors (service temporarily unavailable)
            status_code = 503 if result["error"] == "AI_API_ERROR" else 500
            return jsonify(result), status_code
        
        # Store in session for potential caching
        session['last_recommendations'] = result
        
        return jsonify(result), 200
        
    except Exception as e:
        # Catch-all for unexpected errors
        return jsonify({
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred while generating recommendations.",
            "detail": str(e)
        }), 500


@study_rec_bp.route('/cached', methods=['GET'])
def get_cached_recommendations():
    """
    GET /api/recommendations/cached
    Retrieve the last generated recommendations from session cache.
    Useful for dashboard loading without hitting the AI API again.
    
    Response: Cached recommendations or empty if none exist
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in."}), 401
    
    cached = session.get('last_recommendations')
    
    if not cached:
        return jsonify({
            "message": "No cached recommendations. Generate new ones first.",
            "recommendations": []
        }), 200
    
    return jsonify(cached), 200


@study_rec_bp.route('/status', methods=['GET'])
def api_status():
    """
    GET /api/recommendations/status
    Check if the recommendation AI APIs are available.
    Useful for the frontend to show/hide the recommendations feature.
    
    Response: API availability status
    """
    gemini_ok = GEMINI_AVAILABLE and bool(GEMINI_API_KEY)
    openai_ok = OPENAI_AVAILABLE and bool(OPENAI_API_KEY)
    
    return jsonify({
        "gemini_available": gemini_ok,
        "openai_available": openai_ok,
        "any_api_available": gemini_ok or openai_ok,
        "rate_limit_seconds": RATE_LIMIT_SECONDS
    }), 200
