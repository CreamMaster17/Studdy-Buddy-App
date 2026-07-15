"""
Sprint 1 - User Story #3: User Input into Practice Quizzes
Author: Samuel Gamon

This module handles AI-powered quiz generation from user text notes.
It provides Flask routes for generating multiple-choice quizzes and grading user responses.
The AI prompt is carefully engineered to return strict JSON-formatted quiz data.
"""

import os
import json
import re
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timezone

# Try to import Google Gemini API (primary), fallback to OpenAI
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

quiz_gen_bp = Blueprint('quiz_generator', __name__, url_prefix='/api/quiz')

# Configure AI APIs
if GEMINI_AVAILABLE:
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)

if OPENAI_AVAILABLE:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY

# AI Prompt template for strict JSON output
QUIZ_GENERATION_PROMPT = """You are an expert educational AI assistant. Your task is to generate multiple-choice quiz questions based on the study notes provided below.

STRICT REQUIREMENTS:
1. Generate exactly {num_questions} multiple-choice questions based on the provided notes.
2. Each question must have exactly 4 options (A, B, C, D).
3. Only ONE option should be correct.
4. Return your response ONLY as a valid JSON object. No additional text, no explanations, no markdown formatting.
5. The JSON must follow this exact structure:

{{
  "quiz_title": "Brief descriptive title based on the notes topic",
  "total_questions": {num_questions},
  "questions": [
    {{
      "question_id": 1,
      "question_text": "The actual question text?",
      "options": {{
        "A": "First option text",
        "B": "Second option text",
        "C": "Third option text",
        "D": "Fourth option text"
      }},
      "correct_answer": "A",
      "explanation": "Brief explanation of why this answer is correct"
    }}
  ]
}}

STUDY NOTES:
{notes}

Remember: Return ONLY the JSON object. No other text."""


def _call_gemini_api(prompt):
    """Call Google Gemini API to generate quiz content."""
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return None
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=2048
            )
        )
        return response.text
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        return None


def _call_openai_api(prompt):
    """Call OpenAI API to generate quiz content."""
    if not OPENAI_AVAILABLE or not OPENAI_API_KEY:
        return None
    
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful educational AI that generates quiz questions. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None


def _parse_ai_response(ai_response):
    """
    Parse AI response to extract valid JSON.
    Handles cases where AI might wrap JSON in markdown code blocks
    or include extra conversational text.
    """
    if not ai_response:
        return None
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', ai_response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object
        json_match = re.search(r'(\{.*\})', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = ai_response
    
    try:
        parsed = json.loads(json_str)
        return parsed
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        return None


def generate_quiz_from_notes(notes_text, num_questions=5):
    """
    Generate a multiple-choice quiz from study notes using AI.
    
    Args:
        notes_text (str): The user's study notes
        num_questions (int): Number of questions to generate (default: 5)
    
    Returns:
        dict: Parsed JSON quiz data with questions, options, and correct answers
    """
    prompt = QUIZ_GENERATION_PROMPT.format(
        num_questions=num_questions,
        notes=notes_text
    )
    
    # Try Gemini first (team's preferred API), fallback to OpenAI
    ai_response = _call_gemini_api(prompt)
    if ai_response is None:
        ai_response = _call_openai_api(prompt)
    
    if ai_response is None:
        return {
            "error": "Failed to generate quiz. AI API unavailable."
        }
    
    quiz_data = _parse_ai_response(ai_response)
    
    if quiz_data is None:
        return {
            "error": "Failed to parse AI response into valid quiz format."
        }
    
    # Validate the quiz structure
    if "questions" not in quiz_data:
        return {
            "error": "Invalid quiz format: missing 'questions' array."
        }
    
    # Ensure each question has required fields
    for i, q in enumerate(quiz_data["questions"]):
        q["question_id"] = i + 1  # Ensure consistent IDs
        if "explanation" not in q:
            q["explanation"] = ""
    
    # Add metadata
    quiz_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    quiz_data["source_notes_length"] = len(notes_text)
    
    return quiz_data


def grade_quiz_submission(quiz_data, user_answers):
    """
    Grade a user's quiz submission against the correct answers.
    
    Args:
        quiz_data (dict): The original quiz data with correct answers
        user_answers (dict): Mapping of question_id to user's selected option (e.g., {"1": "A", "2": "C"})
    
    Returns:
        dict: Grading results with score, correct count, and per-question feedback
    """
    if not quiz_data or "questions" not in quiz_data:
        return {"error": "Invalid quiz data provided for grading."}
    
    results = {
        "total_questions": len(quiz_data["questions"]),
        "correct_count": 0,
        "incorrect_count": 0,
        "unanswered_count": 0,
        "score_percentage": 0.0,
        "question_results": [],
        "graded_at": datetime.now(timezone.utc).isoformat()
    }
    
    for question in quiz_data["questions"]:
        q_id = str(question["question_id"])
        correct_answer = question.get("correct_answer", "")
        user_answer = user_answers.get(q_id, "")
        
        if not user_answer:
            is_correct = False
            results["unanswered_count"] += 1
        elif user_answer.upper() == correct_answer.upper():
            is_correct = True
            results["correct_count"] += 1
        else:
            is_correct = False
            results["incorrect_count"] += 1
        
        results["question_results"].append({
            "question_id": question["question_id"],
            "question_text": question["question_text"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": question.get("explanation", "")
        })
    
    # Calculate percentage
    total = results["total_questions"]
    if total > 0:
        results["score_percentage"] = round((results["correct_count"] / total) * 100, 1)
    
    return results


# Flask Routes

@quiz_gen_bp.route('/generate', methods=['POST'])
def generate_quiz():
    """
    POST /api/quiz/generate
    Generate a quiz from provided study notes.
    
    Request body: {"notes": "study notes text here", "num_questions": 5}
    Response: JSON quiz data with questions and options
    """
    data = request.get_json()
    
    if not data or 'notes' not in data:
        return jsonify({"error": "Missing required field: 'notes'"}), 400
    
    notes_text = data['notes']
    num_questions = data.get('num_questions', 5)
    
    # Validate input
    if not notes_text or len(notes_text.strip()) < 10:
        return jsonify({"error": "Notes text is too short. Minimum 10 characters required."}), 400
    
    if not isinstance(num_questions, int) or num_questions < 1 or num_questions > 20:
        return jsonify({"error": "num_questions must be an integer between 1 and 20."}), 400
    
    quiz_data = generate_quiz_from_notes(notes_text, num_questions)
    
    if "error" in quiz_data:
        return jsonify(quiz_data), 500
    
    # Store the generated quiz in session for grading (without correct answers exposed)
    session['last_generated_quiz'] = quiz_data
    
    # Return quiz with correct answers hidden (for frontend display)
    safe_quiz = {
        "quiz_title": quiz_data.get("quiz_title", "Generated Quiz"),
        "total_questions": quiz_data.get("total_questions", 0),
        "questions": [
            {
                "question_id": q["question_id"],
                "question_text": q["question_text"],
                "options": q["options"]
            }
            for q in quiz_data.get("questions", [])
        ],
        "generated_at": quiz_data.get("generated_at")
    }
    
    return jsonify(safe_quiz), 200


@quiz_gen_bp.route('/grade', methods=['POST'])
def grade_quiz():
    """
    POST /api/quiz/grade
    Grade a user's quiz submission.
    
    Request body: {"answers": {"1": "A", "2": "C", ...}}
    Response: Grading results with score and feedback
    """
    data = request.get_json()
    
    if not data or 'answers' not in data:
        return jsonify({"error": "Missing required field: 'answers'"}), 400
    
    # Retrieve the last generated quiz from session
    quiz_data = session.get('last_generated_quiz')
    if not quiz_data:
        return jsonify({"error": "No quiz found. Please generate a quiz first."}), 400
    
    user_answers = data['answers']
    
    if not isinstance(user_answers, dict):
        return jsonify({"error": "'answers' must be an object mapping question IDs to selected options."}), 400
    
    results = grade_quiz_submission(quiz_data, user_answers)
    
    if "error" in results:
        return jsonify(results), 500
    
    # Store the graded result in session for history saving
    session['last_graded_result'] = {
        "quiz_title": quiz_data.get("quiz_title", "Untitled Quiz"),
        "results": results
    }
    
    return jsonify(results), 200


@quiz_gen_bp.route('/submit-and-save', methods=['POST'])
def submit_and_save_quiz():
    """
    POST /api/quiz/submit-and-save
    Grade a quiz and automatically save it to the user's history.
    Requires user to be logged in (user_id in session).
    
    Request body: {"answers": {"1": "A", "2": "C", ...}}
    Response: Grading results with confirmation of save
    """
    data = request.get_json()
    
    if not data or 'answers' not in data:
        return jsonify({"error": "Missing required field: 'answers'"}), 400
    
    # Check if user is logged in
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "User must be logged in to save quiz history."}), 401
    
    # Retrieve the last generated quiz from session
    quiz_data = session.get('last_generated_quiz')
    if not quiz_data:
        return jsonify({"error": "No quiz found. Please generate a quiz first."}), 400
    
    user_answers = data['answers']
    results = grade_quiz_submission(quiz_data, user_answers)
    
    if "error" in results:
        return jsonify(results), 500
    
    # Save to user's quiz history (if database is available)
    try:
        from quiz_history import save_quiz_result
        save_result = save_quiz_result(
            user_id=user_id,
            quiz_title=quiz_data.get("quiz_title", "Untitled Quiz"),
            score_percentage=results["score_percentage"],
            correct_count=results["correct_count"],
            total_questions=results["total_questions"],
            question_results=results["question_results"]
        )
        results["saved_to_history"] = save_result
    except ImportError:
        results["saved_to_history"] = False
        results["save_note"] = "Quiz history module not available."
    except Exception as e:
        results["saved_to_history"] = False
        results["save_error"] = str(e)
    
    return jsonify(results), 200
