"""
Sprint 2 - User Story #6: Quiz History and Progress Tracking
Author: Samuel Gamon

This module manages saving and retrieving a user's quiz history and scores.
It provides database models, Flask routes for persistence, and clean JSON responses.
Quiz history is linked to specific user accounts via session-based user IDs.
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Blueprint, request, jsonify, session, g
from datetime import datetime, timezone

quiz_history_bp = Blueprint('quiz_history', __name__, url_prefix='/api/history')

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': os.environ.get('DB_PORT', '5432'),
    'database': os.environ.get('DB_NAME', 'aistudybuddy'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', '')
}


def get_db_connection():
    """Create and return a database connection."""
    if 'db_conn' not in g:
        try:
            g.db_conn = psycopg2.connect(**DB_CONFIG)
        except psycopg2.Error as e:
            print(f"Database connection error: {str(e)}")
            return None
    return g.db_conn


def close_db_connection(e=None):
    """Close the database connection at the end of request."""
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()


def init_quiz_tables():
    """
    Initialize the quiz-related database tables.
    Creates tables if they don't exist.
    """
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cur:
            # Table for quiz results/sessions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    quiz_title VARCHAR(255) NOT NULL,
                    score_percentage DECIMAL(5,2) NOT NULL,
                    correct_count INTEGER NOT NULL,
                    total_questions INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for individual question responses within a quiz
            cur.execute("""
                CREATE TABLE IF NOT EXISTS quiz_question_results (
                    id SERIAL PRIMARY KEY,
                    quiz_result_id INTEGER REFERENCES quiz_results(id) ON DELETE CASCADE,
                    question_id INTEGER NOT NULL,
                    question_text TEXT NOT NULL,
                    user_answer VARCHAR(10) NOT NULL,
                    correct_answer VARCHAR(10) NOT NULL,
                    is_correct BOOLEAN NOT NULL,
                    explanation TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table for generated quizzes (snapshots)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS generated_quizzes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    quiz_title VARCHAR(255) NOT NULL,
                    quiz_data JSONB NOT NULL,
                    source_notes_length INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for faster user-specific queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id 
                ON quiz_results(user_id)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_quiz_question_results_quiz_id 
                ON quiz_question_results(quiz_result_id)
            """)
            
            conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Error initializing quiz tables: {str(e)}")
        conn.rollback()
        return False


def save_quiz_result(user_id, quiz_title, score_percentage, correct_count, 
                     total_questions, question_results=None):
    """
    Save a completed quiz result to the database.
    
    Args:
        user_id (int): The logged-in user's ID
        quiz_title (str): Title of the quiz
        score_percentage (float): User's score as percentage
        correct_count (int): Number of correct answers
        total_questions (int): Total number of questions
        question_results (list, optional): Detailed per-question results
    
    Returns:
        dict: Result with success status and quiz_result_id
    """
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed"}
    
    try:
        with conn.cursor() as cur:
            # Insert the main quiz result
            cur.execute("""
                INSERT INTO quiz_results 
                (user_id, quiz_title, score_percentage, correct_count, total_questions)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (user_id, quiz_title, score_percentage, correct_count, total_questions))
            
            quiz_result_id = cur.fetchone()[0]
            
            # Insert individual question results if provided
            if question_results:
                for qr in question_results:
                    cur.execute("""
                        INSERT INTO quiz_question_results
                        (quiz_result_id, question_id, question_text, user_answer, 
                         correct_answer, is_correct, explanation)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        quiz_result_id,
                        qr.get("question_id", 0),
                        qr.get("question_text", ""),
                        qr.get("user_answer", ""),
                        qr.get("correct_answer", ""),
                        qr.get("is_correct", False),
                        qr.get("explanation", "")
                    ))
            
            conn.commit()
            
            return {
                "success": True,
                "quiz_result_id": quiz_result_id,
                "message": "Quiz result saved successfully."
            }
            
    except psycopg2.Error as e:
        conn.rollback()
        return {"success": False, "error": f"Database error: {str(e)}"}


def get_user_quiz_history(user_id, limit=50, offset=0):
    """
    Fetch a user's quiz history from the database.
    
    Args:
        user_id (int): The logged-in user's ID
        limit (int): Maximum number of results to return
        offset (int): Number of results to skip (for pagination)
    
    Returns:
        list: Quiz history entries formatted as clean JSON
    """
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, quiz_title, score_percentage, correct_count, 
                       total_questions, created_at
                FROM quiz_results
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            
            results = cur.fetchall()
            
            # Format the results into clean JSON
            history = []
            for row in results:
                history.append({
                    "quiz_result_id": row["id"],
                    "quiz_title": row["quiz_title"],
                    "score_percentage": float(row["score_percentage"]),
                    "correct_count": row["correct_count"],
                    "total_questions": row["total_questions"],
                    "taken_at": row["created_at"].isoformat() if row["created_at"] else None
                })
            
            return history
            
    except psycopg2.Error as e:
        print(f"Error fetching quiz history: {str(e)}")
        return []


def get_quiz_result_detail(quiz_result_id, user_id):
    """
    Fetch detailed results for a specific quiz attempt.
    
    Args:
        quiz_result_id (int): The ID of the quiz result
        user_id (int): The logged-in user's ID (for verification)
    
    Returns:
        dict: Detailed quiz result with per-question breakdown
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get main quiz result
            cur.execute("""
                SELECT id, quiz_title, score_percentage, correct_count,
                       total_questions, created_at
                FROM quiz_results
                WHERE id = %s AND user_id = %s
            """, (quiz_result_id, user_id))
            
            result = cur.fetchone()
            if not result:
                return None
            
            # Get question-level details
            cur.execute("""
                SELECT question_id, question_text, user_answer,
                       correct_answer, is_correct, explanation
                FROM quiz_question_results
                WHERE quiz_result_id = %s
                ORDER BY question_id
            """, (quiz_result_id,))
            
            questions = cur.fetchall()
            
            return {
                "quiz_result_id": result["id"],
                "quiz_title": result["quiz_title"],
                "score_percentage": float(result["score_percentage"]),
                "correct_count": result["correct_count"],
                "total_questions": result["total_questions"],
                "taken_at": result["created_at"].isoformat() if result["created_at"] else None,
                "questions": [
                    {
                        "question_id": q["question_id"],
                        "question_text": q["question_text"],
                        "user_answer": q["user_answer"],
                        "correct_answer": q["correct_answer"],
                        "is_correct": q["is_correct"],
                        "explanation": q["explanation"]
                    }
                    for q in questions
                ]
            }
            
    except psycopg2.Error as e:
        print(f"Error fetching quiz detail: {str(e)}")
        return None


def get_user_quiz_stats(user_id):
    """
    Get aggregate statistics for a user's quiz history.
    
    Args:
        user_id (int): The logged-in user's ID
    
    Returns:
        dict: Aggregate statistics (total quizzes, average score, best score, etc.)
    """
    conn = get_db_connection()
    if not conn:
        return {}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_quizzes,
                    AVG(score_percentage) as average_score,
                    MAX(score_percentage) as best_score,
                    MIN(score_percentage) as worst_score,
                    SUM(correct_count) as total_correct_answers,
                    SUM(total_questions) as total_questions_answered
                FROM quiz_results
                WHERE user_id = %s
            """, (user_id,))
            
            result = cur.fetchone()
            
            if not result or result["total_quizzes"] == 0:
                return {
                    "total_quizzes": 0,
                    "average_score": 0.0,
                    "best_score": 0.0,
                    "worst_score": 0.0,
                    "total_correct_answers": 0,
                    "total_questions_answered": 0
                }
            
            return {
                "total_quizzes": result["total_quizzes"],
                "average_score": round(float(result["average_score"]), 1),
                "best_score": round(float(result["best_score"]), 1),
                "worst_score": round(float(result["worst_score"]), 1),
                "total_correct_answers": result["total_correct_answers"],
                "total_questions_answered": result["total_questions_answered"]
            }
            
    except psycopg2.Error as e:
        print(f"Error fetching quiz stats: {str(e)}")
        return {}


# Flask Routes

@quiz_history_bp.route('/save', methods=['POST'])
def save_quiz():
    """
    POST /api/history/save
    Save a quiz result to the user's history.
    
    Request body: {
        "quiz_title": "Quiz Title",
        "score_percentage": 80.0,
        "correct_count": 4,
        "total_questions": 5,
        "question_results": [...]
    }
    Response: Success confirmation with quiz_result_id
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in to save quiz history."}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided."}), 400
    
    quiz_title = data.get('quiz_title', 'Untitled Quiz')
    score_percentage = data.get('score_percentage', 0.0)
    correct_count = data.get('correct_count', 0)
    total_questions = data.get('total_questions', 0)
    question_results = data.get('question_results', [])
    
    result = save_quiz_result(
        user_id=user_id,
        quiz_title=quiz_title,
        score_percentage=score_percentage,
        correct_count=correct_count,
        total_questions=total_questions,
        question_results=question_results
    )
    
    if result.get("success"):
        return jsonify(result), 201
    else:
        return jsonify(result), 500


@quiz_history_bp.route('/list', methods=['GET'])
def list_history():
    """
    GET /api/history/list
    Get the logged-in user's quiz history.
    
    Query params: ?limit=50&offset=0
    Response: Array of quiz history entries
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in to view quiz history."}), 401
    
    # Handle edge case: brand new user with empty history
    # Return empty array gracefully instead of error
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate pagination params
        if limit < 1 or limit > 100:
            limit = 50
        if offset < 0:
            offset = 0
        
        history = get_user_quiz_history(user_id, limit=limit, offset=offset)
        
        return jsonify({
            "history": history,
            "total_count": len(history),
            "limit": limit,
            "offset": offset
        }), 200
        
    except Exception as e:
        # Graceful fallback for edge cases
        return jsonify({
            "history": [],
            "total_count": 0,
            "limit": 50,
            "offset": 0,
            "note": "No quiz history found."
        }), 200


@quiz_history_bp.route('/detail/<int:quiz_result_id>', methods=['GET'])
def quiz_detail(quiz_result_id):
    """
    GET /api/history/detail/<quiz_result_id>
    Get detailed results for a specific quiz attempt.
    
    Response: Detailed quiz result with per-question breakdown
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in."}), 401
    
    detail = get_quiz_result_detail(quiz_result_id, user_id)
    
    if detail is None:
        return jsonify({"error": "Quiz result not found."}), 404
    
    return jsonify(detail), 200


@quiz_history_bp.route('/stats', methods=['GET'])
def user_stats():
    """
    GET /api/history/stats
    Get aggregate quiz statistics for the logged-in user.
    
    Response: Aggregate statistics object
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in."}), 401
    
    stats = get_user_quiz_stats(user_id)
    return jsonify(stats), 200
