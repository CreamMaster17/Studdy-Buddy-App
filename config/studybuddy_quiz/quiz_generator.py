"""
Sprint 1 / Sprint 5 - AI Quiz Generation & Grading
Author: Samuel Gamon

Generates multiple-choice quizzes from study notes and grades submissions.
Sprint 5: tightened prompt + more robust JSON parsing for variable note lengths.
"""

import json
import os
import re
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Try Google Gemini first, fallback to OpenAI
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

# Sprint 5 tightened prompt: strict JSON, handles short/long notes
QUIZ_GENERATION_PROMPT = """You are an expert educational AI assistant. Generate multiple-choice quiz questions from the study notes below.

STRICT REQUIREMENTS:
1. Generate exactly {num_questions} multiple-choice questions grounded ONLY in the notes.
2. Each question must have exactly 4 options labeled A, B, C, D.
3. Exactly ONE option is correct; set "correct_answer" to that letter.
4. If notes are short, still produce {num_questions} questions by focusing on key facts (do not invent unrelated topics).
5. If notes are long, prioritize the most important concepts; avoid trivia from footnotes.
6. Return ONLY a valid JSON object. No markdown fences, no commentary, no trailing text.
7. Use this exact JSON structure:

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

Return ONLY the JSON object."""


def _call_gemini_api(prompt):
    """Call Google Gemini API to generate quiz content."""
    if not GEMINI_AVAILABLE or GEMINI_CLIENT is None:
        return None

    try:
        response = GEMINI_CLIENT.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 2048,
            },
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
                {
                    "role": "system",
                    "content": (
                        "You are a helpful educational AI that generates quiz questions. "
                        "Always return valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI API error: {str(e)}")
        return None


def _parse_ai_response(ai_response):
    """
    Parse AI response into JSON.
    Handles markdown fences and extra conversational text around the object.
    """
    if not ai_response:
        return None

    text = ai_response.strip()

    # Prefer fenced JSON blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # First balanced-looking object (greedy across newlines)
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = text

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Last resort: trim to outermost braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                return None
        print("JSON parsing error: no JSON object found")
        return None


def _validate_question(question):
    """Ensure a question has options A-D and a valid correct_answer."""
    options = question.get("options")
    if not isinstance(options, dict):
        return False
    for key in ("A", "B", "C", "D"):
        if key not in options or not str(options[key]).strip():
            return False
    answer = str(question.get("correct_answer", "")).strip().upper()
    return answer in ("A", "B", "C", "D")


def generate_quiz_from_notes(notes_text, num_questions=5):
    """
    Generate a multiple-choice quiz from study notes using AI.

    Returns:
        dict: Quiz data, or {"error": "..."} on failure
    """
    prompt = QUIZ_GENERATION_PROMPT.format(
        num_questions=num_questions,
        notes=notes_text,
    )

    ai_response = _call_gemini_api(prompt)
    if ai_response is None:
        ai_response = _call_openai_api(prompt)

    if ai_response is None:
        return {"error": "Failed to generate quiz. AI API unavailable."}

    quiz_data = _parse_ai_response(ai_response)
    if quiz_data is None:
        return {"error": "Failed to parse AI response into valid quiz format."}

    if "questions" not in quiz_data or not isinstance(quiz_data["questions"], list):
        return {"error": "Invalid quiz format: missing 'questions' array."}

    cleaned = []
    for i, q in enumerate(quiz_data["questions"]):
        if not isinstance(q, dict):
            continue
        q["question_id"] = i + 1
        if "explanation" not in q:
            q["explanation"] = ""
        if "correct_answer" in q:
            q["correct_answer"] = str(q["correct_answer"]).strip().upper()
        if _validate_question(q):
            cleaned.append(q)

    if not cleaned:
        return {"error": "Invalid quiz format: no valid questions with A-D options."}

    quiz_data["questions"] = cleaned[:num_questions]
    quiz_data["total_questions"] = len(quiz_data["questions"])
    if not quiz_data.get("quiz_title"):
        quiz_data["quiz_title"] = "Generated Quiz"
    quiz_data["generated_at"] = datetime.now(timezone.utc).isoformat()
    quiz_data["source_notes_length"] = len(notes_text)

    return quiz_data


def grade_quiz_submission(quiz_data, user_answers):
    """
    Grade a user's quiz submission against the correct answers.

    Args:
        quiz_data (dict): Original quiz with correct answers
        user_answers (dict): Mapping of question_id -> selected option

    Returns:
        dict: Score breakdown and per-question feedback
    """
    if not quiz_data or "questions" not in quiz_data:
        return {"error": "Invalid quiz data provided for grading."}

    if not isinstance(user_answers, dict):
        user_answers = {}

    results = {
        "total_questions": len(quiz_data["questions"]),
        "correct_count": 0,
        "incorrect_count": 0,
        "unanswered_count": 0,
        "score_percentage": 0.0,
        "question_results": [],
        "graded_at": datetime.now(timezone.utc).isoformat(),
    }

    for question in quiz_data["questions"]:
        q_id = str(question["question_id"])
        correct_answer = str(question.get("correct_answer", "")).strip().upper()
        user_answer = str(user_answers.get(q_id, "")).strip()

        if not user_answer:
            is_correct = False
            results["unanswered_count"] += 1
        elif user_answer.upper() == correct_answer:
            is_correct = True
            results["correct_count"] += 1
        else:
            is_correct = False
            results["incorrect_count"] += 1

        results["question_results"].append(
            {
                "question_id": question["question_id"],
                "question_text": question.get("question_text", ""),
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": question.get("explanation", ""),
            }
        )

    total = results["total_questions"]
    if total > 0:
        results["score_percentage"] = round(
            (results["correct_count"] / total) * 100, 1
        )

    return results


def quiz_for_client(quiz_data):
    """Return quiz JSON safe for the frontend (no correct answers)."""
    return {
        "quiz_title": quiz_data.get("quiz_title", "Generated Quiz"),
        "total_questions": quiz_data.get("total_questions", 0),
        "questions": [
            {
                "question_id": q["question_id"],
                "question_text": q["question_text"],
                "options": q["options"],
            }
            for q in quiz_data.get("questions", [])
        ],
        "generated_at": quiz_data.get("generated_at"),
    }
