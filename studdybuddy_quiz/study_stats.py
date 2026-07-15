"""
Sprint 3 - User Story #10: User Study Statistics Dashboard
Author: Samuel Gamon

This module provides backend database queries and API endpoints for the
User Study Statistics Dashboard. It calculates aggregate metrics from the
user's quiz history and packages them into a clean JSON response for the
frontend profile page. Supports dynamic refresh after quiz completion.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta, timezone

study_stats_bp = Blueprint('study_stats', __name__, url_prefix='/api/stats')

# Database configuration (shared with quiz_history module)
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'aistudybuddy'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', '')
}


def get_db_connection():
    """Create and return a database connection."""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print(f"Database connection error: {str(e)}")
        return None


def get_user_dashboard_stats(user_id):
    """
    Calculate comprehensive dashboard statistics for a user.
    
    Args:
        user_id (int): The logged-in user's ID
    
    Returns:
        dict: Formatted dashboard statistics with properly rounded decimals
    """
    conn = get_db_connection()
    if not conn:
        # Return empty but valid stats structure on DB error
        return _empty_stats()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Basic aggregate stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_quizzes,
                    COALESCE(AVG(score_percentage), 0) as average_score,
                    COALESCE(MAX(score_percentage), 0) as best_score,
                    COALESCE(MIN(score_percentage), 0) as worst_score,
                    SUM(correct_count) as total_correct,
                    SUM(total_questions) as total_questions,
                    MAX(created_at) as last_quiz_date
                FROM quiz_results
                WHERE user_id = %s
            """, (user_id,))
            
            basic = cur.fetchone()
            total_quizzes = basic["total_quizzes"]
            
            # Handle empty history for brand new users
            if total_quizzes == 0:
                return _empty_stats()
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            cur.execute("""
                SELECT 
                    COUNT(*) as quizzes_this_week,
                    COALESCE(AVG(score_percentage), 0) as weekly_average
                FROM quiz_results
                WHERE user_id = %s AND created_at >= %s
            """, (user_id, week_ago))
            
            weekly = cur.fetchone()
            
            # Subject/topic breakdown (from quiz titles)
            cur.execute("""
                SELECT 
                    quiz_title,
                    COUNT(*) as times_taken,
                    COALESCE(AVG(score_percentage), 0) as avg_score
                FROM quiz_results
                WHERE user_id = %s
                GROUP BY quiz_title
                ORDER BY times_taken DESC
                LIMIT 5
            """, (user_id,))
            
            subject_breakdown = []
            for row in cur.fetchall():
                subject_breakdown.append({
                    "subject": row["quiz_title"],
                    "quizzes_taken": row["times_taken"],
                    "average_score": round(float(row["avg_score"]), 1)
                })
            
            # Recent quiz trend (last 10 quizzes for chart data)
            cur.execute("""
                SELECT 
                    id,
                    quiz_title,
                    score_percentage,
                    created_at
                FROM quiz_results
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (user_id,))
            
            recent_scores = []
            for row in reversed(cur.fetchall()):
                recent_scores.append({
                    "quiz_id": row["id"],
                    "quiz_title": row["quiz_title"],
                    "score": round(float(row["score_percentage"]), 1),
                    "date": row["created_at"].strftime("%Y-%m-%d")
                })
            
            # Calculate progress indicator (improvement trend)
            progress_status = _calculate_progress(recent_scores)
            
            # Build the clean dashboard response
            # Fix: round all decimals to 1 place to avoid formatting issues on frontend
            stats = {
                "overview": {
                    "total_quizzes_taken": total_quizzes,
                    "overall_average_score": round(float(basic["average_score"]), 1),
                    "best_score": round(float(basic["best_score"]), 1),
                    "worst_score": round(float(basic["worst_score"]), 1),
                    "total_correct_answers": basic["total_correct"] or 0,
                    "total_questions_answered": basic["total_questions"] or 0,
                    "overall_accuracy_rate": round(
                        (basic["total_correct"] / basic["total_questions"] * 100), 1
                    ) if basic["total_questions"] else 0.0,
                    "last_quiz_date": basic["last_quiz_date"].isoformat() if basic["last_quiz_date"] else None
                },
                "weekly_activity": {
                    "quizzes_this_week": weekly["quizzes_this_week"],
                    "weekly_average_score": round(float(weekly["weekly_average"]), 1)
                },
                "subject_breakdown": subject_breakdown,
                "score_trend": recent_scores,
                "progress_indicator": progress_status,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            return stats
            
    except psycopg2.Error as e:
        print(f"Error calculating dashboard stats: {str(e)}")
        return _empty_stats()
    finally:
        conn.close()


def _empty_stats():
    """
    Return an empty stats structure for brand new users with no quiz history.
    This prevents frontend crashes when a user has no data yet.
    """
    return {
        "overview": {
            "total_quizzes_taken": 0,
            "overall_average_score": 0.0,
            "best_score": 0.0,
            "worst_score": 0.0,
            "total_correct_answers": 0,
            "total_questions_answered": 0,
            "overall_accuracy_rate": 0.0,
            "last_quiz_date": None
        },
        "weekly_activity": {
            "quizzes_this_week": 0,
            "weekly_average_score": 0.0
        },
        "subject_breakdown": [],
        "score_trend": [],
        "progress_indicator": {
            "status": "new",
            "label": "Just Getting Started",
            "description": "Complete your first quiz to see your progress!",
            "trend_direction": "neutral"
        },
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


def _calculate_progress(recent_scores):
    """
    Calculate the user's progress trend based on recent quiz scores.
    
    Args:
        recent_scores (list): List of recent score entries
    
    Returns:
        dict: Progress indicator with status, label, and trend direction
    """
    if len(recent_scores) < 2:
        return {
            "status": "new",
            "label": "Just Getting Started" if not recent_scores else "First Quiz Complete!",
            "description": "Keep taking quizzes to track your progress." if not recent_scores else "Take more quizzes to see your trend!",
            "trend_direction": "neutral"
        }
    
    # Compare first half average vs second half average
    half = len(recent_scores) // 2
    first_half_avg = sum(s["score"] for s in recent_scores[:half]) / half if half > 0 else 0
    second_half_avg = sum(s["score"] for s in recent_scores[half:]) / (len(recent_scores) - half) if (len(recent_scores) - half) > 0 else 0
    
    diff = second_half_avg - first_half_avg
    
    if diff >= 10:
        return {
            "status": "improving",
            "label": "Improving",
            "description": f"Your scores are trending up by {round(diff, 1)} points! Keep it up!",
            "trend_direction": "up",
            "trend_value": round(diff, 1)
        }
    elif diff >= 5:
        return {
            "status": "improving_slightly",
            "label": "Getting Better",
            "description": f"You're showing improvement (+{round(diff, 1)} points).",
            "trend_direction": "up",
            "trend_value": round(diff, 1)
        }
    elif diff <= -10:
        return {
            "status": "declining",
            "label": "Needs Attention",
            "description": "Your recent scores have dropped. Consider reviewing past material.",
            "trend_direction": "down",
            "trend_value": round(diff, 1)
        }
    elif diff <= -5:
        return {
            "status": "declining_slightly",
            "label": "Slight Dip",
            "description": "A small decrease in scores. A quick review might help!",
            "trend_direction": "down",
            "trend_value": round(diff, 1)
        }
    else:
        return {
            "status": "steady",
            "label": "Steady",
            "description": "Your scores are holding steady. Keep practicing!",
            "trend_direction": "neutral",
            "trend_value": round(diff, 1)
        }


# Flask Routes

@study_stats_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """
    GET /api/stats/dashboard
    Fetch the complete study statistics dashboard for the logged-in user.
    
    Response: Comprehensive dashboard data formatted for frontend rendering.
    Safe to call even for brand new users with empty history.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in to view dashboard."}), 401
    
    stats = get_user_dashboard_stats(user_id)
    return jsonify(stats), 200


@study_stats_bp.route('/refresh', methods=['POST'])
def refresh_dashboard():
    """
    POST /api/stats/refresh
    Force a refresh of the dashboard stats after a new quiz is completed.
    This allows the frontend to dynamically update without a full page reload.
    
    Request body: {} (empty, uses session user_id)
    Response: Updated dashboard statistics
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in."}), 401
    
    # The stats are calculated fresh each time, so this returns the latest data
    stats = get_user_dashboard_stats(user_id)
    
    # Add a refresh timestamp to help frontend manage caching
    stats["refreshed_at"] = datetime.now(timezone.utc).isoformat()
    
    return jsonify(stats), 200


@study_stats_bp.route('/quick-summary', methods=['GET'])
def quick_summary():
    """
    GET /api/stats/quick-summary
    Get a minimal stats summary for display in compact UI areas
    (e.g., navbar dropdown, sidebar widget).
    
    Response: Minimal stats object with just key numbers
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in."}), 401
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"total_quizzes": 0, "average_score": 0.0}), 200
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_quizzes,
                    COALESCE(AVG(score_percentage), 0) as average_score
                FROM quiz_results
                WHERE user_id = %s
            """, (user_id,))
            
            result = cur.fetchone()
            
            return jsonify({
                "total_quizzes": result["total_quizzes"],
                "average_score": round(float(result["average_score"]), 1)
            }), 200
            
    except psycopg2.Error as e:
        return jsonify({"total_quizzes": 0, "average_score": 0.0}), 200
    finally:
        conn.close()
